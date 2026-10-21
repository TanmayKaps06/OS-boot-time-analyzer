"""Plain-language recommendations based only on observed information."""
from __future__ import annotations

import pandas as pd


def make_recommendations(history: pd.DataFrame) -> list[str]:
    values = history["login_window_seconds"].dropna() if not history.empty else pd.Series(dtype=float)
    if values.empty:
        return [
            "No login-screen timing is available yet. macOS may have discarded the relevant log event, especially if collection began after startup.",
            "If startup feels slow, review Login Items in System Settings and close apps you do not need to open automatically. This app will not change them for you.",
        ]

    suggestions: list[str] = []
    latest = float(values.iloc[-1])
    if latest >= 90:
        suggestions.append("This startup took over 90 seconds to reach the observed login-window event. Review unnecessary Login Items and background apps in System Settings.")
    elif latest >= 45:
        suggestions.append("This startup was moderately slow. If it happens repeatedly, review Login Items and recently added background apps.")
    else:
        suggestions.append("The observed login-window timing looks reasonably quick. Keep an eye on the history for a consistent slowdown.")

    if len(values) >= 2:
        change = latest - float(values.iloc[-2])
        if change > 10:
            suggestions.append("The latest observed startup is more than 10 seconds slower than the previous one. A recent app, login item, or update may be worth reviewing.")
        elif change < -10:
            suggestions.append("The latest observed startup is more than 10 seconds faster than the previous one.")
    return suggestions
