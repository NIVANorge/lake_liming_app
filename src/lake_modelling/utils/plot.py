import streamlit as st
import altair as alt


def plot_result(result, x_title, y_title):
    st.markdown("## Result")
    chart = alt.Chart(result).mark_line().encode(x=x_title, y=y_title)
    st.altair_chart(chart, use_container_width=True)

    return None
