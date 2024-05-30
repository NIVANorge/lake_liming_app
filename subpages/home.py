import streamlit as st


def app():
    """Main function for the 'home' page."""
    st.markdown(
        """For å komme i gang, velg ett av alternativene fra venstre sidefelt. For 
        fullstendige detaljer om applikasjonen og hvordan du bruker den, se 
        <a href="https://nivanorge.github.io/lake_liming_app/" target="_blank">Dokumentasjonen</a>.""",
        unsafe_allow_html=True,
    )

    return None