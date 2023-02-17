import altair as alt
import streamlit as st

from src.utils.inter import get_inst_dissolution

def instantaneous_test(df, lime_conc_all_dis, ca_conc_all_dis, method="trapezoidal"):
    """Calculate results for the instantaneous dissolution test. This involves
    estimating the area under a curve. Two methods for solving this are supported.

    Args
        df:                Dataframe. Data from 'instantaneous_dissolution_data' worksheet of
                           template.
        lime_conc_all_dis: Float. Expected lime concentration in the column if all dissolved
                           and evenly mixed
        ca_conc_all_dis:   Float. Expected Ca concentration in the column if all dissolved
                           and evenly mixed
        method:            Str. Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.
                           Method to use for integration. See
                             https://en.wikipedia.org/wiki/Trapezoidal_rule
                           and
                             https://en.wikipedia.org/wiki/Simpson%27s_rule
                           for details.

    Returns
        Dataframe with column ID as the index and columns pH and instantaneous
        dissolution (in %).

    """
    assert method in (
        "trapezoidal",
        "simpson",
    ), "'method' must be either 'trapezoidal' or 'simpson'."

    st.markdown("### Instantaneous dissolution")
    st.markdown(
        f"**Lime added:** {lime_conc_all_dis:.1f} mg/l ({ca_conc_all_dis:.1f} mg/l of Ca)"
    )

    res_df = get_inst_dissolution(df, ca_conc_all_dis, "pH", "Ca", method)

    res_df = res_df.round(1)

    return res_df


def overdosing_test(df, lime_prod_ca_pct, method="trapezoidal"):
    """Calculate results for the overdosing test. This involves estimating the area under
    a curve. Two methods for solving this are supported.

    Args
        df:               Dataframe. Data from 'overdosing_data' worksheet of the template.
        lime_prod_ca_pct: Float. Percentage of Ca in the lime being tested
        method:           Str. Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.
                          Method to use for integration. See
                            https://en.wikipedia.org/wiki/Trapezoidal_rule
                          and
                            https://en.wikipedia.org/wiki/Simpson%27s_rule
                          for details.

    Returns
        Dataframe with columns overdosing amount (in mg/l) and overdosing factor
        (dimensionless).

    """
    assert method in (
        "trapezoidal",
        "simpson",
    ), "'method' must be either 'trapezoidal' or 'simpson'."

    st.markdown("### Overdosing factors")
    st.markdown("**Column pH:** 4.6")

    res_df = get_inst_dissolution(df, lime_prod_ca_pct, "od", "Ca", method)
    # Adjust the dissolution to factor
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
