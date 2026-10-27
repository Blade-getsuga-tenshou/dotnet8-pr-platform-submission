"""DORA metrics pipeline: Bronze -> Silver -> Gold with data-quality gates.

Local implementation of the Microsoft Fabric design (Bronze, Silver, Gold).
Run from the repo root:  python pipeline/run_pipeline.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from quality import run_checks

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source" / "dora_metrics.xlsx"
OUT = ROOT / "data" / "output"

KEYS = {"commits": "commit_id", "builds": "build_id", "incidents": "workitem_id"}
DATETIME_COLUMNS = {
    "commits": ["author_date", "committer_date", "ingestion_datetime"],
    "builds": ["pipeline_start_time", "pipeline_end_time", "ingestion_datetime"],
    "incidents": [
        "incident_started_datetime",
        "incident_reported_customersupport_datetime",
        "incident_reported_engineering_datetime",
        "investigation_started_datetime",
        "incident_resolved_datetime",
        "ingestion_datetime",
    ],
}


def bronze(sheets):
    """Raw copy of each sheet plus lineage columns. No business rules."""
    loaded_at = datetime.now(timezone.utc).isoformat()
    tables = {}
    for name, df in sheets.items():
        t = df.copy()
        t["_source_file"] = SOURCE.name
        t["_source_sheet"] = name
        t["_loaded_at_utc"] = loaded_at
        tables[name] = t
    return tables


def silver(bronze_tables):
    """Typed, de-duplicated tables keyed on the source primary keys."""
    tables = {}
    for name in ("commits", "builds", "incidents"):
        key = ["commit_id", "build_sk"] if name == "commits" else KEYS[name]
        df = bronze_tables[name].drop_duplicates(key, keep="last").copy()
        for col in DATETIME_COLUMNS[name]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        tables[name] = df
    tables["commits"]["build_sk"] = pd.to_numeric(tables["commits"]["build_sk"], errors="coerce")
    tables["builds"]["build_id"] = pd.to_numeric(tables["builds"]["build_id"], errors="coerce")
    tables["incidents"]["caused_by_deployment"] = (
        pd.to_numeric(tables["incidents"]["caused_by_deployment"], errors="coerce").fillna(0).astype(int)
    )
    tables["projects"] = bronze_tables["projects"].drop_duplicates("project_id", keep="last").copy()
    return tables


def gold(silver_tables, excluded_incident_ids):
    """DORA metrics. Assumptions A1 and A2 are listed in the data-engineering doc."""
    commits = silver_tables["commits"]
    builds = silver_tables["builds"].dropna(subset=["pipeline_end_time"]).copy()
    incidents = silver_tables["incidents"]
    incidents = incidents[~incidents["workitem_id"].isin(list(excluded_incident_ids))].copy()

    # A1: every completed build counts as a deployment (the sheet has no result field).
    # A2: lead time runs from the earliest committer_date of commits linked to the build.
    first_commit = (
        commits.dropna(subset=["build_sk"]).groupby("build_sk")["committer_date"].min()
        .rename("first_commit_time")
    )
    builds = builds.merge(first_commit, left_on="build_id", right_index=True, how="left")
    builds["lead_time_hours"] = (
        (builds["pipeline_end_time"] - builds["first_commit_time"]).dt.total_seconds() / 3600
    )
    negative_lead = int((builds["lead_time_hours"] < 0).sum())
    builds.loc[builds["lead_time_hours"] < 0, "lead_time_hours"] = float("nan")

    builds["week"] = builds["pipeline_end_time"].dt.to_period("W-SUN").dt.start_time
    incidents["week"] = incidents["incident_started_datetime"].dt.to_period("W-SUN").dt.start_time
    incidents["time_to_restore_hours"] = (
        (incidents["incident_resolved_datetime"] - incidents["incident_started_datetime"]).dt.total_seconds() / 3600
    )

    dep_weekly = builds.groupby("week").agg(
        deployments=("build_id", "count"),
        median_lead_time_hours=("lead_time_hours", "median"),
    )
    inc_weekly = incidents.groupby("week").agg(
        incidents=("workitem_id", "count"),
        caused_by_deployment=("caused_by_deployment", "sum"),
    )
    weekly = dep_weekly.join(inc_weekly, how="outer").fillna(
        {"deployments": 0, "incidents": 0, "caused_by_deployment": 0}
    ).sort_index()
    weekly["change_failure_rate"] = (
        weekly["caused_by_deployment"] / weekly["deployments"]
    ).where(weekly["deployments"] > 0)

    window_days = (
        builds["pipeline_end_time"].max().normalize() - builds["pipeline_end_time"].min().normalize()
    ).days + 1
    summary = {
        "deployment_frequency_per_day": len(builds) / window_days,
        "median_lead_time_hours": builds["lead_time_hours"].median(),
        "change_failure_rate": incidents["caused_by_deployment"].sum() / len(builds),
        "median_time_to_restore_hours": incidents["time_to_restore_hours"].median(),
        "mean_time_to_restore_hours": incidents["time_to_restore_hours"].mean(),
        "deployments_counted": len(builds),
        "incidents_included": len(incidents),
        "incidents_quarantined": len(excluded_incident_ids),
        "lead_time_negative_excluded": negative_lead,
        "window_days": window_days,
    }
    return weekly, summary


def main():
    if not SOURCE.exists():
        sys.exit(f"Missing source file: {SOURCE}. Copy the case study Excel there first.")
    OUT.mkdir(parents=True, exist_ok=True)

    sheets = pd.read_excel(SOURCE, sheet_name=None, engine="openpyxl")
    b = bronze(sheets)
    s = silver(b)
    dq, excluded = run_checks(s)
    weekly, summary = gold(s, excluded)

    for layer, tables in (("bronze", b), ("silver", s)):
        folder = OUT / layer
        folder.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            df.to_csv(folder / f"{name}.csv", index=False)

    gold_dir = OUT / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(gold_dir / "dora_weekly.csv")
    pd.Series(summary).to_frame("value").to_csv(gold_dir / "dora_summary.csv")
    dq.to_csv(OUT / "dq_report.csv", index=False)

    print(dq.to_string(index=False))
    print()
    print(pd.Series(summary).to_string())

    failed_errors = dq[(dq["severity"] == "error") & (dq["status"] == "FAIL")]
    return 1 if len(failed_errors) else 0


if __name__ == "__main__":
    sys.exit(main())