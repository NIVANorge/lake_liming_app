import streamlit as st


def get_lake_params():
    st.markdown("### Lake characteristics")
    with st.expander("Help"):
        st.markdown(
            """Enter the characteristics for your lake of interest using the input boxes below.
            Estimates for mean monthly and annual discharge will be shown in the plot."""
        )
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
        col1.selectbox("Flow profile", ("None", "Fjell", "Kyst"), index=1)
    ).lower()
    pH_lake0 = col2.number_input("Initial pH", min_value=4.5, max_value=6.5, value=4.5)
    pH_inflow = col2.number_input("Inflow pH", min_value=4.5, max_value=6.5, value=4.5)
    toc_lake0 = col2.number_input("TOC concentration (mg/l)", min_value=0.0, value=4.0)
    lake_params = (area, depth, tau, flow_prof, pH_lake0, pH_inflow, toc_lake0)

    return lake_params


def get_product(products):
    st.markdown("## Liming products")
    with st.expander("Help"):
        st.markdown(
            """Choose a liming product from the list below to view column test results (instantaneous 
            dissolution and overdosing factors) from the database."""
        )
    prod_name = st.selectbox("Choose liming product", (products))

    return prod_name


def get_model_params():
    st.markdown("### Liming parameters")
    with st.expander("Help"):
        st.markdown(
            """
        Use the input boxes below to define the **liming procedure**.
            
        For each product in the database, the model will simulate changes in Ca
        (equivalent) concentration and pH for the specified lake using this procedure.
        """
        )
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
    lime_month = col2.number_input(
        "Application month", min_value=1, max_value=12, value=7
    )
    n_months = col2.number_input("Number of months to simulate", min_value=1, value=24)
    # F_sol = col1.number_input(
    #     "Proportion of lake-bottom lime that remains soluble (-)",
    #     min_value=0.0,
    #     max_value=1.0,
    #     value=1.0,
    # )
    # ca_aq_sat = col1.number_input(
    #     "'ca_aq_sat' (testing only)", min_value=0.1, value=8.5
    # )
    # rate_const = col2.number_input(
    #     "Initial dissolution rate for lake-bottom lime (per month)",
    #     min_value=0.0,
    #     value=0.1,
    # )
    # activity_const = col2.number_input(
    #     "Rate at which lake-bottom lime becomes 'inactive' (per month)",
    #     min_value=0.0,
    #     value=0.1,
    # )
    F_sol = 1
    ca_aq_sat = 8.5
    rate_const = 0.1
    activity_const = 0.1

    model_params = (
        lime_dose,
        lime_month,
        spr_meth,
        spr_prop,
        F_sol,
        rate_const,
        activity_const,
        ca_aq_sat,
        n_months,
    )

    return model_params