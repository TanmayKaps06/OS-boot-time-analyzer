"""Read boot information exposed by normal macOS utilities.

This module only reads public system state. It does not change services,
login items, or system configuration.
"""
from __future__ import annotations

import platform
import re
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

from .models import BootSnapshot

BOOT_TIME_PATTERN = re.compile(r"sec\s*=\s*(\d+)")
LOG_TIMESTAMP_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
)


def _run(command: list[str], timeout: int = 10) -> Optional[str]:
    try:
        result = subprocess.run(
            command, text=True, capture_output=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def get_boot_time() -> Optional[datetime]:
    """Return the kernel boot timestamp, or None outside macOS/unavailable."""
    if platform.system() != "Darwin":
        return None
    output = _run(["sysctl", "-n", "kern.boottime"])
    match = BOOT_TIME_PATTERN.search(output or "")
    if not match:
        return None
    return datetime.fromtimestamp(int(match.group(1)), tz=timezone.utc).astimezone()


def get_login_window_seconds(boot_time: datetime) -> tuple[Optional[float], str]:
    """Find the first logged loginwindow event after boot, when retained.

    This is deliberately conservative: launch of loginwindow is only a useful
    login-screen indicator, not proof of the instant a display became usable.
    """
    if platform.system() != "Darwin":
        return None, "Unavailable: this collector runs on macOS only."

    end = boot_time + timedelta(hours=2)
    start_text = boot_time.strftime("%Y-%m-%d %H:%M:%S")
    end_text = end.strftime("%Y-%m-%d %H:%M:%S")
    output = _run(
        [
            "log", "show", "--style", "syslog", "--start", start_text,
            "--end", end_text, "--predicate", 'process == "loginwindow"',
            "--info",
        ],
        timeout=15,
    )
    if not output:
        return None, "Unavailable: no retained login-window event was found."

    for line in output.splitlines():
        match = LOG_TIMESTAMP_PATTERN.match(line)
        if not match:
            continue
        try:
            event_time = datetime.fromisoformat(match.group(1)).astimezone()
        except ValueError:
            continue
        seconds = (event_time - boot_time).total_seconds()
        if 0 <= seconds <= 2 * 60 * 60:
            return round(seconds, 1), "Observed from the first retained loginwindow log event."
    return None, "Unavailable: login-window logs could not be read or parsed."


def parse_launchctl_list(output: str) -> pd.DataFrame:
    """Parse active launchd jobs from ``launchctl list`` output.

    The PID column is ``-`` for a job that is loaded but is not currently
    running. Such jobs are excluded: the returned list is intentionally a
    snapshot of active jobs, not every configured startup job.
    """
    services: list[dict[str, object]] = []
    for line in output.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) != 3 or parts[0] == "PID":
            continue
        pid_text, status, label = parts
        if not pid_text.isdigit():
            continue
        services.append(
            {"Service label": label, "Process ID": int(pid_text), "Status": status}
        )
    return pd.DataFrame(services, columns=["Service label", "Process ID", "Status"])


def get_active_background_services() -> tuple[pd.DataFrame, str]:
    """Return currently running launchd jobs in the signed-in user's domain."""
    empty = pd.DataFrame(columns=["Service label", "Process ID", "Status"])
    if platform.system() != "Darwin":
        return empty, "Unavailable: background-service collection runs on macOS only."

    output = _run(["launchctl", "list"])
    if output is None:
        return empty, "Unavailable: macOS did not allow launch service information to be read."
    services = parse_launchctl_list(output)
    return services, (
        "This is a current snapshot of running launchd jobs in your signed-in "
        "user session. It does not identify which service affected boot speed."
    )


def collect_snapshot() -> BootSnapshot:
    now = datetime.now().astimezone()
    boot_time = get_boot_time()
    if boot_time is None:
        return BootSnapshot(
            boot_time=None,
            observed_at=now,
            uptime_seconds=None,
            login_window_seconds=None,
            login_window_note="Unavailable: kernel boot time could not be read.",
            collection_note="No boot record was measured on this platform.",
        )
    uptime = max(0.0, (now - boot_time).total_seconds())
    login_seconds, login_note = get_login_window_seconds(boot_time)
    return BootSnapshot(
        boot_time=boot_time,
        observed_at=now,
        uptime_seconds=round(uptime, 1),
        login_window_seconds=login_seconds,
        login_window_note=login_note,
    )
