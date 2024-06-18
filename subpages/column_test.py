import streamlit as st
from src.col_tests.utils.display_results import display_results
from src.col_tests.utils.read_input import read_template


def app():
    """Main function for the 'column_test' page."""

    # st.markdown("## Column tests")
    # st.info(
    #     """You can explore column test results for lime products that are **already
    #     in the database** from the `Innsjømodellering` tab.""",
    #     icon="ℹ️",
    # )
    # with st.expander("Help"):
    #     st.markdown(
    #         """Use this page to upload **new** column test data from an Excel template.
    #     First download a blank copy of the template
    #     [here](https://github.com/NIVANorge/lake_liming_app/raw/main/data/liming_app_data_template_v1-1.xlsx).
    #     Then fill-in your column test results and upload the completed template
    #     using the button in the left sidebar."""
    #     )
    st.markdown("## Kolonnetester")
    st.info(
        """Du kan utforske kolonnetestresultater for kalkprodukter som er **allerede i 
        databasen** fra fanen `Innsjømodellering`.""",
        icon="ℹ️",
    )
    with st.expander("Hjelp"):
        st.markdown(
            """Bruk denne siden til å laste opp **nye** kolonnetestdata fra en Excel-mal. 
            Last først ned en tom kopi av malen 
            [her](https://github.com/NIVANorge/lake_liming_app/raw/main/data/liming_app_data_template_v1-1.xlsx). 
            Fyll deretter ut kolonnetestresultatene og last opp den ferdige malen ved å 
            bruke knappen i venstre sidefelt."""
        )
    data_file = st.sidebar.file_uploader("Last opp mal")
    if data_file:
        st.session_state["data_file"] = data_file

    if "data_file" in st.session_state:
        data_file = st.session_state["data_file"]
        with st.spinner("Leser data..."):
            st.markdown(f"**Filnavn:** `{data_file.name}`")
            read_template(data_file)

            par_df = st.session_state["par_df"]
            inst_df = st.session_state["inst_df"]
            od_df = st.session_state["od_df"]

            # Print basic info for test as a whole
            par_val_dict = par_df.to_dict()["Value"]
            st.markdown(
                f"""
                ### Behandler data for produkt: `{par_val_dict['lime_product_name']}`
                **Totalt Ca-innhold etter masse:** {par_val_dict['lime_prod_ca_pct']} %

                **Totalt Mg-innhold etter masse:** {par_val_dict['lime_prod_mg_pct']} %
            """
            )

            def subheader(str):
                st.markdown(
                    f'<p style="color:#0047AB;font-size:28px;padding-top:10px"><b>{str}</b></p>',
                    unsafe_allow_html=True,
                )

            subheader("Kalsium resultater")
            left_col, right_col = st.columns(2)
            # Instantaneous test
            with left_col:
                display_results(
                    par_val_dict,
                    inst_df,
                    element="Ca",
                    test_type="instantaneous",
                    method="trapezoidal",
                )
            # Overdosing test
            with right_col:
                display_results(
                    par_val_dict,
                    od_df,
                    element="Ca",
                    test_type="overdosing",
                    method="trapezoidal",
                )

            # Display Mg results if data present
            if inst_df["Mg_mg/l"].sum() != 0:
                subheader("Magnesium resultater")
                left_col, right_col = st.columns(2)
                with left_col:
                    # Instantaneous test
                    display_results(
                        par_val_dict,
                        inst_df,
                        element="Mg",
                        test_type="instantaneous",
                        method="trapezoidal",
                    )
                with right_col:
                    # Overdosing test
                    display_results(
                        par_val_dict,
                        od_df,
                        element="Mg",
                        test_type="overdosing",
                        method="trapezoidal",
                    )

    return None