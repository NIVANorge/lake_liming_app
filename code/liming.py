import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import trapz
from scipy.integrate import simpson

plt.style.use("ggplot")


def validate_input(template_path):
    """Performs checking of template supplied by user.
    Args
        template_path: Str. Path to completed Excel template

    Returns
        None. If all checks pass, otherwise raises error.
    """

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
        Dataframe with columns pH and instantaneous dissolution (in %).

    """
    assert method in (
        "trapezoidal",
        "simpson",
    ), "'method' must be either 'trapezoidal' or 'simpson'."

    col_groups = df.groupby("Column")
    ph_list = []
    inst_diss_list_pct = []
    print("\nInstantaneous dissolution for column tests (varying pH):")
    for col, col_df in col_groups:
        ph = col_df["pH"].iloc[0]
        ys = col_df["Ca_mg/l"].values
        xs = col_df["Depth_m"].values

        if method == "trapezoidal":
            res = trapz(ys, xs)
        else:
            res = simpson(ys, xs)

        inst_diss_pct = 100 * res / (2 * conc_all_dis)

        ph_list.append(ph)
        inst_diss_list_pct.append(inst_diss_pct)

        print(f"  Column {col} (pH {ph}): {inst_diss_pct:.1f} %")

    res_df = pd.DataFrame({"pH": ph_list, "inst_diss_pct": inst_diss_list_pct})

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
    od_list = []
    inst_diss_list_pct = []
    print("\nOverdosing factors for column tests (at fixed pH):")
    for col, col_df in col_groups:
        od = col_df["Lime_added_mg/l"].iloc[0]
        ys = col_df["Ca_mg/l"].values
        xs = col_df["Depth_m"].values

        if method == "trapezoidal":
            res = trapz(ys, xs)
        else:
            res = simpson(ys, xs)

        inst_diss_pct = res / (1.6 * od * lime_prod_ca_pct)

        od_list.append(od)
        inst_diss_list_pct.append(inst_diss_pct)

    res_df = pd.DataFrame({"od": od_list, "inst_diss_pct": inst_diss_list_pct})
    res_df["od_factor"] = res_df["inst_diss_pct"].max() / res_df["inst_diss_pct"]
    res_df.sort_values("od_factor", inplace=True)
    for idx, row in res_df.iterrows():
        print(
            f"  Overdosing factor ({row['od']} mg/l lime added): {row['od_factor']:.2f}"
        )

    return res_df


def column_test_summary(template_path, method="trapezoidal"):
    """Calculate results for the instantaneous dissolution and overdosing test.
    Print summary to output.

    Args
        template_path: Str. Path to completed Excel template
        method:        Str. Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.
                       Method to use for integration. See
                         https://en.wikipedia.org/wiki/Trapezoidal_rule
                       and
                         https://en.wikipedia.org/wiki/Simpson%27s_rule
                       for details.

    Returns
        None. For now...
    """
    validate_input(template_path)

    par_df = pd.read_excel(template_path, sheet_name="parameters", index_col=0)
    inst_df = pd.read_excel(template_path, sheet_name="instantaneous_dissolution_data")
    od_df = pd.read_excel(template_path, sheet_name="overdosing_data")

    # Print basic info for test as a whole
    par_val_dict = par_df.to_dict()["Value"]
    init_col_conc = 1000 * par_val_dict["mass_lime_g"] / par_val_dict["water_vol_l"]
    conc_all_diss = init_col_conc * par_val_dict["lime_prod_ca_pct"] / 100
    print(f"Processing data for product: {par_val_dict['lime_product_name']}")
    print("")
    print(f"Total Ca content by mass: {par_val_dict['lime_prod_ca_pct']} %")
    print(f"Concentration of lime added: {init_col_conc:.1f} mg/l")
    print(
        f"Ca concentration if all lime dissolved and well-mixed: {conc_all_diss:.2f} mg-Ca/l"
    )

    # Instantaneous dissolution test
    inst_res_df = instantaneous_test(inst_df, conc_all_diss, method=method)

    # Overdosing test
    od_res_df = overdosing_test(od_df, par_val_dict["lime_prod_ca_pct"], method=method)

    # Plots
    fig, axes = plt.subplots(figsize=(12, 5), nrows=1, ncols=2)
    axes[0].plot(inst_res_df["pH"], inst_res_df["inst_diss_pct"], "r-o")
    axes[0].set_xlabel("pH")
    axes[0].set_ylabel("Dissolution (%)")
    axes[0].set_title(
        f"Instantaneous dissolution curve for\n{par_val_dict['lime_product_name']}"
    )

    axes[1].plot(od_res_df["od"], od_res_df["od_factor"], "r-o")
    axes[1].set_xlabel("Lime added (mg/l)")
    axes[1].set_ylabel("Overdosing factor [-]")
    axes[1].set_title(f"Overdosing curve for\n{par_val_dict['lime_product_name']}")
