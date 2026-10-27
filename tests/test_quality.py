import pandas as pd

from quality import check_detection_lag, check_incident_timeline


def _incident(workitem_id, started, reported_cs, reported_eng, resolved):
    return pd.DataFrame([{
        "workitem_id": workitem_id,
        "incident_started_datetime": pd.Timestamp(started),
        "incident_reported_customersupport_datetime": pd.Timestamp(reported_cs),
        "incident_reported_engineering_datetime": pd.Timestamp(reported_eng),
        "incident_resolved_datetime": pd.Timestamp(resolved),
    }])


def test_resolved_before_engineering_report_is_flagged():
    # Mirrors incident 1004 in the supplied data.
    df = _incident(1004, "2024-05-05 22:00", "2024-05-06 06:17", "2024-05-06 06:17", "2024-05-06 05:47")
    result, excluded = check_incident_timeline(df)
    assert result["status"] == "FAIL"
    assert excluded == {1004}


def test_valid_timeline_passes():
    df = _incident(1, "2024-08-21 08:40", "2024-08-21 09:00", "2024-08-21 09:12", "2024-08-21 10:42")
    result, excluded = check_incident_timeline(df)
    assert result["status"] == "PASS"
    assert excluded == set()


def test_detection_lag_over_seven_days_is_flagged():
    # Mirrors incident 1011 (reported 14 days after it started).
    df = _incident(1011, "2024-11-05 03:00", "2024-11-19 03:00", "2024-11-19 03:00", "2024-11-21 13:30")
    result, _ = check_detection_lag(df)
    assert result["status"] == "FAIL"
    assert result["failing_ids"] == "1011"