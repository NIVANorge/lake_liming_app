import altair as alt
import streamlit as st

from src.col_tests.utils.column_tests import get_test_results


def get_concentrations(par_val_dict, element):
    """ Calculates lime and element concentrations
    as well as proportion of the element in lime by mass.

    Args
        par_val_dict:   Dict. Dictionary of parameter values from parameter worksheet
        element:        Str. Chemical element to use. Either 'Ca' or 'Mg'

    Returns
        Tuple of lime and element concentration and element proportion as floats.
    """

    lime_conc_all_dis = (
        1000 * par_val_dict["mass_lime_g"] / par_val_dict["water_vol_l"]
       )

    element_percentage = par_val_dict[f'lime_prod_{element.lower()}_pct']
    element_prop = element_percentage / 100
    element_conc_all_dis = lime_conc_all_dis * element_prop

    return lime_conc_all_dis, element_conc_all_dis, element_prop


def plot_and_table(df, title):
    # TODO: df must be of 2 columns - xaxis and yaxis
    """ Creates a table and chart from DataFrame.

    Args
        df:     DataFrame of values to plot
        title:  Str. Plot title

    Returns
        None. Displays the table and chart in streamlit.
    """

    # Table
    st.dataframe(
        df.style.format("{:.1f}"), use_container_width=True
    )

    # Plot
    inst_chart = make_chart(
        df,
        df.columns[0],
        df.columns[1],
        title,
    )
    st.altair_chart(inst_chart, use_container_width=True)


def make_chart(df, x_col, y_col, title):
    """Make a simple Altair line chart where data points have tooltips.

    Args
        df:    Dataframe with x- and y-data
        x_col: Str. Name of column in 'df' with x-values
        y_col: Str. Name of column in 'df' with y-values
        title: Str. Title for chart

    Returns
        Altair chart object.
    """
    pts = (
        alt.Chart(df, title=title)
        .mark_circle()
        .encode(x=x_col, y=y_col, tooltip=[x_col, y_col])
    )

    lines = (
        alt.Chart(df).mark_area(color="lightblue", line=True).encode(x=x_col, y=y_col)
    )

    chart = lines + pts

    return chart


def display_results(par_val, df, element="Ca", test_type="instantaneous", method="trapezoidal"):
    """Display results for either the instantaneous dissolution or
    overdosing factor column tests. Two methods are supported.

    Args
        par_val:    Dict. Dictionary of parameter names & values from the parameter
                    worksheet of the spreadsheet.
        df:         DataFrame. Data from a test result worksheet of the spreadsheet.
        element:    Str. Default 'Ca'. Either 'Ca' or 'Mg'.
        test_type:  Str. Default 'instantaneous'. Either 'instantaneous' or 'overdosing'.
        method:     Str. Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.

    Returns
        None
    """

    assert element in ("Ca", "Mg",
                       ), "'element' must be either 'Ca' or 'Mg'."

    assert test_type in (
        "instantaneous",
        "overdosing",
    ), "'test_type' must be either 'instantaneous' or 'overdosing'."

    assert method in (
        "trapezoidal",
        "simpson",
    ), "'method' must be either 'trapezoidal' or 'simpson'."

    lime_conc, element_conc, element_prop = get_concentrations(par_val, element)

    if (test_type == "instantaneous"):
        test_title = "Momentanoppløsning"
        st.markdown(f"### {test_title}")
        st.markdown(
            f"**Kalk tilsatt:** {lime_conc:.1f} mg/l ({element_conc:.1f} mg/l of {element})"
        )
    else:
        test_title = "Overdoseringsfaktorer"
        st.markdown(f"### {test_title}")
        st.markdown(f"**Kolonne pH:** {df['pH'].iloc[0]}")

    results_df = get_test_results(df, element, element_prop, test_type, method)

    plot_and_table(results_df, f"{test_title} test")
