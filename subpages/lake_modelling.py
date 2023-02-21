import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
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


def app():
    """Main function for the 'lake_modelling' page."""
    st.markdown("## Lake modelling")

    init_cond = get_initial_cond()

    lake = get_lake_params()

    n_months = get_duration()

    lim_param = get_lim_param(n_months)

    ca_sim = run_ca_model(
        init_cond,
        lake,
        lim_param,
    )

    plot_result(ca_sim.reset_index(), "index", "Ca (mg/l)")

    return None


def get_initial_cond():
    st.markdown("### Initial Conditions")
    col1, col2 = st.columns(2)
    C_lake0 = col1.number_input(
        "Initial lake Ca concentration (mg-Ca/l)", min_value=0, value=1
    )
    C_in0 = col1.number_input(
        "Lake inflow Ca concentration (mg-Ca/l)", min_value=0, value=1
    )
    C_bott0 = col2.number_input(
        "Lake bottom concentration (mg-Ca/l)", min_value=0, value=0
    )
    pH_lake0 = col2.number_input("Lake pH", min_value=1.0, max_value=7.0, value=4.5)

    init_cond = C_lake0, C_in0, C_bott0, pH_lake0

    return init_cond


def get_lake_params():
    st.markdown("### Lake characteristics")
    col1, col2 = st.columns(2)

    area = col1.number_input("Lake area (km2)", min_value=0.0, value=1.14)
    mean_depth = col1.number_input("Mean lake depth (m)", min_value=0.0, value=5.6)
    res_time = col2.number_input("Volume / mean_annual_q", min_value=0, value=10)
    flow_profile = col2.selectbox("Choose profile", ("none", "fjell", "kyst"))

    lake_params = (area, mean_depth, res_time, flow_profile)

    return lake_params


def get_duration():
    st.markdown("### Model setup")
    n_months = st.number_input("Number of months to simulate", min_value=0, value=12)
    return n_months


def get_lim_param(n_months):
    st.markdown("### Liming product")
    col1, col2 = st.columns(2)

    lime_prod = col1.selectbox(
        "Choose liming product", ("Miljøkalk EY3", "Miljøkalk VK3", "SK2")
    )
    lime_dose = col1.number_input('Liming "dose" (mg-lime/l)', min_value=0, value=10)
    lime_month = col1.number_input(
        "Month in which lime is added, must be less than lenght of simulation",
        max_value=n_months - 1,
        value=2,
    )
    spr_meth = col2.selectbox("Choose distribution", ("Wet", "Dry"))
    K_L = col2.number_input(
        "Lime dissoltuion rate on the bottom of the lake (month^-1)",
        min_value=0,
        value=1,
    )
    F_active = col2.number_input(
        'Proportion of lake-bottom lime that remains "active" (i.e. available for dissolution)',
        min_value=0.0,
        max_value=1.0,
        value=0.4,
    )

    lim_param = (lime_prod, lime_dose, lime_month, spr_meth, K_L, F_active, n_months)

    return lim_param


def plot_result(result, x_title, y_title):
    st.markdown("## Result")
    chart = alt.Chart(result).mark_line().encode(x=x_title, y=y_title)
    st.altair_chart(chart, use_container_width=True)

    return None


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
    dt=0.01,
):
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
    # Unpack parameters
    C_lake0, C_in0, C_bott0, pH_lake0 = init_cond
    area, mean_depth, res_time, flow_profile = lake
    lime_prod, lime_dose, lime_month, spr_meth, K_L, F_active, n_months = lim_param
    par_dict = {
        "C_lake0": C_lake0,
        "pH_lake0": pH_lake0,
        "lime_prod": lime_prod,
        "lime_dose": lime_dose,
        "spr_meth": spr_meth,
        "K_L": K_L,
        "F_active": F_active,
        "res_time": res_time,
        "flow_profile": flow_profile,
    }

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
    q_df = pd.read_excel("notebooks/relative_discharge_by_month.xlsx", index_col=0)

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
