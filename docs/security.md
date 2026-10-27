# Security

## Controls in place

- Least-privilege token. Both workflows set permissions: contents: read at the top level. The workflows only read code and upload artifacts, so they need no write access.
- SHA-pinned actions. actions/checkout, actions/setup-dotnet, and actions/upload-artifact are pinned to full commit SHAs, with the major version in a comment. Version tags can be moved by a maintainer; commit SHAs cannot.
- Branch protection on main. The required check must pass, the branch must be up to date (strict: true), force pushes are blocked, and branch deletion is blocked.
- No secrets. The workflows use no repository secrets, so a compromised step has nothing to exfiltrate.
- Fork PRs. The pull_request trigger gives fork PRs a read-only token and no secrets.
- Retention. Test results and build output expire after 14 days.

## Trade-offs

- enforce_admins is off. The repo owner can bypass protection. This is acceptable for a solo sample, but in an enterprise setup it should be on, so bypasses are impossible without an audited exception.
- Zero required approvals. A solo owner cannot approve their own PR, so approvals are set to 0. The status check still gates every merge. Enterprise repos should require at least one approval plus CODEOWNERS (see governance.md).
- First-party actions only. Every action comes from the actions organization. This keeps the trust surface small, at the cost of not using community actions for coverage reporting.

## Proposed next controls (not implemented)

- Dependabot for GitHub Actions, to propose SHA updates automatically.
- CODEOWNERS on .github/workflows/, so workflow changes need a platform reviewer.
- Organization-level rulesets and required workflows, so every repo inherits the same gate.
- Signed commits on main.
- Secret and dependency scanning. This depends on licensing for private repos.