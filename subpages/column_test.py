from io import BytesIO
import pandas as pd
import streamlit as st
import altair as alt
from numpy import trapz
from scipy.integrate import simpson


def app():
    """Main function for the 'column_test' page."""
    st.markdown("## Column tests")
    data_file = st.sidebar.file_uploader("Upload template")
    if data_file:
        st.session_state["data_file"] = data_file

    if "data_file" in st.session_state:
        data_file = st.session_state["data_file"]
        with st.spinner("Reading data..."):
            st.markdown(f"**File name:** `{data_file.name}`")
            read_template(data_file)
            par_df = st.session_state["par_df"]
            inst_df = st.session_state["inst_df"]
            od_df = st.session_state["od_df"]

            # Print basic info for test as a whole
            par_val_dict = par_df.to_dict()["Value"]
            lime_conc_all_dis = (
                1000 * par_val_dict["mass_lime_g"] / par_val_dict["water_vol_l"]
            )
            ca_conc_all_dis = lime_conc_all_dis * par_val_dict["lime_prod_ca_pct"] / 100
            st.markdown(
                f"""
                ### Processing data for product: `{par_val_dict['lime_product_name']}`
                **Total Ca content by mass:** {par_val_dict['lime_prod_ca_pct']} %

                **Concentration of lime added:** {lime_conc_all_dis:.1f} mg/l
            """
            )

            left_col, right_col = st.columns(2)

            # Instantaneous test
            with left_col:
                # Table
                inst_res_df = instantaneous_test(
                    inst_df, ca_conc_all_dis, method="trapezoidal"
                )
                st.dataframe(
                    inst_res_df.style.format("{:.1f}"), use_container_width=True
                )

                # Plot
                inst_chart = make_chart(
                    inst_res_df,
                    "pH",
                    "Dissolution (%)",
                    "Instantaneous dissolution test",
                )
                st.altair_chart(inst_chart, use_container_width=True)

            # Overdosing test
            with right_col:
                # Table
                od_res_df = overdosing_test(
                    od_df, par_val_dict["lime_prod_ca_pct"], method="trapezoidal"
                )
                st.dataframe(od_res_df.style.format("{:.1f}"), use_container_width=True)

                # Plot
                od_chart = make_chart(
                    od_res_df,
                    "Lime added (mg/l)",
                    "Overdosing factor (-)",
                    "Overdosing test",
                )
                st.altair_chart(od_chart, use_container_width=True)

    return None


def check_column_values(df, col_name, expected_set):
    """Checks the unique values in 'df' column 'col_name' are equal
    to the set 'expected_set.'

    Args
        df:           Dataframe of data
        col_name:     Str. Name of column in 'df'
        expected_set: Set of expected values

    Returns
        Stops Streamlit with an error if the the unique values are not as
        expected. Otherwise None.
    """
    assert isinstance(expected_set, set), "'expected_set' must be a set."
    unique_vals = set(df[col_name].unique())
    if unique_vals != expected_set:
        msg = f"{col_name} must only contain values {expected_set} (not {unique_vals})."
        st.error(msg)
        st.stop()
    else:
        return None


def read_template(template_path):
    """Read a data template supplied by user and add results to the session state.

    Args
        template_path: Str. Path to completed Excel template

    Returns
        None. Values are added to the session state.
    """
    par_df = pd.read_excel(template_path, sheet_name="parameters", index_col=0)
    inst_df = pd.read_excel(template_path, sheet_name="instantaneous_dissolution_data")
    od_df = pd.read_excel(template_path, sheet_name="overdosing_data")

    # Check input template
    inst_unique_vals = {
        "Column": ("A", "B", "C", "D", "E"),
        "pH": (4.0, 4.5, 5.0, 5.5, 6.0),
        "Depth_m": (0.0, 0.4, 0.8, 1.2, 1.6, 2.0),
    }
    for key, val in inst_unique_vals.items():
        check_column_values(inst_df, key, set(val))

    od_unique_vals = {
        "Column": ("A", "B", "C", "D", "E"),
        "pH": (4.6,),
        "Lime_added_mg/l": (10, 20, 35, 50, 85),
        "Depth_m": (0.0, 0.4, 0.8, 1.2, 1.6),
    }
    for key, val in od_unique_vals.items():
        check_column_values(od_df, key, set(val))

    st.session_state["par_df"] = par_df
    st.session_state["inst_df"] = inst_df
    st.session_state["od_df"] = od_df

    return None


def instantaneous_test(df, conc_all_dis, method="trapezoidal"):
    """Calculate results for the instantaneous dissolution test. This involves
    estimating the area under a curve. Two methods for solving this are supported.

    Args
        df:           Dataframe. Data from 'instantaneous_dissolution_data' worksheet of
                      template.
        conc_all_dis: Float. Expected concentration in the column if all Ca was dissolved
                      and evenly mixed
        method:       Str. Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.
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

    col_groups = df.groupby("Column")
    col_list = []
    ph_list = []
    inst_diss_list_pct = []
    st.markdown("### Instantaneous dissolution")
    for col, col_df in col_groups:
        col_df.sort_values("Depth_m", inplace=True)
        ph = col_df["pH"].iloc[0]
        ys = col_df["Ca_mg/l"].values
        xs = col_df["Depth_m"].values
        xmin, xmax = xs.min(), xs.max()

        if method == "trapezoidal":
            res = trapz(ys, xs)
        else:
            res = simpson(ys, xs)
        inst_diss_pct = 100 * res / (conc_all_dis * (xmax - xmin))

        col_list.append(col)
        ph_list.append(ph)
        inst_diss_list_pct.append(inst_diss_pct)

    res_df = pd.DataFrame(
        {
            "Column": col_list,
            "pH": ph_list,
            "Dissolution (%)": inst_diss_list_pct,
        }
    )
    res_df.set_index("Column", inplace=True)
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

    col_groups = df.groupby("Column")
    col_list = []
    od_list = []
    inst_diss_list_pct = []
    st.markdown("### Overdosing factors")
    for col, col_df in col_groups:
        col_df.sort_values("Depth_m", inplace=True)
        od = col_df["Lime_added_mg/l"].iloc[0]
        ys = col_df["Ca_mg/l"].values
        xs = col_df["Depth_m"].values
        xmin, xmax = xs.min(), xs.max()

        if method == "trapezoidal":
            res = trapz(ys, xs)
        else:
            res = simpson(ys, xs)
        inst_diss_pct = res / (od * lime_prod_ca_pct * (xmax - xmin))

        col_list.append(col)
        od_list.append(od)
        inst_diss_list_pct.append(inst_diss_pct)

    res_df = pd.DataFrame(
        {
            "Column": col_list,
            "Lime added (mg/l)": od_list,
            "inst_diss_pct": inst_diss_list_pct,
        }
    )
    res_df["Overdosing factor (-)"] = (
        res_df["inst_diss_pct"].max() / res_df["inst_diss_pct"]
    )
    res_df.sort_values("Overdosing factor (-)", inplace=True)
    res_df.set_index("Column", inplace=True)
    del res_df["inst_diss_pct"]
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

    lines = alt.Chart(df).mark_line().encode(x=x_col, y=y_col)

    chart = lines + pts

    return chart
