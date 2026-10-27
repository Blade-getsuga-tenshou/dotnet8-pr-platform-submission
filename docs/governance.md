# Governance

## Required status checks

The required check name must match the job name GitHub displays. Two mismatches happened during setup:

1. The first rule used "PR Validation / Build, test, and collect coverage (pull_request)", which is how gh pr checks displays the check. The API reports only the job name, so the rule never matched and PR #2 stayed blocked.
2. After the build moved into a reusable workflow, the name changed to "validate / Build, test, and collect coverage", because the caller's job ID is prefixed. PR #3 needed a rule update before it could merge.

A mismatch does not fail loudly. The PR is simply blocked. Enterprise teams should use a stable job name, or manage required checks through a central ruleset, so a refactor does not silently block every PR.

## Approval policy

| Setting | Solo sample (this repo) | Enterprise recommendation |
|---|---|---|
| Required approvals | 0 | At least 1, with CODEOWNERS |
| Required status checks | Build and test; Python tests | Build and test; Python tests; stable names |
| Admin bypass | Allowed | Disabled, with audited exceptions |
| Force push and deletion on main | Blocked | Blocked |

## Legacy constraint: x86 builds

The sample builds and tests for x64 (default job) and for x86 (the "x86 build and test (legacy target)" job). Both run on GitHub-hosted Windows runners. The x86 job is not a required check, so it reports evidence without changing branch protection. This shows the pipeline pattern works for x86. It does not prove that a real legacy product builds, because the sample has no 32-bit-only dependencies.

Remaining limit: legacy products that depend on 32-bit-only components (for example certain COM objects, drivers, or native libraries) still need a real 32-bit environment.

Enterprise path: legacy products with 32-bit-only dependencies run on self-hosted Windows runners, labelled (for example, legacy-x86) and kept separate from the general runner pool. Each of those runners needs an owner, patching, and a decision on when it can be retired.

## Decision log

| Decision | Reason | Revisit when |
|---|---|---|
| Hosted x64 runners for the default job, x86 job non-required | Free for public repos; the x86 job shows the pattern works on a standard runner | Legacy products with 32-bit-only dependencies need CI |
| Reusable workflow for the build | Other repos can call the same pattern | More than one .NET solution exists |
| Required checks on main | Prevents merges without passing validation | Never; this is a baseline control |
| Approvals set to 0 | Solo owner cannot self-approve | A second reviewer joins |
| Actions pinned to SHAs | Stops silent changes from a tag move | Dependabot is enabled |