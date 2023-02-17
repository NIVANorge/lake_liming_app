import streamlit as st
from src.utils.func_utils import *
from src.utils.input_data_utils import *


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
            lime_conc_all_dis = (
                1000 * par_val_dict["mass_lime_g"] / par_val_dict["water_vol_l"]
            )
            ca_conc_all_dis = lime_conc_all_dis * par_val_dict["lime_prod_ca_pct"] / 100
            st.markdown(
                f"""
                ### Processing data for product: `{par_val_dict['lime_product_name']}`
                **Total Ca content by mass:** {par_val_dict['lime_prod_ca_pct']} %

                **Total Mg content by mass:** {par_val_dict['lime_prod_mg_pct']} %
            """
            )

            # left_col, pad, right_col = st.columns([10, 1, 10])
            left_col, right_col = st.columns(2)

            # Instantaneous test
            with left_col:
                # Table
                inst_res_df = instantaneous_test(
                    inst_df, lime_conc_all_dis, ca_conc_all_dis, method="trapezoidal"
                )
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
                # Table
                od_res_df = overdosing_test(
                    od_df, par_val_dict["lime_prod_ca_pct"], method="trapezoidal"
                )
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
