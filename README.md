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

## GitHub access fallback

The skills prefer a runtime-native GitHub connector when it is actually exposed and sufficient. If that connector is missing or cannot perform the required authenticated repository operation, they fall back to authenticated `gh` — including inside ChatGPT/Codex runtimes. They must not substitute public web search or unauthenticated `curl` calls for private GitHub access.

## Local install

The simplest installation is to clone this repository directly as your Codex user skills directory:

~~~bash
git clone https://github.com/superkelvint/github-issue-worker.git ~/.agents/skills
~~~

That produces the discovery layout directly:

~~~text
~/.agents/skills/
  issue/SKILL.md
  verify/SKILL.md
  issue-followup/SKILL.md
~~~

Then restart Codex if the skills do not appear immediately.

Update all three skills later with:

~~~bash
git -C ~/.agents/skills pull
~~~

### If `~/.agents/skills` already contains other skills

Do not clone over an existing non-empty directory. In that case, keep this repository elsewhere and symlink its three skill directories:

~~~bash
git clone https://github.com/superkelvint/github-issue-worker.git ~/.codex/github-issue-worker
ln -s ~/.codex/github-issue-worker/issue ~/.agents/skills/issue
ln -s ~/.codex/github-issue-worker/verify ~/.agents/skills/verify
ln -s ~/.codex/github-issue-worker/issue-followup ~/.agents/skills/issue-followup
~~~

If you previously installed an older copy of any of these skills, remove that old copy or symlink first so Codex does not discover duplicate skill names.
