# AI Use Statement

## Tools used

- Claude (chat interface), Anthropic. Used for planning, drafting code and documents, and troubleshooting.

## Where AI contributed significantly

- Scaffolding: the .NET solution layout and the first GitHub Actions workflow conversion from the supplied Azure pipeline.
- Workflow design: the reusable workflow and the decision to pin actions to commit SHAs.
- Pipeline code: the Bronze, Silver, and Gold transformations, the data-quality checks, the dashboard generator, and the Fabric notebook cells.
- Documentation drafts: README, security, governance, migration, validation and rollback, and data-engineering docs.

## Where I made the decisions

- Runner choice: hosted x64 runners, with x86 documented as a legacy limitation.
- Required checks, approval count (0 for a solo repo), and admin-bypass setting.
- The data-quality thresholds, including the 80% linkage threshold and the 7-day detection limit. These were not changed to make checks pass.
- The metric assumptions A1 to A5 in docs/data-engineering.md.
- The decision to report both median and mean time to restore, with the median as the headline figure.
- The decision to run Part B both in Fabric (after the trial was blocked and a paid F2 capacity was used) and locally as the tested reference.

## How I validated AI output

- Every PR passed the required checks before merge. PR #1 predates branch protection.
- Ran the pytest suite (five tests) locally and in CI.
- Recounted commit-to-build links from the source workbook. This found that the first de-duplication dropped 12 links; it was corrected to use commit_id together with build_sk.
- Confirmed the Fabric Bronze row counts (164, 350, 11, 2) and the Silver counts match the local pipeline.
- Compared the Fabric Gold summary with the local pipeline output. All metrics match, including the mean time to restore.
- Checked the generated dashboard and the notebook code for personal data before committing.

## Errors the AI made that were caught

- Suggested that the Azure free account would allow a Fabric capacity. It does not for a personal account.
- Reported a 40-versus-52 linkage discrepancy before it was reconciled.
- Claimed the test file was written when it was not. Caught when the tests folder was checked.
- Hardcoded an incident ID in the Fabric Gold filter. Replaced with a rule-driven DQ1 exclusion.
- A nested code block in a generated document broke a PowerShell paste. Fixed by writing files in smaller steps.

## Note

This statement describes how the work was done. The content of the submission, including all code, metrics, and recommendations, is my responsibility, and I can explain and defend each part.