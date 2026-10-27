"""Data-quality checks run on Silver before Gold metrics are calculated.

Severity:
  error   - offending incidents are excluded from Gold; the run exits 1
  warning - reported for review; metrics are still calculated
"""
from __future__ import annotations

import pandas as pd

DETECTION_LAG_LIMIT = pd.Timedelta(days=7)
MIN_BUILD_LINKAGE_RATE = 0.80


def _result(check, severity, checked, failed_ids):
    failed = len(failed_ids)
    return {
        "check": check,
        "severity": severity,
        "rows_checked": int(checked),
        "rows_failed": failed,
        "status": "PASS" if failed == 0 else "FAIL",
        "failing_ids": ";".join(str(i) for i in failed_ids),
    }


def check_incident_timeline(incidents):
    """DQ1 (error): resolution cannot precede the start or the engineering report."""
    started = incidents["incident_started_datetime"]
    reported_eng = incidents["incident_reported_engineering_datetime"]
    resolved = incidents["incident_resolved_datetime"]
    bad = incidents[(resolved < started) | (resolved < reported_eng)]
    ids = bad["workitem_id"].tolist()
    return _result("DQ1_incident_timeline_order", "error", len(incidents), ids), set(ids)


def check_build_linkage(builds, commits):
    """DQ2 (warning): most builds should have at least one commit linked by build_sk."""
    linked = builds["build_id"].isin(commits["build_sk"].dropna().unique())
    rate = float(linked.mean()) if len(builds) else 0.0
    row = {
        "check": "DQ2_build_commit_linkage",
        "severity": "warning",
        "rows_checked": len(builds),
        "rows_failed": int((~linked).sum()),
        "status": "PASS" if rate >= MIN_BUILD_LINKAGE_RATE else "FAIL",
        "failing_ids": f"linkage_rate={rate:.1%}",
    }
    return row, set()


def check_detection_lag(incidents):
    """DQ3 (warning): a customer-support report more than 7 days after start suggests a detection gap."""
    lag = incidents["incident_reported_customersupport_datetime"] - incidents["incident_started_datetime"]
    bad = incidents[lag > DETECTION_LAG_LIMIT]
    result = _result("DQ3_detection_lag_within_7d", "warning", len(incidents), bad["workitem_id"].tolist())
    return result, set()


def run_checks(silver):
    rows, excluded = [], set()
    r1, bad_ids = check_incident_timeline(silver["incidents"])
    rows.append(r1)
    excluded |= bad_ids
    r2, _ = check_build_linkage(silver["builds"], silver["commits"])
    rows.append(r2)
    r3, _ = check_detection_lag(silver["incidents"])
    rows.append(r3)
    return pd.DataFrame(rows), excluded