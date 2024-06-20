import streamlit as st
from src.comparison_factors.utils.plot_factors import plot_factors


def app():
    """Main function for the 'comparison_factors' page."""

    st.markdown("## Omregningsfaktorer")
    # st.markdown(
    #     """
    # These plots show the simulated effectiveness of different lime products compared
    # to a reference standard for lakes with various mean depths and water residence
    # times. **Values less than one indicate the product is more effective than the
    # standard; values greater than one imply it is less effective (per unit mass)**.

    # The reference used for these plots is `Standard Kalk Kat3`. The vertical red dashed
    # line shows factors that Miljødirektoratet will use in the procurement of lime for  
    # watershed liming. The factors will be multipled by the amount of lime offered to
    # compare the effectiveness of different lime products.

    # See the
    # [Documentation](https://nivanorge.github.io/lake_liming_app/user-guide.html#sec-comparison-factors)
    # for details.
    # """
    # )
    st.markdown(
        """
    Disse plottene viser den simulerte effektiviteten til ulike kalkprodukter sammenlignet 
    med en referansestandard for innsjøer med ulike middeldybder og vannoppholdstider. 
    **Verdier mindre enn én indikerer at produktet er mer effektivt enn standarden; verdier 
    større enn én betyr at den er mindre effektiv (per kilogram)**.
    
    Referansen som brukes for disse plottene er `Standard Kalk Kat3`. Den vertikale røde 
    stiplede linjen viser faktorer som Miljødirektoratet vil bruke i anskaffelser for levering
    og spredning av kalk for bruk innen vassdragskalking. Faktorene vil multipliseres med 
    oppgitt mengde tilbudt kalk, dette for å regne ut behov for mengde av ulike kalkprodukter.
    
    Se [Dokumentasjon](https://nivanorge.github.io/lake_liming_app/user-guide.html#sec-comparison-factors)
    for detaljer.
    """
    )
    # with st.expander("Help"):
    #     st.markdown(
    #         """
    #     The plots are interactive:
    #      * Click on the series names in the legend to turn curves on/off.
    #      * Use `SHIFT + Click` to select multiple curves.
    #      * Use your mouse wheel to zoom in/out.
    #      * Double-click to return to the full extent.
    #      * Hover on any line to see details as "tooltips".
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
        """
        )
    chart = plot_factors()
    st.altair_chart(chart, use_container_width=True)