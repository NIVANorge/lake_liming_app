import streamlit as st


def app():
    """Main function for the 'home' page."""
    st.markdown(
        """A starting point for discussing the features and layout for the lake liming application.
    """
    )
    st.info(
        """This application is a prototype.
    """,
        icon="ℹ️",
    )

    with st.expander("Getting started"):
        st.markdown(
            """
        To explore model output based on the **existing database** of lime products, choose the
        `Lake modelling` tab from the left sidebar.
            
        If you wish to upload and explore **new column test data**, first download and fill-in
        the Excel template 
        [here](https://github.com/NIVANorge/lake_liming_app/blob/main/data/liming_app_data_template_v1-1.xlsx).
        Then choose `Upload column test data` from the left sidebar to view the results.
        """
        )

    return None