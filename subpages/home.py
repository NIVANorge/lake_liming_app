import streamlit as st


def app():
    """Main function for the 'home' page."""
    st.markdown(
        """A starting point for discussing the features and layout for the lake liming application.
    """
    )
    st.info(
        """This application is only a prototype. The final version will likely look different.
    """,
        icon="ℹ️",
    )

    with st.expander("Getting started"):
        st.markdown(
            """Data templates for use with this application can be found 
            [here](https://github.com/NIVANorge/lake_liming_app/tree/main/data). Download the appropriate 
            template and add your data, then use the buttons in the left sidebar to upload the template 
            and explore the results.
        """
        )

    return None
