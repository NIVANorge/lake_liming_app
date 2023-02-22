def get_test_settings(test_type):
    """Returns basic parameter settings for either instantaneous
    or overdosing test calculations.

    Args
        test_type:      Str. Either 'instantaneous' or 'overdosing'

    Returns
        param_settings: Dict. Dictionary of parameter values for
                        specified test type.
    """

    # TODO: Can we populate this directly from the spreadsheet instead of hardcoding?

    if (test_type == 'instantaneous'):
        param_settings = dict(
            col_name = 'pH',
            xlabel = 'pH (-)',
            lime_dose = {
                'A': 10,
                'B': 10,
                'C': 10,
                'D': 10,
                'E': 10,
            },
        )
    else:
        param_settings = dict(
            col_name = 'Lime_added_mg/l',
            xlabel = 'Lime added (mg/l)',
            lime_dose = {
                'A': 10,
                'B': 20,
                'C': 35,
                'D': 50,
                'E': 85,
            },
        )

    return param_settings
