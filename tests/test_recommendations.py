import pandas as pd

from boot_analyzer.recommendations import make_recommendations


def test_missing_measurements_are_explained():
    history = pd.DataFrame({"login_window_seconds": [None]})
    result = make_recommendations(history)
    assert "No login-screen timing" in result[0]


def test_slow_latest_boot_is_flagged():
    history = pd.DataFrame({"login_window_seconds": [50.0, 95.0]})
    result = make_recommendations(history)
    assert "over 90 seconds" in result[0]
    assert "slower" in result[1]
