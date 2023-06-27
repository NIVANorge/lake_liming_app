import streamlit as st
import altair as alt

from src.lake_modelling.utils.read_products import (
    get_lime_product_names,
    get_lime_products,
)

from src.lake_modelling.utils.ca_model import run_ca_model

from src.lake_modelling.utils.user_inputs import (
    get_duration,
    get_initial_cond,
    get_lake_params,
    get_lim_param,
)

from src.lake_modelling.utils.lake_model import Model, Lake, LimeProduct

from src.lake_modelling.utils.plot import plot_result

LIME_PRODUCTS_DATA = "data/lime_products.xlsx"


def app():
    """Main function for the 'lake_modelling' page."""
    st.markdown("## Lake modelling")

    init_cond = get_initial_cond()

    lake = get_lake_params()

    n_months = get_duration()

    products = get_lime_products(LIME_PRODUCTS_DATA)

    lim_param = get_lim_param(n_months, get_lime_product_names(products))

    ca_sim = run_ca_model(init_cond, lake, lim_param, products)

    # plot_result(ca_sim.reset_index(), "index", "Ca (mg/l)")

    new_lake = Lake()
    new_prod = LimeProduct("SK2")

    new_model = Model(new_lake, new_prod)

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
