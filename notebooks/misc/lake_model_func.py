import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import odeint


# "Database" of lime product data
LIME_DATA = {
    "Miljøkalk EY3": {
        "IDph40": 70.4,
        "IDph45": 51.2,
        "IDph50": 44.0,
        "IDph55": 42.3,
        "IDph60": 37.8,
        "OD10": 1.0,
        "OD20": 1.2,
        "OD35": 1.5,
        "OD50": 2.2,
        "OD85": 3.4,
        "CaPct": 38.5,
        "MgPct": 0,
        "DryFac": 0.7,
        "ColDepth": 2.0,
    },
    "Miljøkalk VK3": {
        "IDph40": 81.9,
        "IDph45": 63.4,
        "IDph50": 58.4,
        "IDph55": 51.6,
        "IDph60": 52.1,
        "OD10": 1.0,
        "OD20": 1.3,
        "OD35": 2.0,
        "OD50": 2.3,
        "OD85": 3.6,
        "CaPct": 39,
        "MgPct": 0,
        "DryFac": 0.7,
        "ColDepth": 2.0,
    },
    "SK2": {
        "IDph40": 66,
        "IDph45": 63,
        "IDph50": 60,
        "IDph55": 58,
        "IDph60": 56,
        "OD10": 1.0,
        "OD20": 1.0,
        "OD35": 1.1,
        "OD50": 1.4,
        "OD85": 2.3,
        "CaPct": 33.2,
        "MgPct": 1.4,
        "DryFac": 0.6,
        "ColDepth": 5.0,
    },
}


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


def validate_user_input(par_dict):
    """Check user supplied parameters.

    Args
        par_dict: Dict of form
                  par_dict = {
                        "C_lake0": C_lake0,
                        "C_in0": C_in0,
                        "C_bott0": C_bott0,
                        "pH_lake0": pH_lake0,
                        "lime_prod": lime_prod,
                        "lime_dose": lime_dose,
                        "lime_month": lime_month,
                        "spr_meth": spr_meth,
                        "K_L": K_L,
                        "F_active": F_active,
                        "area": area,
                        "mean_depth": mean_depth,
                        "res_time": res_time,
                        "flow_profile": flow_profile,
                        "n_months": n_months,
                    }
    Returns
        None.
    """
    assert (
        par_dict["lime_prod"] in LIME_DATA.keys()
    ), f"Lime product '{par_dict['lime_prod']}' not found in database."

    assert par_dict["spr_meth"] in (
        "wet",
        "dry",
    ), "'spr_meth' must be either 'wet' or 'dry'."

    assert par_dict["flow_profile"] in (
        "none",
        "fjell",
        "kyst",
    ), "'flow_profile' must be one of ('none', 'fjell', 'kyst')."

    assert 1 < par_dict["pH_lake0"] < 7, "'pH_lake0' must be between 1 and 7."

    assert 0 <= par_dict["F_active"] <= 1, "'F_active' must be between 0 and 1."

    gt_or_eq_0 = [
        "C_lake0",
        "C_in0",
        "C_bott0",
        "lime_dose",
        "K_L",
        "area",
        "mean_depth",
        "res_time",
        "n_months",
    ]
    for par in gt_or_eq_0:
        assert par_dict[par] >= 0, f"'{par}' must be greater than or equal to zero."

    assert (
        0 <= par_dict["lime_month"] <= par_dict["n_months"]
    ), "'lime_month' must be less than 'n_months'."

    return None


def run_ca_model(par_dict, dt=0.01):
    """Run the model for Ca concentration using parameters from 'par_dict'.

    Args
        par_dict: Dict of model parameters:
                      par_dict = {
                            "C_lake0": C_lake0,
                            "C_in0": C_in0,
                            "C_bott0": C_bott0,
                            "pH_lake0": pH_lake0,
                            "lime_prod": lime_prod,
                            "lime_dose": lime_dose,
                            "lime_month": lime_month,
                            "spr_meth": spr_meth,
                            "K_L": K_L,
                            "F_active": F_active,
                            "area": area,
                            "mean_depth": mean_depth,
                            "res_time": res_time,
                            "flow_profile": flow_profile,
                            "n_months": n_months,
                        }
        dt:         Float between 0 and 1 (months). Time resolution in decimal
                    months for evaluating the model within each monthly time step.
                    NOTE: This parameter does not affect how the ODEs are solved
                    (that is handled automatically). It simply sets the level of
                    temporal detail in the output. Larger values run faster, but
                    give coarser output. Default 0.01.

    Returns
        Dataframe with time index (in decimal months) and Ca concentration.
    """
    assert 0 < dt < 1, "'dt' must be between zero and one."
    validate_user_input(par_dict)

    # Unpack parameters
    C_lake0 = par_dict["C_lake0"]
    C_in0 = par_dict["C_in0"]
    C_bott0 = par_dict["C_bott0"]
    pH_lake0 = par_dict["pH_lake0"]
    lime_prod = par_dict["lime_prod"]
    lime_dose = par_dict["lime_dose"]
    lime_month = par_dict["lime_month"]
    spr_meth = par_dict["spr_meth"]
    K_L = par_dict["K_L"]
    F_active = par_dict["F_active"]
    area = par_dict["area"]
    mean_depth = par_dict["mean_depth"]
    res_time = par_dict["res_time"]
    flow_profile = par_dict["flow_profile"]
    n_months = par_dict["n_months"]

    if spr_meth == "dry":
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
    q_df = pd.read_excel("../data/flow_typologies.xlsx", index_col=0)

    # Time domain
    months = range(1, n_months + 1)
    month_ids = (list(range(1, 13)) * n_months)[:n_months]

    # Loop  over months
    C_bott = C_bott0
    C_lake = C_lake0
    ys = []
    tis = []
    for month in months:
        if month == lime_month:
            # Lake concentration immediately increases by C_inst, and some lime
            # is added to the bottom to contribute to 'slow' dissolution
            C_bott = C_bott + F_active * (ca_dose - C_inst)
            C_lake = C_lake + C_inst

        # Estimate flow this month
        q = q_mean * q_df.loc[month_ids[month - 1], flow_profile]

        # Solve ODEs. NOTE: 'ti' should be a one-month period with the desired time
        # step, 'dt'. For the basic balance of inflow and outflow, ANY one-month
        # period is OK. However, for the evaluation dC_slow_dt, 'ti' MUST be the
        # number of months since liming (so the exponential is evaluated in the right
        # place).
        y0 = [C_lake]
        params = [q, V, C_in0, C_bott, K_L]
        if month >= lime_month:
            ti = np.linspace(
                month - lime_month, month - lime_month + 1, num=int(1 + 1 / dt)
            )
        else:
            ti = np.linspace(month - 1, month, num=int(1 + 1 / dt))
        y = odeint(dCdt, y0, ti, args=(params,))
        y = y[:, 0]
        if month >= lime_month:
            ti = ti + lime_month - 1
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
        "F_active",
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
    df = df[~df.index.duplicated(keep="last")]
    df.index = df.index + 1

    return df


def est_res_time_from_lake_props(area_km2, mean_depth_m, q_m3ps):
    """Calculates lake residence time based on surface area, mean depth
    and mean flow. Useful for setting up model.

    Args
        area_km2:    Float. Surface area in km2
        avg_depth_m: Float. Mean deoth in metres
        q_m3ps:      Float. Mean annual discharge in m3/s

    Returns
        Float. Residence time in years.
    """
    V = area_km2 * 1e6 * mean_depth_m  # Lake volume in m3
    res_time = V / (q_m3ps * 60 * 60 * 24 * 365)

    return res_time
