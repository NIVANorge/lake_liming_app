"""Unit tests for utility functions"""
import pandas as pd
import numpy as np
from numpy import trapz
from scipy.integrate import simpson

import pytest
from pytest import mark

# TODO: uninstall nptyping
#from nptyping import NDArray, Float
import numpy.typing as npt

def mock_input_data(type, element):
    pass

#inst_ca_data = pd.Series([2.82,2.62,2.64,2.76,2.81,2.16,2.01,1.93,1.91,1.90,1.77,1.71,1.66,1.64,1.75,1.64,1.72,1.62,1.54,1.63,1.56,1.49,1.54,1.51,1.00])
#od_ca_data = pd.Series([2.03,1.98,2.03,2.04,1.85,3.37,3.17,3.22,3.66,3.53,4.57,4.24,4.56,4.73,4.78,4.45,4.34,4.69,4.5,4.62,5.04,5.01,4.98,5.05,5.07])


def integrate(y:npt.ArrayLike, x:npt.ArrayLike, method:str):
    if method == "trapezoidal":
        res = trapz(y, x)
    else:
        res = simpson(y, x)

    return res

inst_ca_test = [2.82,2.62,2.64,2.76,2.81]
inst_ca_depth = [0.0, 0.4, 0.8, 1.2, 1.6]

result = integrate(inst_ca_test, inst_ca_depth, "trapezoidal")
print(result)

def get_inst_dissolution(df, f_par, test_type, element):

    assert test_type in (
        "pH",
        "od",
    ), "'test_type' must be either 'pH' or 'od'"

    # populate constant based on test_type
    if (test_type == 'pH'):
        xlabel = 'pH'
        od = 1
        percent = 100
    else:
        xlabel = '"Lime_added_mg/l"'
        od = 1
        percent = 1

    col_groups = df.groupby("Column")
    col_list = []
    x_list = []
    inst_diss_list_pct = []

    for col, col_df in col_groups:
        col_df.sort_values("Depth_m", inplace=True)
        x_values = col_df[xlabel].iloc[0]
        ys = col_df[element + "_mg/l"].values
        xs = col_df["Depth_m"].values
        xmin, xmax = xs.min(), xs.max()

        res = integrate(ys, xs, "trapezoidal")
        # TODO: Where did the *10 in delimiter disappear?
        inst_diss_pct = percent * res / (od * f_par * (xmax - xmin))

        col_list.append(col)
        x_list.append(x_values)
        inst_diss_list_pct.append(inst_diss_pct)

    res_df = pd.DataFrame(
        {
            "Column": col_list,
            xlabel: x_list,
            "Dissolution (%)": inst_diss_list_pct,
        }
    )
    res_df.set_index("Column", inplace=True)
