import streamlit as st
from src.lake_modelling.utils.lake_model import (
    LIME_PRODUCTS_DATA,
    Lake,
    LimeProduct,
    MM_Ca,
    MM_CaCO3,
    MM_Mg,
    MM_MgCO3,
)
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
    st.markdown(
        f"**Sammensetning etter masse:** {prod.ca_pct:.1f} % Ca ({prod.ca_pct*MM_CaCO3/MM_Ca:.1f} % CaCO3) "
        f"og {prod.mg_pct:.1f} % Mg ({prod.mg_pct*MM_MgCO3/MM_Mg:.1f} % MgCO3)."
    )
    st.markdown(
        f"**Nøytraliserende verdi:** {prod.ca_pct*MM_CaCO3/MM_Ca + 1.19*prod.mg_pct*MM_MgCO3/MM_Mg:.1f} %."
    )
    prod.plot_column_data(plot_lib)

    st.markdown("## Innsjømodellering")
    area, depth, tau, flow_prof, pH_lake0, pH_inflow, toc_lake0 = get_lake_params()
    lake = Lake(area, depth, tau, flow_prof, pH_lake0, pH_inflow, toc_lake0)
    lake.plot_flow_profile(plot_lib)

    res_df = run_multiple_products(lake, products)
    st.markdown("### Modell resultater")
    # with st.expander("Help"):
    #     st.markdown(
    #         """
    #     The plots are interactive:
    #      * Click on the series names in the legend to turn curves on/off.
    #      * Use `SHIFT + Click` to select multiple curves.
    #      * Use your mouse wheel to zoom in/out.
    #      * Double-click to return to the full extent.
    #      * Hover on any line to see details as "tooltips".

    #     Dashed horizontal lines on the pH plot mark the lake's initial and inflow pH.
    #     """
    #     )
    with st.expander("Hjelp"):
        st.markdown(
            """
        Plottene er interaktive:
         * Klikk på serienavnene i forklaringen for å slå kurver på/av.
         * Bruk `SHIFT + Klikk` for å velge flere kurver.
         * Bruk musehjulet til å zoome inn/ut.
         * Dobbeltklikk for å gå tilbake til hele omfanget.
         * Hold musepekeren på en linje for å se detaljer som "verktøytips".
        
        Stiplede horisontale linjer på pH-plottet markerer innsjøens start- og innløps-pH.
        """
        )
    plot_multiple_products(res_df, pH_lake0, pH_inflow, plot_lib)

    return None