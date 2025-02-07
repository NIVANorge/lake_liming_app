import altair as alt
import pandas as pd

OMFAC_CSV = r"./data/omregningsfaktorer.csv"


def read_factors():
    """Read omregningsfactors."""
    df = pd.read_csv(OMFAC_CSV)
    df["Dybde (m)"] = df["Dybde (m)"].astype(str) + " m"

    return df


def plot_factors():
    """Create a 2x2 facet grid showing omregningsfaktorer."""
    df = read_factors()
    checkbox_selection = alt.selection_point(fields=["Produkt"], bind="legend")

    base_chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "Oppholdstid (år):Q",
                scale=alt.Scale(type="log", base=10, domain=(0.2, 3)),
            ),
            y=alt.Y(
                "Faktor (-):Q",
                scale=alt.Scale(domain=(0.8, 2)),
                axis=alt.Axis(title="Faktor (-)"),
            ),
            color="Produkt:N",
            opacity=alt.condition(checkbox_selection, alt.value(1), alt.value(0)),
            tooltip=alt.condition(
                checkbox_selection,
                [
                    alt.Tooltip("Oppholdstid (år):Q"),
                    alt.Tooltip("Faktor (-):Q"),
                    alt.Tooltip("Produkt:N"),
                ],
                alt.value(None),
            ),
        )
        .add_params(checkbox_selection)
    )

    line = (
        alt.Chart()
        .mark_rule(color="red", strokeDash=[10, 10])
        .encode(
            x=alt.X(
                "a:Q",
                scale=alt.Scale(domain=(0.2, 3)),
                axis=alt.Axis(title="Oppholdstid (år)"),
            ),
        )
        .transform_filter((alt.datum["Dybde (m)"] == "10 m"))
        .transform_calculate(a="0.7")
    )

    chart = (
        alt.layer(base_chart, line, data=df)
        .properties(width=300, height=300)
        .facet(facet=alt.Facet("Dybde (m):N", sort=[5, 10, 15, 20]), columns=2)
        .resolve_scale(x="independent", y="independent")
        .interactive()
    )

    return chart