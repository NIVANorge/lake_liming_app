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
            """Some help text here.
        """
        )

    return None
