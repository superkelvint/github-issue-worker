# GitHub Coding Agent Skills

This repository contains two independent Codex/ChatGPT skills for a GitHub issue-to-PR workflow.

## $issue

Select one open issue, optionally filter by keyword, claim it atomically, implement it test-first, verify it, and open a PR.

Examples:

~~~text
$issue
$issue hnsw
$issue "schema fidelity"
~~~

Once $issue successfully claims an issue, it may not terminate with the issue stranded: it must either open/preserve an implementation PR or release the claim.

## $verify

Process all open PRs that are still in GitHub draft state. Verify the exact head, run repository-required tests/checks, repair PR-scoped failures when safe, push fixes to the existing branch, reverify, and mark the PR ready for review only when all required gates pass.

~~~text
$verify
~~~

$verify never merges or approves PRs. Non-draft PRs are outside its queue.

## Layout

~~~text
issue/
  SKILL.md
  agents/openai.yaml
  scripts/claim_issue.py
  scripts/release_issue.py
verify/
  SKILL.md
  agents/openai.yaml
~~~

## Local install

Clone the repository once, then expose each skill directory under Codex's skill directory:

~~~bash
mkdir -p ~/.codex/skills ~/.codex/github-skill-repos
git clone https://github.com/superkelvint/github-issue-worker.git \
  ~/.codex/github-skill-repos/github-issue-worker
ln -s ~/.codex/github-skill-repos/github-issue-worker/issue ~/.codex/skills/issue
ln -s ~/.codex/github-skill-repos/github-issue-worker/verify ~/.codex/skills/verify
~~~

If you previously installed the old repository-root $issue skill, remove that old installation first to avoid duplicate discovery.

Update both skills later with:

~~~bash
cd ~/.codex/github-skill-repos/github-issue-worker
git pull
~~~

Restart Codex after installing or updating skills.
