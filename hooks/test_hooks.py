import pytest


def pytest_runtest_logreport(report):
    if report.when == "call" and report.failed:
        print(f"\n[FAILED] {report.nodeid}")


def pytest_sessionfinish(session, exitstatus):
    passed = session.testscollected - session.testsfailed
    print(f"\n--- Results: {passed} passed, {session.testsfailed} failed ---")
