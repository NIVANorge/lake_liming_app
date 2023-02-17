import streamlit as st
from src.col_tests.utils.column_tests import *
from src.col_tests.utils.read_input import *


def app():
    """Main function for the 'column_test' page."""
    st.markdown("## Column tests")
    data_file = st.sidebar.file_uploader("Upload template")
    if data_file:
        st.session_state["data_file"] = data_file

    if "data_file" in st.session_state:
        data_file = st.session_state["data_file"]
        with st.spinner("Reading data..."):
            st.markdown(f"**File name:** `{data_file.name}`")
            read_template(data_file)
            par_df = st.session_state["par_df"]
            inst_df = st.session_state["inst_df"]
            od_df = st.session_state["od_df"]

            # Print basic info for test as a whole
            par_val_dict = par_df.to_dict()["Value"]
            st.markdown(
                f"""
                ### Processing data for product: `{par_val_dict['lime_product_name']}`
                **Total Ca content by mass:** {par_val_dict['lime_prod_ca_pct']} %

                **Total Mg content by mass:** {par_val_dict['lime_prod_mg_pct']} %
            """
            )

            # left_col, pad, right_col = st.columns([10, 1, 10])
            left_col, right_col = st.columns(2)

            # TODO: if no data - display warning and not display table & plots!!!

            # Instantaneous test
            with left_col:
                lime_conc_all_dis = (
                    1000 * par_val_dict["mass_lime_g"] / par_val_dict["water_vol_l"]
                    )
                ca_conc_all_dis = lime_conc_all_dis * par_val_dict["lime_prod_ca_pct"] / 100

                st.markdown("### Instantaneous dissolution")
                st.markdown(
                    f"**Lime added:** {lime_conc_all_dis:.1f} mg/l ({ca_conc_all_dis:.1f} mg/l of Ca)"
                )
                inst_res_df = get_test_results(
                    inst_df, ca_conc_all_dis, test_type="instantaneous", method="trapezoidal"
                )
                # TODO: Here check if flag triggered!!!

                # Table
                st.dataframe(
                    inst_res_df.style.format("{:.1f}"), use_container_width=True
                )

                # Plot
                inst_chart = make_chart(
                    inst_res_df,
                    "pH (-)",
                    "Dissolution (%)",
                    "Instantaneous dissolution test",
                )
                st.altair_chart(inst_chart, use_container_width=True)

            # Overdosing test
            with right_col:
                st.markdown("### Overdosing factors")
                st.markdown("**Column pH:** 4.6")
                od_res_df = get_test_results(
                    od_df, par_val_dict["lime_prod_ca_pct"], test_type="overdosing", method="trapezoidal"
                )
                # Table
                st.dataframe(od_res_df.style.format("{:.1f}"), use_container_width=True)
                # Plot
                od_chart = make_chart(
                    od_res_df,
                    "Lime added (mg/l)",
                    "Overdosing factor (-)",
                    "Overdosing test",
                )
                st.altair_chart(od_chart, use_container_width=True)

    return None
