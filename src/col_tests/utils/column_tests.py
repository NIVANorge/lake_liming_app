import altair as alt
import streamlit as st

from src.col_tests.utils.inst_dissolution import get_inst_dissolution

def get_test_results(df, test_input, test_type="instantaneous", method="trapezoidal"):
    """Calculate results for either the instantaneous dissolution or
    overdosing factor column tests. This involves estimating the area
    under a curve. Two methods for solving this are supported.

    Args
        df (DataFrame):     Data from a test result worksheet of the template.
        test_input (float): Instantaneous test:
                                Expected Ca concentration in the column if all dissolved
                                and evenly mixed
                            Overdosing test:
                                Percentage of Ca in the lime being tested.
        test_type (str):    Default 'instantaneous'. Either 'instantaneous' or 'overdosing'.
        method (str):       Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.
                            Method to use for integration. See
                             https://en.wikipedia.org/wiki/Trapezoidal_rule
                            and
                             https://en.wikipedia.org/wiki/Simpson%27s_rule
                            for details.

    Returns
        Dataframe with column ID as the index and
        columns pH and instantaneous dissolution (in %) for instantaneous test
        or
        overdosing amount (in mg/l) and overdosing factor (dimensionless)
        for overdosing test.

    """
    assert test_type in (
        "instantaneous",
        "overdosing",
    ), "'test_type' must be either 'instantaneous' or 'overdosing'."
    assert method in (
        "trapezoidal",
        "simpson",
    ), "'method' must be either 'trapezoidal' or 'simpson'."

    res_df = get_inst_dissolution(df, test_input, test_type, "Ca", method)

    # Adjust the dissolution to overdosing factor
    if (test_type == 'overdosing'):
        res_df["Overdosing factor (-)"] = (
            res_df["Dissolution (%)"].max() / res_df["Dissolution (%)"]
        )
        res_df.sort_values("Overdosing factor (-)", inplace=True)
        del res_df["Dissolution (%)"]

    res_df = res_df.round(1)

    return res_df


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
