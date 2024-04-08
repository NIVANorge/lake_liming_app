import streamlit as st
import subpages.column_test
import subpages.home
import subpages.lake_modelling
from streamlit_option_menu import option_menu

PAGES = {
    "Home": subpages.home,
    "Upload column test data": subpages.column_test,
    "Lake modelling": subpages.lake_modelling,
}


def main():
    """Main function of the app."""
    st.title("Lake liming app")
    st.sidebar.image(r"./images/niva-logo.png", use_column_width=True)
    with st.sidebar:
        selection = option_menu(
            None,
            options=["Home", "Upload column test data", "Lake modelling"],
            icons=["house", "clipboard-data", "droplet"],
            default_index=0,
        )
    page = PAGES[selection]
    page.app()


if __name__ == "__main__":
    main()