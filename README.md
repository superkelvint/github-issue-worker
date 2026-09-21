# GitHub Issue Worker

A Codex/ChatGPT skill for autonomous **issue → claim → regression test → implementation → verification → pull request** work.

The important concurrency rule is deliberately simple: `codex/issue-N` is the canonical remote claim branch. It is created through GitHub's create-ref API, so concurrent workers racing for the same issue do not both proceed. The worker that cannot create the ref must choose another issue.

## Behavior

- inspects open GitHub issues and selects one atomic, reviewable task;
- optionally restricts selection to issues matching a keyword or phrase;
- reads repository `AGENTS.md` instructions before modifying code;
- claims exactly one issue before coding;
- writes a failing regression test first for reported bugs;
- implements the smallest correct fix;
- runs focused and repository-required verification;
- pushes the claimed branch and opens a PR containing `Fixes #N`;
- never auto-merges or independently closes the issue;
- safely releases abandoned claims with an actionable explanation.

## Usage

Consider all open issues:

```text
$issue
```

Restrict selection to matching issues:

```text
$issue hnsw
$issue "schema fidelity"
```

The argument is a hard filter. If nothing matching it is actionable, the worker stops instead of selecting an unrelated issue.

## Requirements

The coding environment needs `git`, Python 3, and an authenticated GitHub CLI (`gh`) with write access to the target repository.

## Install

Use this repository as a skill source in your Codex/ChatGPT skill setup, or package the directory with the OpenAI skill packaging tooling. The skill entrypoint is [`SKILL.md`](SKILL.md).

## Included utilities

- `scripts/claim_issue.py` — atomic remote claim plus best-effort assignment/comment/label metadata.
- `scripts/release_issue.py` — release an abandoned claim while refusing to delete branches that already contain work or have an open PR.
