import pandas as pd
from numpy import trapz
from scipy.integrate import simpson

# TODO: uninstall nptyping
#from nptyping import NDArray, Float
import numpy.typing as npt
import streamlit as st

from src.col_tests.utils.test_settings import get_test_settings


def integrate(y, x, method):
    if method == "trapezoidal":
        res = trapz(y, x)
    else:
        res = simpson(y, x)

    return res


def calculate_inst_dissolution(col_groups, test_input, param_settings, method, element):
    inst_diss_list = []

    for col, col_df in col_groups:
        col_df.sort_values("Depth_m", inplace=True)
        ys = col_df[element + "_mg/l"].values
        xs = col_df["Depth_m"].values
        xmin, xmax = xs.min(), xs.max()

        res = integrate(ys, xs, method)
        # TODO: Where did the *10 in delimiter disappear?
        inst_diss_pct = param_settings['percent_factor'] * res / (param_settings['od_factor'][col] * test_input * (xmax - xmin))

        inst_diss_list.append(inst_diss_pct)

    return inst_diss_list


def get_inst_dissolution(df, test_input, test_type, element, method):

    param_settings = get_test_settings(test_type)

    col_groups = df.groupby("Column")
    col_list = df["Column"].unique().tolist()
    x_list = df[param_settings['col_name']].unique().tolist()

    inst_diss_list_pct = calculate_inst_dissolution(col_groups, test_input, param_settings, method, element)

    res_df = pd.DataFrame(
        {
            "Column": col_list,
            param_settings['xlabel']: x_list,
            "Dissolution (%)": inst_diss_list_pct,
        }
    )
    res_df.set_index("Column", inplace=True)

    return res_df
