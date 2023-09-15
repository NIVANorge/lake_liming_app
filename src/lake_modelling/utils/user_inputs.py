import streamlit as st


def get_lake_params():
    st.markdown("### Lake characteristics")
    col1, col2 = st.columns(2)

    area = col1.number_input("Surface area (km²)", min_value=0.01, value=0.2)
    depth = col1.number_input("Mean depth (m)", min_value=0.01, value=5.0)
    tau = col1.number_input(
        "Water residence time (years)",
        min_value=0.1,
        value=0.7,
        step=0.1,
        format="%.1f",
    )
    flow_prof = (
        col2.selectbox("Flow profile", ("None", "Fjell", "Kyst"), index=1)
    ).lower()
    pH_lake0 = col2.number_input("Initial pH", min_value=1.0, max_value=7.0, value=4.5)
    toc_lake0 = col2.number_input("TOC concentration (mg/l)", min_value=0.0, value=4.0)

    lake_params = (area, depth, tau, flow_prof, pH_lake0, toc_lake0)

    return lake_params


def get_product(products):
    # products.append("Custom Product")

    st.markdown("### Liming products")
    prod_name = st.selectbox("Choose liming product", (products))
    # if prod_name == "Custom Product":
    #     st.text("Input for custom liming product to be implemented")

    return prod_name


def get_model_params():
    st.markdown("### Model parameters")
    col1, col2 = st.columns(2)

    lime_dose = col1.number_input(
        "Lime dose (mg/l of product)", min_value=0.1, max_value=85.0, value=10.0
    )
    spr_prop = col1.number_input(
        "Proportion of lake surface area limed (-)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
    )
    spr_meth = col1.selectbox("Application method", ("Wet", "Dry"), index=0).lower()
    lime_month = col1.number_input(
        "Application month", min_value=1, max_value=12, value=1
    )
    F_sol = col2.number_input(
        "Proportion of lake-bottom lime that remains soluble (-)",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
    )
    rate_const = col2.number_input(
        "Initial dissolution rate for lake-bottom lime (per month)",
        min_value=0.0,
        value=1.0,
    )
    activity_const = col2.number_input(
        "Rate at which lake-bottom lime becomes 'inactive' (per month)",
        min_value=0.0,
        value=0.1,
    )
    ca_aq_sat = col2.number_input(
        "'ca_aq_sat' (testing only)", min_value=0.1, value=8.5
    )
    n_months = col2.number_input("Number of months to simulate", min_value=1, value=24)

    model_params = (
        lime_dose,
        lime_month,
        spr_meth,
        spr_prop,
        F_sol,
        rate_const,
        activity_const,
        ca_aq_sat,
        n_months + 1,
    )

    return model_params
