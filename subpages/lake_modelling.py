import streamlit as st

from src.lake_modelling.utils.read_products import (
    lime_product_names,
    lime_products,
)

from src.lake_modelling.utils.user_inputs import (
    get_prod_and_duration,
    get_lake_params,
)

from src.lake_modelling.utils.lake_model import (
    Model,
    Lake,
    LimeProduct,
    LIME_PRODUCTS_DATA,
)


def app():
    """Main function for the 'lake_modelling' page."""
    st.markdown("## Lake modelling")
    plot_lib = st.selectbox(
        "Choose a plotting library:", options=["Altair", "Matplotlib"]
    )

    products = lime_product_names(lime_products(LIME_PRODUCTS_DATA))

    area, depth, tau, flow_prof, pH_lake0, colour_lake0 = get_lake_params()
    new_lake = Lake(area, depth, tau, flow_prof, pH_lake0, colour_lake0)
    new_lake.plot_flow_profile(plot_lib)

    name, n_months = get_prod_and_duration(products)
    new_prod = LimeProduct(name)
    new_prod.plot_column_data(plot_lib)

    new_model = Model(lake=new_lake, lime_product=new_prod, n_months=n_months)
    st.markdown("## Result")

    new_model.plot_result(plot_lib)

    return None
