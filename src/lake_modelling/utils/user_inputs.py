import streamlit as st


def get_lake_params():
    st.markdown("### Lake characteristics")
    col1, col2 = st.columns(2)

    area = col1.number_input("Lake area (km2)", min_value=0.01, value=0.2)
    depth = col1.number_input("Mean lake depth (m)", min_value=0.01, value=5.0)
    tau = col1.number_input(
        "Water residence time (years)",
        min_value=0.1,
        value=0.7,
        step=0.1,
        format="%.1f",
    )
    flow_prof = (
        col2.selectbox("Choose profile", ("None", "Fjell", "Kyst"), index=1)
    ).lower()
    pH_lake0 = col2.number_input("Lake pH", min_value=1.0, max_value=7.0, value=4.5)
    colour_lake0 = col2.number_input("Lake colour (mgPt/l)", value=10.0)

    lake_params = (area, depth, tau, flow_prof, pH_lake0, colour_lake0)

    return lake_params


def get_prod_and_duration(products):
    col1, col2 = st.columns(2)

    col1.markdown("### Liming products")
    prod_name = col1.selectbox("Choose liming product", (products))

    col2.markdown("### Simulation length")
    n_months = col2.number_input("Number of months to simulate", min_value=1, value=24)

    return (prod_name, n_months + 1)


def get_lim_param(n_months, products):
    st.markdown("### Liming product")
    col1, col2 = st.columns(2)

    lime_prod = col1.selectbox("Choose liming product", (products))
    lime_dose = col1.number_input(
        'Liming "dose" (mg-lime/l)', min_value=0.0, value=10.0
    )
    lime_month = col1.number_input(
        "Month in which lime is added, must be less than length of simulation",
        max_value=n_months - 1,
        value=1,
        min_value=1,
    )
    spr_meth = col2.selectbox("Choose distribution method", ("Wet", "Dry"))
    K_L = col2.number_input(
        "Lime dissoltuion rate on the bottom of the lake (month^-1)",
        min_value=0.0,
        value=1.0,
    )
    F_sol = col2.number_input(
        'Proportion of lake-bottom lime that remains "soluble" (i.e. available for dissolution)',
        min_value=0.0,
        max_value=1.0,
        value=0.4,
    )

    lim_param = (lime_prod, lime_dose, lime_month, spr_meth, K_L, F_sol, n_months)

    return lim_param
