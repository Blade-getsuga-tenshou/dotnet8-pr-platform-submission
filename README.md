# dotnet8-pr-platform

Final submission: tag v1.0.0, commit 0b742eb

Case study submission for a Head of DevOps and Analytics assessment.

- Part A (platform engineering): a GitHub Actions PR validation platform for a .NET 8 solution, converted from a supplied Azure DevOps pipeline.
- Part B (data engineering): a DORA metrics pipeline with three data-quality checks, implemented in Microsoft Fabric and as a local Python reference.
- Parts C and D are documented in docs/ as PDFs.

## Links

- Dashboard (GitHub Pages): https://blade-getsuga-tenshou.github.io/dotnet8-pr-platform-submission/dashboard.html
- Data engineering: docs/data-engineering.md
- AI Use Statement: docs/ai-use-statement.md
- Governance and security: docs/governance.md, docs/security.md
- Migration mapping: docs/migration.md
- Validation and rollback: docs/validation-and-rollback.md

## Prerequisites

- .NET 8 SDK
- Python 3.12
- Git
- GitHub CLI (gh), optional

## Part A: PR validation

- Trigger: pull_request into main for opened, synchronize, reopened, and ready_for_review. Draft PRs are skipped.
- .github/workflows/pr-validation.yml is the caller. It runs the reusable workflow, the Python tests, and the x86 job.
- .github/workflows/dotnet-build-test.yml is the reusable workflow (workflow_call). It restores, builds, runs tests with XPlat coverage, publishes src/Core, and uploads test-results and build-output, kept 14 days.
- Required checks on main: validate / Build, test, and collect coverage, and Python tests (pytest). A PR cannot merge until both pass.
- Non-required job: x86 build and test (legacy target). It builds and tests the sample for x86 on a hosted runner. It is not a required check.
- All actions are pinned to commit SHAs.
- Remaining limit: legacy products that depend on 32-bit-only components (for example certain COM objects, drivers, or native libraries) still need a real 32-bit environment. See docs/migration.md and docs/governance.md.

## Part B: DORA metrics

Two implementations use the same rules and produce identical Gold results.

1. Microsoft Fabric. Lakehouse dora_lakehouse in workspace dotnet8-dora-fabric, on a paid F2 capacity. Bronze, Silver, and Gold are Delta tables. The notebook code is in fabric/bronze_silver_gold.py.
2. Local Python. pipeline/run_pipeline.py writes Bronze, Silver, and Gold as CSV files in data/output, runs the data-quality checks, and exits with code 1 if an error-level check fails.

Why both: a Fabric trial could not start for the personal account ("Fabric trial isn't available for your account"). Azure also rejects personal accounts for capacity creation. A native member account was created in the tenant that owns the subscription, and a paid F2 capacity was assigned to the workspace. The local pipeline is the tested reference.

Results on the supplied data (synthetic):

| Metric | Value | Basis |
|---|---|---|
| Deployment frequency | 2.17 per day | 350 builds over 161 days |
| Lead time for changes (median) | 2.38 hours | Partial: 52 of 350 builds have a linked commit (14.9%) |
| Change failure rate | 0.86% | 3 of 350 deployments, from 10 included incidents |
| Time to restore (median) | 2.03 hours | Primary figure: 10 included incidents |
| Time to restore (mean) | 43.64 hours | Pulled up by incident 1011, reported 14 days after it started |

Data-quality checks:

- DQ1 (error): incident 1004 is resolved before it was reported. It is excluded from Gold and the run exits with code 1.
- DQ2 (warning): 14.9% of builds have a linked commit, against an 80% threshold. Fails. Metrics are still calculated and lead time is labelled as partial.
- DQ3 (warning): incident 1011 was reported 14 days after it started. Fails.
- Unit tests cover DQ1, DQ2, and DQ3 in tests/.

Dashboard: the delivered view is the HTML dashboard on GitHub Pages, generated from the local Gold outputs. A Power BI report is in docs/dora-metrics.pbix, with a screenshot in docs/powerbi-dashboard.png.

## Running the code

Local, from the repo root with the virtual environment active:

    pip install -r requirements.txt
    python pipeline/run_pipeline.py
    python pipeline/build_dashboard.py
    pytest

Fabric: upload data/source/dora_metrics.xlsx to the lakehouse Files folder, then run the notebook cells in fabric/bronze_silver_gold.py in order.

The source workbook is not in the repo. Place it at data/source/dora_metrics.xlsx. It is gitignored because it contains author email addresses.

## Known limitations

- Lead time covers 52 of 350 builds. It is not the team's full lead time until commit linkage improves.
- Change failure rate and time to restore rest on 10 incidents and are not statistically reliable.
- The source has no production-deployment flag, so all completed builds are treated as deployments.
- Legacy products with 32-bit-only dependencies are not covered by the sample.
- Solo-repo settings: required approvals are 0 and admins can bypass protection. Enterprise settings are in docs/governance.md.
- All data is synthetic.

## Pull request history

| PR | Change | Result |
|---|---|---|
| #1 | Baseline PR validation workflow | Merged |
| #2 | Actions pinned to commit SHAs | Merged |
| #3 | Reusable workflow and build artifacts | Merged |
| #4 | Docs: security, governance, migration, validation | Merged |
| #5 | DORA pipeline, data-quality checks, pytest job | Merged |
| #6 | Baseline DORA dashboard | Merged |
| #7 | Part B README and AI Use Statement | Merged |
| #8 | Fabric Bronze, Silver, and Gold code | Merged |
| #9 | Mean time to restore | Merged |
| #10 | DQ2 unit tests | Merged |
| #11 | Sync docs and Fabric code | Merged |
| #12 | Power BI report and screenshot | Merged |
| #14 | Non-required x86 build and test job | Merged |
