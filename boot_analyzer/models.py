from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BootSnapshot:
    """Information collected for one OS boot session.

    ``login_window_seconds`` is only set when unified logs contain an
    observable loginwindow event.  It is an indicator, not a power-button
    measurement.
    """

    boot_time: Optional[datetime]
    observed_at: datetime
    uptime_seconds: Optional[float]
    login_window_seconds: Optional[float]
    login_window_note: str
    collection_note: str = ""
