import streamlit as st
from src.lake_modelling.utils.lake_model import LIME_PRODUCTS_DATA, Lake, LimeProduct
from src.lake_modelling.utils.read_products import lime_product_names, lime_products
from src.lake_modelling.utils.run_products import (
    plot_multiple_products,
    run_multiple_products,
)
from src.lake_modelling.utils.user_inputs import get_lake_params, get_product


def app():
    """Main function for the 'lake_modelling' page."""
    # plot_lib = st.selectbox(
    #     "Choose a plotting library:", options=["Altair", "Matplotlib"]
    # )
    plot_lib = "Altair"

    products = lime_product_names(lime_products(LIME_PRODUCTS_DATA))
    name = get_product(products)
    prod = LimeProduct(name)
    prod.plot_column_data(plot_lib)

    st.markdown("## Lake modelling")
    area, depth, tau, flow_prof, pH_lake0, pH_inflow, toc_lake0 = get_lake_params()
    lake = Lake(area, depth, tau, flow_prof, pH_lake0, pH_inflow, toc_lake0)
    lake.plot_flow_profile(plot_lib)

    res_df = run_multiple_products(lake, products)
    st.markdown("### Model results")
    with st.expander("Help"):
        st.markdown(
            """
        The plots are interactive:
         * Click on the series names in the legend to turn curves on/off.
         * Use `SHIFT + Click` to select multiple curves.
         * Use your mouse wheel to zoom in/out.
         * Double-click to return to the full extent.
         * Hover on any line to see details as "tooltips".

        Dashed horizontal lines on the pH plot mark the lake's initial and inflow pH.
        """
        )
    plot_multiple_products(res_df, pH_lake0, pH_inflow, plot_lib)

    return None