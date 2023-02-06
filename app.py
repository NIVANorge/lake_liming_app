import streamlit as st
from streamlit_option_menu import option_menu

import subpages.column_test
import subpages.home
import subpages.lake_modelling

PAGES = {
    "Home": subpages.home,
    "Column tests": subpages.column_test,
    "Lake modelling": subpages.lake_modelling,
}


def main():
    """Main function of the app."""
    st.title("Lake liming app")
    st.sidebar.image(r"./images/niva-logo.png", use_column_width=True)
    with st.sidebar:
        selection = option_menu(
            None,
            options=["Home", "Column tests", "Lake modelling"],
            icons=["house", "clipboard-data", "droplet"],
            default_index=0,
        )
    page = PAGES[selection]
    page.app()


if __name__ == "__main__":
    main()
