# Mac Boot Time Analyzer

A beginner-friendly Streamlit dashboard that saves the startup information macOS makes available for each boot.

## What it measures

- **Last boot time** comes from `sysctl kern.boottime`.
- **Mac uptime** is the elapsed time since that kernel boot timestamp. It is shown for context and is **not** a boot-duration measurement.
- **Observed time to login window** is calculated only when unified logs contain a `loginwindow` event. It measures from kernel boot to that logged event, so it is a helpful login-screen indicator—not a claimed power-button-to-screen time.
- **Active background services** is a live count of currently running `launchd` jobs in the signed-in user's session. The expandable list shows their labels and process IDs. It is a current snapshot, not evidence that a listed service delayed startup.

When a log event is missing or cannot be read, the dashboard shows **Unavailable**. It never fills in an estimate. macOS can discard old log events, so starting the app long after boot can mean that this value is unavailable.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The SQLite database is created at `data/boot_history.sqlite3`. A boot is stored once, using the kernel boot timestamp as its unique key, so opening the dashboard repeatedly does not create duplicates.

## Permissions and safety

The app invokes read-only macOS tools (`sysctl` and `log show`) under the current user. It does not modify Login Items, background services, system settings, or system files.

## Project structure

```
app.py                       Streamlit dashboard
boot_analyzer/collector.py   macOS data collection
boot_analyzer/database.py    SQLite storage
boot_analyzer/recommendations.py
```
