# Validation and rollback

## Validating a change

1. Open a PR into main. The required check "validate / Build, test, and collect coverage" runs automatically.
2. Confirm the check passes with gh pr checks <number>.
3. Download test-results and build-output from the run's Artifacts section to confirm coverage and publish output were produced.
4. Locally, run dotnet test DotNet8PrPlatform.sln before pushing, to catch failures earlier.

## Rolling back a bad workflow change

Workflow changes take effect on the PR branch itself. A broken workflow fails only its own PR and does not affect main until merged.

If a merged change breaks main:

1. Find the merge commit with git log --oneline.
2. Create a revert branch and run git revert <merge-commit>.
3. Open a PR for the revert. It runs the same required check.
4. Merge it through the PR. Do not force-push main, because branch protection blocks it.

## Rolling back branch protection

If a protection rule blocks valid merges, update the rule with gh api -X PUT and the corrected payload, then record the change in the PR or in governance.md. Changing a required check name is a governance change, so note the reason.

## Emergency bypass

In this solo repo, admin bypass is enabled. Use it only for a real outage, and note the reason in the repo. Normal changes go through a PR.