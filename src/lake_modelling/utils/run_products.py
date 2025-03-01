import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sn
import streamlit as st
from src.lake_modelling.utils.lake_model import LimeProduct, Model
from src.lake_modelling.utils.user_inputs import get_model_params

plt.style.use("ggplot")


def run_multiple_products(lake, products):
    """Run the same model (lake and model parameters), but for multiple lime products.
    Used to compare different products in a particular situation.

    Args
        lake:     Obj. lm.Lake object to model
        products: List. Product names to consider.

    Returns
        Dataframe with columns 'date', 'product', 'Delta Ca (mg/l)' and 'pH'.
    """
    (
        lime_dose,
        lime_month,
        spr_meth,
        spr_prop,
        F_sol,
        rate_const,
        activity_const,
        ca_aq_sat,
        n_months,
    ) = get_model_params()

    lime_tonnes = spr_prop * lime_dose * lake.volume / 1e9
    st.markdown(f"**Amount of product added: {lime_tonnes:.2f} tonnes.**")

    df_list = []
    for prod_name in products:
        prod = LimeProduct(prod_name)
        model = Model(
            lake=lake,
            lime_product=prod,
            lime_dose=lime_dose,
            lime_month=lime_month,
            spr_meth=spr_meth,
            spr_prop=spr_prop,
            F_sol=F_sol,
            rate_const=rate_const,
            activity_const=activity_const,
            ca_aq_sat=ca_aq_sat,
            n_months=n_months,
        )
        df = model.run()
        df.set_index("date", inplace=True)
        df = df.resample("D").mean().reset_index()
        df["product"] = prod_name
        df_list.append(df)
    df = pd.concat(df_list, axis="rows")

    return df


def plot_multiple_products(df, pH_lake0, pH_inflow, lib):
    """Plot results from 'run_multiple_products'.

    Args
        df:        Dataframe. As returned by 'run_multiple_products'
        pH_lake0:  Float. Lake initial pH (dimensionless)
        pH_inflow: Float. Lake inflow pH (dimensionless)
        lib:       Str. Plotting library to use. Either 'Altair' or 'Matplotlib'

    Returns
        Chart object. The chart is also added to the Streamlit app if Streamlit
        is running.
    """
    if lib == "Matplotlib":
        # Matplotlib charts
        df = df.melt(id_vars=["date", "product"])
        df.set_index("date", inplace=True)
        g = sn.relplot(
            df,
            x="date",
            y="value",
            row="variable",
            hue="product",
            kind="line",
            aspect=3,
            height=3,
            facet_kws={"sharey": False, "sharex": True},
        )
        g.axes[0, 0].set_ylim(bottom=0)
        g.axes[1, 0].axhline(y=pH_lake0, ls="--", c="k")
        g.axes[1, 0].axhline(y=pH_inflow, ls="--", c="k")
        g.axes[0, 0].set_ylabel("$\Ca_{ekv}$ (mg/l)")
        g.axes[1, 0].set_ylabel("Innsjø pH (-)")
        g.axes[1, 0].set_xlabel("")
        g.axes[0, 0].set_title("")
        g.axes[1, 0].set_title("")
        sn.move_legend(g, "upper right", bbox_to_anchor=(0.95, 0.95))
        plt.tight_layout()
        st.set_option("deprecation.showPyplotGlobalUse", False)
        st.pyplot()
    else:
        # Altair charts
        checkbox_selection = alt.selection_point(fields=["product"], bind="legend")
        init_lake_ph = (
            alt.Chart(pd.DataFrame({"pH": [pH_lake0]}))
            .mark_rule(strokeDash=[10, 10])
            .encode(y="pH")
        )
        inflow_ph = (
            alt.Chart(pd.DataFrame({"pH": [pH_inflow]}))
            .mark_rule(strokeDash=[10, 10])
            .encode(y="pH")
        )
        ph_chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("date", axis=alt.Axis(title="Måneder", grid=True)),
                y=alt.Y(
                    "pH",
                    axis=alt.Axis(title="Innsjø pH (-)"),
                    scale=alt.Scale(zero=False),
                ),
                color="product",
                opacity=alt.condition(checkbox_selection, alt.value(1), alt.value(0)),
                tooltip=["product", "date", alt.Tooltip("pH", format=",.2f")],
            )
            .add_params(checkbox_selection)
            .properties(width=600, height=200)
            .interactive()
        )
        ca_chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X(
                    "date",
                    axis=alt.Axis(title=" ", grid=True),
                ),
                y=alt.Y(
                    "Ca (mg/l)",
                    axis=alt.Axis(title="Ca\u2091\u2096\u1D65 (mg/l)"),
                    # scale=alt.Scale(zero=False),
                ),
                color="product",
                opacity=alt.condition(checkbox_selection, alt.value(1), alt.value(0)),
                tooltip=[
                    "product",
                    "date",
                    alt.Tooltip("Ca (mg/l)", format=",.2f"),
                ],
            )
            .add_params(checkbox_selection)
            .properties(width=600, height=200)
            .interactive()
        )
        chart = alt.vconcat(ca_chart, ph_chart + init_lake_ph + inflow_ph)
        st.altair_chart(chart, use_container_width=True)

        return chart