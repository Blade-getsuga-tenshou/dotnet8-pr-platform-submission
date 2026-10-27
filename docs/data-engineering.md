# Data engineering: DORA metrics

## Scope

Part B of the case study. The brief asks for a Microsoft Fabric solution with Bronze, Silver, and Gold layers, a baseline dashboard, metric definitions, and three executable data-quality checks.

The Fabric solution is implemented in a Fabric lakehouse on a paid F2 capacity. A local Python implementation applies the same rules and is the tested reference. Both produce identical Gold results.

## Implementation status

| Component | Local Python | Microsoft Fabric |
|---|---|---|
| Bronze (raw copy with lineage columns) | Implemented: CSV in data/output/bronze | Implemented: Delta tables bronze_commits, bronze_builds, bronze_incidents, bronze_projects |
| Silver (typed, de-duplicated, DQ checks) | Implemented: CSV in data/output/silver | Implemented: Delta tables silver_commits, silver_builds, silver_incidents |
| Gold (weekly and summary metrics) | Implemented: dora_weekly.csv, dora_summary.csv | Implemented: Delta table gold_dora_weekly and printed summary |
| Data-quality checks DQ1 to DQ3 | Implemented, with unit tests | Implemented in the Silver and Gold cells |
| Dashboard | HTML on GitHub Pages | Not built |
| Power BI report | Not built | Not built |
| Semantic model | Not built | Not built |
| Fabric Dataflow Gen2 | Not applicable | Not built |

## Source

One Excel workbook supplied with the case study. The data is synthetic.

| Sheet | Rows | Content |
|---|---|---|
| commits | 164 | Commit author, committer, build link (build_sk) |
| builds | 350 | Completed pipeline runs with start and end times |
| incidents | 11 | Outages with start, report, investigation, and resolution times |
| projects | 2 | Project lookup |

## Layers

Bronze keeps every value as received, as text, with three lineage columns: _source_file, _source_sheet, and _loaded_at_utc. It applies no business rules. Values are typed in Silver.

Silver converts types and removes duplicates on these keys:

- commits: commit_id together with build_sk. A commit can belong to more than one build. In the source, 56 commits are linked to more than one build, so commit_id alone would drop real links. The first version of this pipeline used commit_id alone and lost 12 build links; the fix is recorded here.
- builds: build_id
- incidents: workitem_id

The data-quality checks run on Silver.

Gold produces a weekly table and a summary. Incidents that fail DQ1 are excluded by rule, not by a hardcoded ID.

## Data-quality checks

DQ1, incident timeline order (error). Fails when an incident is resolved before it started or before engineering was notified. Failing incidents are excluded from Gold. Current result: incident 1004 fails. The run exits with code 1.

DQ2, build-to-commit linkage (warning). At least 80% of builds must have one or more linked commits. Current result: 14.9% (52 of 350 builds). The check fails. Metrics are still calculated, and lead time is labelled as partial.

DQ3, detection lag (warning). Fails when the customer-support report is more than 7 days after the incident started. Current result: incident 1011 fails (reported 14 days after start).

Unit tests in tests/ cover DQ1 (failing and passing cases, including the incident 1004 pattern), DQ2 (below and above 80%), and DQ3 (the incident 1011 pattern).

## Metric definitions

| Metric | Formula | Grain | Source | Current value |
|---|---|---|---|---|
| Deployment frequency | Completed builds divided by window days | Summary and weekly | builds | 2.17 per day (350 builds over 161 days) |
| Lead time for changes | Median of (build end time minus earliest committer date of linked commits), in hours | Summary and weekly | builds, commits | 2.38 hours, from 52 builds with a linked commit (14.9% coverage) |
| Change failure rate | Included incidents with caused_by_deployment = 1, divided by deployments | Summary | incidents, builds | 0.86% (3 of 350) |
| Time to restore, median | Median of (resolved time minus started time), in hours, over included incidents | Summary | incidents | 2.03 hours over 10 incidents |
| Time to restore, mean | Mean of the same durations | Summary | incidents | 43.64 hours |

The brief names Mean Time to Restore. Both figures are reported. The median is the headline figure, because one long outage dominates the mean. Incident 1011 was reported 14 days after it started, and assumption A3 counts that gap as restore time.

## Assumptions

A1. Every completed build is counted as a deployment. The workbook has no field showing whether a build was a production deployment.

A2. Lead time starts from the earliest committer date of the commits linked to a build. Author date is not used. Builds with negative lead time are excluded. One build is excluded for this reason.

A3. Time to restore starts at the incident start time, not the report time, so detection delay is included in restore time.

A4. Weeks run Monday to Sunday.

A5. The measurement window runs from the first to the last completed build, inclusive: 161 days.

## Limitations

- Eleven incidents exist, and one is excluded by DQ1. Change failure rate and time to restore are not statistically reliable.
- Lead time covers 52 of 350 builds. It is not the team's full lead time until linkage improves.
- There is no production flag, so all completed builds count as deployments.
- The data covers one 161-day window.
- The source data is synthetic.

## Ownership (proposed, not agreed)

- Metric definitions: Head of DevOps
- Pipeline code and checks: Platform engineering
- Source extracts (commits, builds, incidents): the team that owns each Azure DevOps organization

## Fabric notes

The Fabric lakehouse is dora_lakehouse in workspace dotnet8-dora-fabric. The workspace is assigned to capacity fabricdora001 (F2, Central India). The capacity is suspended between sessions to limit cost.

The Fabric trial could not start for the personal account, so a paid F2 capacity was used instead. The Azure portal also rejected personal accounts for capacity creation.

## How to run

Local, from the repo root with the virtual environment active:

    pip install -r requirements.txt
    python pipeline/run_pipeline.py
    python pipeline/build_dashboard.py
    pytest

Outputs are written to data/output.