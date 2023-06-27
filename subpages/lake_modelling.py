import streamlit as st
import altair as alt

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

from src.lake_modelling.utils.plot import plot_result


def app():
    """Main function for the 'lake_modelling' page."""
    st.markdown("## Lake modelling")

    products = lime_product_names(lime_products(LIME_PRODUCTS_DATA))
    # st.text(products)
    area, depth, tau, flow_prof, pH_lake0, colour_lake0 = get_lake_params()

    name, n_months = get_prod_and_duration(products)

    new_lake = Lake(area, depth, tau, flow_prof, pH_lake0, colour_lake0)
    new_prod = LimeProduct(name)

    new_model = Model(lake=new_lake, lime_product=new_prod, n_months=n_months)

    df = new_model.run()

    st.markdown("## New Model Result")
    ph_chart = (
        alt.Chart(df)
        .mark_line()
        .encode(x=alt.X("date", axis=alt.Axis(title="Months", grid=True)), y="pH")
    )
    ca_chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X(
                "date",
                axis=alt.Axis(title="Months", grid=True),
            ),
            y=alt.Y("Delta Ca (mg/l)", axis=alt.Axis(title="\u0394Ca (mg/l)")),
        )
    )
    st.altair_chart(ca_chart, use_container_width=True)
    st.altair_chart(ph_chart, use_container_width=True)
    # st.altair_chart(alt.vconcat(ca_chart, ph_chart), use_container_width=True)
    return None
