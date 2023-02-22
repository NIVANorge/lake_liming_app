from src.col_tests.utils.inst_dissolution import get_inst_dissolution


def get_test_results(df, element, element_prop, test_type="instantaneous", method="trapezoidal"):
    """Calculate results for either the instantaneous dissolution or
    overdosing factor column tests. This involves estimating the area
    under a curve. Two methods for solving this are supported.

    Args
        df:         DataFrame. Data from a test result worksheet of the template.
        element:    Str. Chemical element. Either 'Ca' or 'Mg'
        element_prop:   Float. Proportion of the element in lime by mass
        test_type:  Str. Default 'instantaneous'. Either 'instantaneous' or 'overdosing'.
        method:     Str. Default 'trapezoidal'. Either 'trapezoidal' or 'simpson'.
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

    res_df = get_inst_dissolution(df, element, element_prop, test_type, method)

    # Adjust the dissolution to overdosing factor if needed
    if (test_type == 'overdosing'):
        res_df["Overdosing factor (-)"] = (
            res_df["Dissolution (%)"].max() / res_df["Dissolution (%)"]
        )
        res_df.sort_values("Overdosing factor (-)", inplace=True)
        del res_df["Dissolution (%)"]

    res_df = res_df.round(1)

    return res_df
