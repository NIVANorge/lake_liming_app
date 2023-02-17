import pandas as pd
from numpy import trapz
from scipy.integrate import simpson

# TODO: uninstall nptyping
#from nptyping import NDArray, Float
import numpy.typing as npt

def integrate(y:npt.ArrayLike, x:npt.ArrayLike, method:str):
    if method == "trapezoidal":
        res = trapz(y, x)
    else:
        res = simpson(y, x)

    return res


def get_inst_dissolution(df, f_par, test_type, element, method):

    assert test_type in (
        "pH",
        "od",
    ), "'test_type' must be either 'pH' or 'od'"

    # populate constant based on test_type
    if (test_type == 'pH'):
        col_name = test_type
        xlabel = test_type+" (-)"
        od = 1
        percent = 100
    else:
        col_name = 'Lime_added_mg/l'
        xlabel = "Lime added (mg/l)"
        od = 1
        percent = 1

    col_groups = df.groupby("Column")
    col_list = []
    x_list = []
    inst_diss_list_pct = []

    for col, col_df in col_groups:
        ########################### How can I take this out to a separate func?
        col_df.sort_values("Depth_m", inplace=True)
        x_values = col_df[col_name].iloc[0]
        if (test_type == 'od'): od = x_values
        ys = col_df[element + "_mg/l"].values
        xs = col_df["Depth_m"].values
        xmin, xmax = xs.min(), xs.max()

        res = integrate(ys, xs, method)
        # TODO: Where did the *10 in delimiter disappear?
        inst_diss_pct = percent * res / (od * f_par * (xmax - xmin))

        col_list.append(col)
        x_list.append(x_values)
        inst_diss_list_pct.append(inst_diss_pct)
        #######################################################################
    res_df = pd.DataFrame(
        {
            "Column": col_list,
            xlabel: x_list,
            "Dissolution (%)": inst_diss_list_pct,
        }
    )
    res_df.set_index("Column", inplace=True)

    return res_df
