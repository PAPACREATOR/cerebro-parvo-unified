feat(docs): add UNKNOWN policy and workflow rules

This PR adds a formalized UNKNOWN policy file describing the TUDO-OU-NADA runner behavior, exit codes, and developer rules. It documents the expectation that the runner performs capability checks and aborts with UNKNOWN when needed, and that PRs are small, tested and reversible.

How to review locally:
1. Checkout branch: git fetch origin && git checkout block/b-adapters
2. Open docs/UNKNOWN_POLICY.md and review the text in Portuguese.

Notes:
- This commit does not change code. It documents the operational policy required by the project.
