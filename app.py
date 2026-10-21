from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from boot_analyzer.collector import collect_snapshot
from boot_analyzer.database import load_history, save_snapshot
from boot_analyzer.recommendations import make_recommendations

DATABASE_PATH = Path(__file__).parent / "data" / "boot_history.sqlite3"

st.set_page_config(page_title="Mac Boot Time Analyzer", page_icon="⏱️", layout="centered")


def display_seconds(value: float | None) -> str:
    return "Unavailable" if value is None or pd.isna(value) else f"{value:.1f} seconds"


def latest_comparison(history: pd.DataFrame) -> str:
    values = history["login_window_seconds"].dropna()
    if len(values) < 2:
        return "Record another boot to compare startup performance."
    difference = float(values.iloc[-1] - values.iloc[-2])
    if abs(difference) < 1:
        return "About the same as the previous recorded startup."
    direction = "faster" if difference < 0 else "slower"
    return f"{abs(difference):.1f} seconds {direction} than the previous recorded startup."


@st.cache_data(ttl=30, show_spinner=False)
def collect_once_for_view() -> object:
    return collect_snapshot()


snapshot = collect_once_for_view()
save_snapshot(DATABASE_PATH, snapshot)
history = load_history(DATABASE_PATH)

st.title("Mac Boot Time Analyzer")
st.caption("A simple record of available macOS startup information.")

st.subheader("Overview")
if snapshot.boot_time is None:
    st.write("**Last boot:** Unavailable")
else:
    st.write(f"**Last boot:** {snapshot.boot_time.strftime('%b %d, %Y at %I:%M %p %Z')}")
st.metric("Mac uptime", display_seconds(snapshot.uptime_seconds), help="Time since the kernel booted. This is not the startup duration.")
st.metric(
    "Observed time to login window", display_seconds(snapshot.login_window_seconds),
    help="Measured from kernel boot to the first retained loginwindow log event. It is an indicator, not a power-button-to-screen measurement.",
)
st.caption(snapshot.login_window_note)
if snapshot.collection_note:
    st.info(snapshot.collection_note)
st.info("Values marked unavailable are not estimated. Some boot events may no longer be in the macOS logs when this app starts.")

st.subheader("Boot history")
st.write(latest_comparison(history))
chart_data = history.dropna(subset=["login_window_seconds"]).copy()
if chart_data.empty:
    st.caption("No comparable login-window timings have been recorded yet.")
else:
    figure = px.line(
        chart_data, x="boot_time", y="login_window_seconds", markers=True,
        labels={"boot_time": "Boot date", "login_window_seconds": "Seconds to observed login window"},
    )
    figure.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(figure, use_container_width=True)

if history.empty:
    st.caption("No boot records saved yet.")
else:
    table = history[["boot_time", "login_window_seconds"]].copy()
    table.columns = ["Boot date", "Observed login window (seconds)"]
    st.dataframe(table.sort_values("Boot date", ascending=False), hide_index=True, use_container_width=True)

st.subheader("Recommendations")
for recommendation in make_recommendations(history):
    st.write(f"• {recommendation}")
