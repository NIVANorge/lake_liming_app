import streamlit as st
from src.lake_modelling.utils.lake_model import (
    LIME_PRODUCTS_DATA,
    Lake,
    LimeProduct,
)
from src.lake_modelling.utils.read_products import lime_product_names, lime_products
from src.lake_modelling.utils.run_products import (
    plot_multiple_products,
    run_multiple_products,
)
from src.lake_modelling.utils.user_inputs import (
    get_lake_params,
    get_product,
)


def app():
    """Main function for the 'lake_modelling' page."""
    st.markdown("## Lake modelling")
    plot_lib = st.selectbox(
        "Choose a plotting library:", options=["Altair", "Matplotlib"]
    )

    products = lime_product_names(lime_products(LIME_PRODUCTS_DATA))

    area, depth, tau, flow_prof, pH_lake0, toc_lake0 = get_lake_params()
    lake = Lake(area, depth, tau, flow_prof, pH_lake0, toc_lake0)
    lake.plot_flow_profile(plot_lib)

    name = get_product(products)
    prod = LimeProduct(name)
    prod.plot_column_data(plot_lib)

    st.markdown("## Result")
    res_df = run_multiple_products(lake, products)
    plot_multiple_products(res_df, pH_lake0, plot_lib)

    return None
