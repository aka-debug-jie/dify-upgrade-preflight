# Contributing

Thank you for helping improve Dify Upgrade Preflight.

Before opening a public issue or pull request, remove all secrets, deployment configuration, raw Compose output, `.env` files, logs, database content, host paths, and container identifiers. Report security-sensitive issues through the process in [SECURITY.md](SECURITY.md).

Changes to an approved upgrade rule or support edge need immutable official evidence, explicit source and target versions, positive, negative, unknown, and boundary cases, plus owner approval recorded in `governance/approvals.yaml`. A candidate is not an approved rule.

Run the applicable test suite and validation commands before proposing a change. Do not submit automatic upgrades, production access, telemetry, raw user configurations, or generated evidence that cannot be publicly reviewed.

This repository is in beta. A passing `NO_KNOWN_BLOCKERS` result remains limited to the declared snapshot, exact support edge, approved catalog, and listed checks.
