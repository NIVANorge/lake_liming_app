import streamlit as st
from src.comparison_factors.utils.plot_factors import plot_factors


def app():
    """Main function for the 'comparison_factors' page."""

    st.markdown("## Omregningsfaktorer")
    st.markdown(
        """
    These plots show the simulated effectiveness of different lime products compared
    to a reference standard for lakes with various mean depths and water residence 
    times. **Values less than one indicate the product is more effective than the 
    standard; values greater than one imply it is less effective (per unit mass)**. 
    
    The reference used for these plots is `Standard Kalk Kat3`.

    See the 
    [Documentation](https://nivanorge.github.io/lake_liming_app/user-guide.html#sec-comparison-factors) 
    for details.
    """
    )
    with st.expander("Help"):
        st.markdown(
            """
        The plots are interactive:
         * Click on the series names in the legend to turn curves on/off.
         * Use `SHIFT + Click` to select multiple curves.
         * Use your mouse wheel to zoom in/out.
         * Double-click to return to the full extent.
         * Hover on any line to see details as "tooltips".
        """
        )
    chart = plot_factors()
    st.altair_chart(chart, use_container_width=True)