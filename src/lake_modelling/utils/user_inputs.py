import streamlit as st


def get_lake_params():
    st.markdown("### Innsjøegenskaper")
    # with st.expander("Help"):
    #     st.markdown(
    #         """Enter the characteristics for your lake of interest using the input boxes below.
    #         Estimates for mean monthly and annual discharge will be shown in the plot."""
    #     )
    with st.expander("Hjelp"):
        st.markdown(
            """Skriv inn egenskapene for din interessante innsjø ved å bruke inntastingsboksene 
            nedenfor. Estimert gjennomsnittlig månedlig og årlig utslipp vil bli vist i plottet."""
        )
    col1, col2 = st.columns(2)
    area = col1.number_input("Overflateareal (km²)", min_value=0.01, value=0.2)
    depth = col1.number_input("Middeldybde (m)", min_value=0.01, value=5.0)
    tau = col1.number_input(
        "Vannoppholdstid (years)",
        min_value=0.1,
        value=0.7,
        step=0.1,
        format="%.1f",
    )
    flow_prof = (
        col1.selectbox("Vannføringsprofil", ("Ingen", "Fjell", "Kyst"), index=1)
    ).lower()
    if flow_prof == "ingen":
        flow_prof = "none"
    pH_lake0 = col2.number_input("Start pH", min_value=4.5, max_value=6.5, value=5.0)
    pH_inflow = col2.number_input("Innløps pH", min_value=4.5, max_value=6.5, value=5.0)
    toc_lake0 = col2.number_input("TOC konsentrasjon (mg/l)", min_value=0.0, value=4.0)
    lake_params = (area, depth, tau, flow_prof, pH_lake0, pH_inflow, toc_lake0)

    return lake_params


def get_product(products):
    st.markdown("## Kalkprodukter")
    # with st.expander("Help"):
    #     st.markdown(
    #         """Choose a liming product from the list below to view column test results (instantaneous 
    #         dissolution and overdosing factors) from the database."""
    #     )
    with st.expander("Hjelp"):
        st.markdown(
            """Velg et kalkprodukt fra listen nedenfor for å se kolonnetestresultater 
            (momentanoppløsning og overdoseringsfaktorer) fra databasen."""
        )
    prod_name = st.selectbox("Velg kalkprodukt", (products))

    return prod_name


def get_model_params():
    st.markdown("### Kalkingsparametere")
    # with st.expander("Help"):
    #     st.markdown(
    #         """
    #     Use the input boxes below to define the **liming procedure**.
            
    #     For each product in the database, the model will simulate changes in Ca
    #     (equivalent) concentration and pH for the specified lake using this procedure.
    #     """
    #     )
    with st.expander("Hjelp"):
        st.markdown(
            """
        Bruk inndataboksene nedenfor for å definere **kalkingsprosedyren**.
        
        For hvert produkt i databasen vil modellen simulere endringer i Ca (ekvivalent) 
        konsentrasjon og pH for den angitte innsjøen ved hjelp av denne prosedyren.
        """
        )
    col1, col2 = st.columns(2)

    lime_dose = col1.number_input(
        "Kalkdose (mg/l produkt)", min_value=0.1, max_value=85.0, value=10.0
    )
    spr_prop = col1.number_input(
        "Andel av innsjøoverflate kalket (-)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
    )
    spr_meth = col1.selectbox("Kalkingsmetode", ("Våt", "Tørr"), index=0).lower()
    if spr_meth == "våt":
        spr_meth = "wet"
    else:
        spr_meth = "dry"
    lime_month = col2.number_input(
        "Kalkingsmåned", min_value=1, max_value=12, value=7
    )
    n_months = col2.number_input("Antall måneder å simulere", min_value=1, value=12)
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