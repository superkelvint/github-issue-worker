# GitHub Coding Agent Skills

This repository contains three independent Codex/ChatGPT skills for a GitHub issue-to-PR workflow.

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

## $issue-followup

Process one open issue labeled `needs-followup`, claim it by moving the issue to `followup-in-progress`, update the existing PR/branch with the requested correction or missing verification, then hand it back by marking the PR ready and moving the issue to `needs-cto-review`.

~~~text
$issue-followup
~~~

$issue-followup does not merge, approve, close, or create replacement PRs for ordinary follow-up work.

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
issue-followup/
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
ln -s ~/.codex/github-skill-repos/github-issue-worker/issue-followup ~/.codex/skills/issue-followup
~~~

If you previously installed the old repository-root $issue skill, remove that old installation first to avoid duplicate discovery.

Update all skills later with:

~~~bash
cd ~/.codex/github-skill-repos/github-issue-worker
git pull
~~~

Restart Codex after installing or updating skills.
