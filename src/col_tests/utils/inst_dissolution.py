import pandas as pd
from numpy import trapz
from scipy.integrate import simpson

from src.col_tests.utils.test_settings import get_test_settings


def integrate(y, x, method):
    """ Approximates integral for inst. dissolution equation.

    Args
        y:          Input array over which to integrate
        x:          Array of sample points corresponding to the input array
        method:     Str. Approximation rule. Either 'trapezoidal' or 'simpson'

    Returns
        res:        Float. Approximated integral value
    """
    if method == "trapezoidal":
        res = trapz(y, x)
    else:
        res = simpson(y, x)

    return res


def calculate_inst_dissolution(col_groups, element, test_input, test_type, method):
    """ Calculates instantaneous dissolution for test columns.

    Args
        col_groups:     DataFrameGroupBy. DataFrame of input data grouped by test columns
        element:        Str. Chemical element for which to calculate. Either 'Ca' or 'Mg'
        test_input:     Float. Test parameter value
        test_type:      Str. Type of the test. Either 'instantaneous' or 'overdosing'
        method:         Str. Approximation rule. Either 'trapezoidal' or 'simpson'

    Returns
        inst_dist_list: List of instantaneous dissolution values for each test column
    """
    inst_diss_list = []
    param_settings = get_test_settings(test_type)

    for col, col_df in col_groups:
        col_df.sort_values("Depth_m", inplace=True)
        ys = col_df[element + "_mg/l"].values
        xs = col_df["Depth_m"].values
        xmin, xmax = xs.min(), xs.max()

        res = integrate(ys, xs, method)
        inst_diss_pct = param_settings['percent_factor'] * res / (param_settings['od_factor'][col] * test_input * (xmax - xmin))
        inst_diss_list.append(inst_diss_pct)

    return inst_diss_list


def get_inst_dissolution(df, element, test_input, test_type, method):
    """ Creates DataFrame of instantaneous dissolution results.

    Args
        df:         DataFrame of original input data (worksheet of the template)
        element:    Str. Chemical element for which to create the result df. Either 'Ca' or 'Mg'
        test_input: Float. Test parameter value
        test_type:  Str. Type of the test. Either 'instantaneous' or 'overdosing'
        method:     Str. Approximation rule. Either 'trapezoidal' or 'simpson'

    Returns
        res_df:     Resulting DataFrame of dissolution value for each test column
    """

    param_settings = get_test_settings(test_type)

    col_groups = df.groupby("Column")
    col_list = df["Column"].unique().tolist()
    x_list = df[param_settings['col_name']].unique().tolist()

    inst_diss_list_pct = calculate_inst_dissolution(col_groups, element, test_input, test_type, method)

    res_df = pd.DataFrame(
        {
            "Column": col_list,
            param_settings['xlabel']: x_list,
            "Dissolution (%)": inst_diss_list_pct,
        }
    )
    res_df.set_index("Column", inplace=True)

    return res_df
