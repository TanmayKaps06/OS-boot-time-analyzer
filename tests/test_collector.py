from boot_analyzer.collector import parse_launchctl_list


def test_only_running_launchd_jobs_are_parsed():
    output = """PID\tStatus\tLabel
-\t0\tcom.apple.inactive-job
241\t0\tcom.example.running-job
533\t78\tcom.example.other-running-job
"""

    services = parse_launchctl_list(output)

    assert list(services["Service label"]) == [
        "com.example.running-job",
        "com.example.other-running-job",
    ]
    assert list(services["Process ID"]) == [241, 533]
