import streamlit as st
import subpages.column_test
import subpages.home
import subpages.lake_modelling
from streamlit_option_menu import option_menu

PAGES = {
    "Forside": subpages.home,
    "Last opp kolonnetestdata": subpages.column_test,
    "Innsjømodellering": subpages.lake_modelling,
    "Omregningsfaktorer": subpages.comparison_factors,
}


def main():
    """Main function of the app."""
    st.title("Innsjøkalking applikasjon")
    st.sidebar.image(r"./images/niva-logo.png", use_column_width=True)
    with st.sidebar:
        selection = option_menu(
            None,
            options=[
                "Forside",
                "Innsjømodellering",
                "Omregningsfaktorer",
                "Last opp kolonnetestdata",
            ],
            icons=["house", "droplet", "graph-down", "clipboard-data"],
            default_index=0,
        )
    page = PAGES[selection]
    page.app()


if __name__ == "__main__":
    main()