import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from scipy.integrate import odeint


def app():
    """Main function for the 'lake_modelling' page."""
    st.markdown("## Lake modelling")

    lake = getLakeParams()

    product = getLimProd()

    n_months = getDuration()

    lake_model, x_title, y_title = model(
        lake,
        product,
        n_months,
        f,
    )
    plotResult(lake_model, x_title, y_title)

    return None


def getLakeParams():
    st.markdown("### Lake characteristics")
    col1, col2 = st.columns(2)

    C_lake0 = col1.number_input(
        "Initial lake Ca concentration (mg-Ca/l)", min_value=0, value=1
    )
    C_in0 = col1.number_input(
        "Lake inflow Ca concentration (mg-Ca/l)", min_value=0, value=1
    )
    C_bott0 = col1.number_input(
        "Lake bottom concentration (mg-Ca/l)", min_value=0, value=0
    )
    area = col2.number_input("Lake area (km2)", min_value=0.0, value=1.14)
    mean_depth = col2.number_input("Mean lake depth (m)", min_value=0.0, value=5.6)
    mean_flow = col2.number_input("Mean flow rate (m3/s)", min_value=0.0, value=0.2)

    lakeParams = (C_lake0, C_in0, C_bott0, area, mean_depth, mean_flow)

    return lakeParams


def getLimProd():
    # define data for liming products (later separate database?)
    name = "Name"
    dose = "Dose"
    content = "Content"
    overdosing = "Overdosing"
    dissolution = "Dissolution"
    data = {
        name: ["Product 1", "Product 2", "Custom"],
        dose: [10, 35, 0],
        content: [38.5, 15, 0],
        overdosing: [1.5, 2, 0],
        dissolution: [1, 1, 0],
    }
    df = pd.DataFrame(data=data)

    st.markdown("### Liming product")
    limProd = st.selectbox("Choose liming product", (df))
    prod = df.loc[df[name] == limProd]

    if limProd == "Custom":
        return getCustomLimParam()
    else:
        st.write(
            "You chose ",
            limProd,
            " with lime dose = ",
            prod[dose].values[0],
            "(mg-lime/l), lime Ca content = ",
            prod[content].values[0],
            ", %, Overdosing factor = ",
            prod[overdosing].values[0],
            " and rate of dissolution of lake bottom lime = ",
            prod[dissolution].values[0],
            ".",
        )
        return (
            prod[dose].values[0],
            prod[content].values[0],
            prod[overdosing].values[0],
            prod[dissolution].values[0],
            prod[name].values[0],
        )


def getCustomLimParam():
    st.markdown("#### Custom Liming parameters")
    col1, col2 = st.columns(2)
    lime_dose = col1.number_input('Liming "dose" (mg-lime/l)', min_value=0, value=10)
    pct_ca = col1.number_input("Lime Ca content by mass (%)", min_value=0.0, value=38.5)
    od_fac = col2.number_input("Overdosing factor (-)", min_value=0.0, value=1.5)
    K_L = col2.number_input(
        "Lime dissoltuion rate on the bottom of the lake (month^-1)",
        min_value=0,
        value=1,
    )

    return (lime_dose, pct_ca, od_fac, K_L, "Custom")


def getDuration():
    st.markdown("### Model setup")
    n_months = st.number_input(
        "Number of months to simulate after liming", min_value=1, value=12
    )
    return n_months


def f(y, t, params):
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


def model(
    lake,
    product,
    n_months,
    f,
):
    C_lake0, C_in0, C_bott0, area, mean_depth, mean_flow = lake
    lime_dose, pct_ca, od_fac, K_L, name = product

    ca_dose = lime_dose * pct_ca / 100
    C_inst = ca_dose / od_fac
    C_bott = C_bott0 + ca_dose - C_inst
    C_lake = C_lake0 + C_inst
    V = 1000 * area * 1e6 * mean_depth  # Lake volume in litres
    q = mean_flow * 1000 * 60 * 60 * 24 * 30  # Flow in litres/month
    # Vector of initial conditions
    y0 = [C_lake]

    # Model parameters
    params = [q, V, C_in0, C_bott, K_L]

    # Solve
    ti = np.arange(0, n_months, 0.01)
    y = odeint(f, y0, ti, args=(params,))

    y_title = "Ca concentration"
    x_title = "Time (months)"

    # Build df from output
    df = pd.DataFrame(data=y, columns=[y_title], index=ti)
    df[x_title] = ti + 0.01

    # Add C_lake0 (before any lime added) to the very start of the series
    df.loc[-0.01] = {y_title: C_lake0, x_title: 0}
    df.index = df.index + 0.01
    df.sort_index(inplace=True)

    return df, x_title, y_title


def plotResult(result, x_title, y_title):
    st.markdown("## Result")
    chart = alt.Chart(result).mark_line().encode(x=x_title, y=y_title)
    st.altair_chart(chart, use_container_width=True)

    return None
