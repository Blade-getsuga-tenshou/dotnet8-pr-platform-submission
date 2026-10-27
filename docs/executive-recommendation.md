# Executive recommendation: Azure DevOps to GitHub migration

## Decision

Re-scope the migration. Do not accelerate or pause.

## Why

Repositories are ahead of plan, but their pipelines are behind. Every repository moved ahead of its pipeline adds split work and developer friction. Pausing would leave the estate split across two platforms with no progress on legacy products and no reliable measure of progress.

## Priorities (next 90 days)

1. Move repositories only with their pipelines. Freeze other moves.
2. Inventory all 1,500 pipelines and convert a pilot wave through shared workflows.
3. Introduce enforcement in stages: audit mode, then required checks, with stable check names.
4. Name one metric owner and fix metric definitions before any target is set.
5. Decide the path for each legacy product: a self-hosted x86 runner with an owner, or retirement.

## Stop or defer

- Stop: repository moves without a ready pipeline.
- Defer: agentic DevOps, until metrics are trusted.
- Defer: legacy products that need x86, to a separate funded track.
- Stop: building custom tooling that GitHub already provides, such as rulesets and the migration importer.

## What the evidence shows

- The conversion pattern works on one pipeline: the converted workflow passes on every pull request.
- Metrics are not yet trustworthy: only 14.9% of builds link to a commit, and the same data gives different lead times depending on the rule used.
- The restore figure depends on the statistic: 2.03 hours median, 43.64 hours mean, driven by one incident.

## Top risks

- Pipeline conversion remains behind.
- Enforcement blocks teams and causes more friction.
- Legacy products stall.

## Decisions required

- CTO: approve the re-scope, name the metric owner, and set the end-state date.
- Security: approve phased enforcement and the self-hosted runner standard for legacy products.
- Product leadership: agree which products move first, accept the revised pace, and agree how friction is measured.

## Investment

A small dedicated platform team, self-hosted Windows runners for legacy products, and the GitHub Enterprise licences. Costs are to be confirmed with the platform team before submission.