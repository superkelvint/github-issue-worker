# Issue Worker

The $issue skill runs one GitHub issue from selection through pull request.

It supports:
- optional hard filtering such as $issue hnsw or $issue "schema fidelity";
- atomic claiming through the canonical codex/issue-N remote branch;
- regression-test-first bug fixes;
- focused implementation and verification;
- pull-request handoff without auto-merge;
- mandatory terminal cleanup: after a successful claim, the worker must either open/preserve an implementation PR or release the claim.

See SKILL.md for the authoritative workflow.
