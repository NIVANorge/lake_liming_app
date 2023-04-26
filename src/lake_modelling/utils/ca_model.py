import numpy as np
import pandas as pd

from math import floor

from scipy.integrate import odeint


def find_nearest(par, val):
    """Returns the most relevant dict key to use for querying
    instantaneous dissolution (ID) and overdosing (OD) data from
    the database. Used for e.g. depth corrections.
    Args
        par: Str. Either 'ID' or 'OD'
        val: Numeric. pH or does value to compare
    Returns
        Str. Dict key.
    """

    assert par in ("ID", "OD")
    if par == "ID":
        val_list = [4.0, 4.5, 5.0, 5.5, 6.0]
    else:
        val_list = [10, 20, 35, 50, 85]

    closest = min(val_list, key=lambda x: abs(x - val))

    if par == "ID":
        return f"IDph{int(closest*10)}"
    else:
        return f"OD{int(closest)}"


def dCdt(y, t, params):
    """Define the ODE system for the TPKALK box model.
    Args
        y:      List. [C_lake]. Current lake concentration of Ca in mg/l
        t:      Array. Time points at which to evaluate C_lake (in months)
        params: Tuple. (Q, V, C_in, C_bott, K_L).
                    Q is mean flow in litres/month
                    V is lake volume in litres
                    C_in in lake inflow concentration of Ca in mg/l
                    C_bott is the 'dose' of lime on the lake bottom in mg-Ca/l
                    K_L determines the rate of dissoltuion of lime on the bottom
                    of the lake (months^-1)
    Returns
        Array.
    """
    # Unpack incremental value for C_lake
    C_lake = y[0]

    # Unpack fixed params
    Q, V, C_in, C_bott, K_L = params

    # Model equations
    dCslow_dt = C_bott * K_L * np.exp(-K_L * t)
    dClake_dt = (Q * C_in - Q * C_lake) / V + dCslow_dt

    # Add results of equations to an array
    res = np.array([dClake_dt])

    return res


def run_ca_model(
    init_cond,
    lake,
    lim_param,
    LIME_DATA,
    dt=0.1,
):
    """Run the model for Ca concentration.
    Args
        init_cond:  Tuple of initial condition parameters:
                        C_lake0:        Lake Ca concentration (mg/l)
                        pH_lake0:       Lake pH
                        C_in0:      Lake inflow concentration (mg/l)
                        C_bott0:    "Active" lime on the lake bottom at t=0 (mg/l)
        lake:       Tuple of lake characteriscs:
                        area:           Lake area (km2)
                        mean_depth:     Lake's mean depth (m)
                        res_time:       Residency time (Volume / mean_annual_q)
                        flow_profile:   'none', 'fjell' or 'kyst'
        lim_param:  Tuple of liming paramethers:
                        lime_prod:      Name of product. Must be in the "database"
                        lime_dose:      Dose as lime (not Ca) in mg/l
                        lime_month:     Month in which lime is added. Must be < 'n_months'
                        spr_meth:       Distribution method 'wet' or 'dry'
                        K_L:            Rate of dissolution of "active" bottom lime (month^-1)
                        F_sol:          Proportion of lake-bottom lime that remains "active" (i.e. available for dissolution)
                        n_months:       Number of months to simulate
        LIME_DATA:  "Database" of liming products
        dt:         Float between 0 and 1 (months). Time resolution in decimal
                    months for evaluating the model within each monthly time step.
                    NOTE: This parameter does not affect how the ODEs are solved
                    (that is handled automatically). It simply sets the level of
                    temporal detail in the output. Larger values run faster, but
                    give coarser output. Default 0.1.
    Returns
        Dataframe with time index (in decimal months) and Ca concentration.
    """
    # Unpack parameters
    C_lake0, C_in0, C_bott0, pH_lake0 = init_cond
    area, mean_depth, res_time, flow_profile = lake
    lime_prod, lime_dose, lime_month, spr_meth, K_L, F_sol, n_months = lim_param
    par_dict = {
        "C_lake0": C_lake0,
        "pH_lake0": pH_lake0,
        "lime_prod": lime_prod,
        "lime_dose": lime_dose,
        "spr_meth": spr_meth,
        "K_L": K_L,
        "F_sol": F_sol,
        "res_time": res_time,
        "flow_profile": flow_profile,
    }

    if spr_meth == "Dry":
        spr_fac = LIME_DATA[lime_prod]["DryFac"]
    else:
        spr_fac = 1

    # Estimate instantaneous dissolution
    col_depth = LIME_DATA[lime_prod]["ColDepth"]
    depth_corr = np.log10(mean_depth / col_depth)
    ph_col_ca = pH_lake0 - depth_corr
    od_fac = LIME_DATA[lime_prod][find_nearest("OD", lime_dose)]
    inst_diss_pct = (
        spr_fac * LIME_DATA[lime_prod][find_nearest("ID", ph_col_ca)] / od_fac
    )
    ca_dose = lime_dose * LIME_DATA[lime_prod]["CaPct"] / 100
    C_inst = ca_dose * inst_diss_pct / 100

    # Hydrology
    V = 1000 * area * 1e6 * mean_depth  # Lake volume in litres
    q_mean = V / (12 * res_time)  # Annual mean flow in litres/month to give res_time
    q_df = pd.read_excel("data/flow_typologies.xlsx", index_col=0)

    # Time domain
    months = list(round(x / 10, 1) for x in range(1, n_months * 10 + 1))
    month_ids = (list(range(1, 13)) * n_months)[:n_months]
    lime_month_round = round(
        lime_month, 1
    )  # rounding up to avoid inconsistencies due to float input

    # Loop  over months
    C_bott = C_bott0
    C_lake = C_lake0
    ys = []
    tis = []
    for month in months:
        if month == lime_month_round:
            # Lake concentration immediately increases by C_inst, and some lime
            # is added to the bottom to contribute to 'slow' dissolution
            C_bott = C_bott + F_sol * (ca_dose - C_inst)
            C_lake = C_lake + C_inst

        # Estimate flow this month
        q = q_mean * q_df.loc[month_ids[floor(month) - 1], flow_profile]

        # Solve ODEs. NOTE: 'ti' should be a one-month period with the desired time
        # step, 'dt'. For the basic balance of inflow and outflow, ANY one-month
        # period is OK. However, for the evaluation dC_slow_dt, 'ti' MUST be the
        # number of months since liming (so the exponential is evaluated in the right
        # place).
        y0 = [C_lake]
        params = [q, V, C_in0, C_bott, K_L]
        if month >= lime_month_round:
            ti = np.linspace(
                month - lime_month_round,
                month - lime_month_round + 0.1,
                num=int(1 + 1 / dt),
            )
        else:
            ti = np.linspace(month - 0.1, month, num=int(1 + 1 / dt))
        y = odeint(dCdt, y0, ti, args=(params,))
        y = y[:, 0]
        if month >= lime_month_round:
            ti = ti + lime_month_round - 1
        ys.append(y)
        tis.append(ti)

        # Update initial conditions for next step
        C_lake = y[-1]

    # Build df from output
    df = pd.DataFrame(
        data=np.concatenate(ys),
        columns=["Ca (mg/l)"],
        index=np.concatenate(tis),
    )

    # Add metadata
    meta_cols = [
        "C_lake0",
        "pH_lake0",
        "K_L",
        "F_sol",
        "flow_profile",
        "lime_prod",
        "lime_dose",
        "spr_meth",
        "res_time",
    ]
    for meta_col in meta_cols:
        df[meta_col] = par_dict[meta_col]
    df = df[meta_cols + ["Ca (mg/l)"]]

    # At each time step, the solver run from (month - 1) to month inclusive.
    # The first and last time points in successive segments are therefore
    # duplicated. Remove these. Also shoft month index by +1 so that e.g.
    # January is between time points 1 and 2 (instead of 0 and 1) etc.
    df.index = np.round(df.index, 2)
    df = df[~df.index.duplicated(keep="last")]
    df.index = df.index + 1

    return df
