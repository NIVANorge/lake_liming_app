import pandas as pd
import streamlit as st


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
    """Reads a data template supplied by user and add results to the session state.

    Args
        template_path: Str. Path to completed Excel template

    Returns
        None. Values are added to the session state.
    """
    par_df = pd.read_excel(template_path, sheet_name="parameters", index_col=0).fillna(
        0
    )
    inst_df = pd.read_excel(
        template_path, sheet_name="instantaneous_dissolution_data"
    ).fillna(0)
    od_df = pd.read_excel(template_path, sheet_name="overdosing_data").fillna(0)

    # Check input template
    inst_unique_vals = {
        "Column": ("A", "B", "C", "D", "E"),
        "pH": (4.0, 4.5, 5.0, 5.5, 6.0),
        "Depth_m": (0.0, 0.4, 0.8, 1.2, 1.6),
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
