#!/usr/bin/env bash
set -uo pipefail

repo=""
base="main"
dry_run=0

usage() {
  cat <<'USAGE'
Usage: reconcile-open-prs.sh [--repo owner/repo] [--base branch] [--dry-run]

Best-effort reconciliation of every open PR targeting the requested base branch.
Each PR is updated independently; conflicts and permission failures are reported
and skipped. The script never resolves conflicts, rebases, force-pushes, or merges PRs.
USAGE
}

while (($#)); do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "error: --repo requires owner/repo" >&2; exit 2; }
      repo="$2"
      shift 2
      ;;
    --base)
      [[ $# -ge 2 ]] || { echo "error: --base requires a branch" >&2; exit 2; }
      base="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "error: GitHub CLI 'gh' is required" >&2
  exit 2
fi

if [[ -z "$repo" ]]; then
  if ! repo="$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)" || [[ -z "$repo" ]]; then
    echo "error: could not infer GitHub repository; pass --repo owner/repo" >&2
    exit 2
  fi
fi

# Use the REST collection with --paginate so this does not silently stop at one page.
# Avoid --slurp for compatibility with older gh versions.
pr_output=""
if ! pr_output="$(gh api --paginate "repos/${repo}/pulls?state=open&base=${base}&per_page=100" --jq '.[].number' 2>&1)"; then
  echo "error: failed to list open PRs for ${repo} base=${base}" >&2
  [[ -n "$pr_output" ]] && printf '%s\n' "$pr_output" >&2
  exit 2
fi

prs=()
while IFS= read -r line; do
  [[ -n "$line" ]] && prs+=("$line")
done <<< "$pr_output"

printf 'PR reconciliation: repo=%s base=%s open=%d\n' "$repo" "$base" "${#prs[@]}"

if ((${#prs[@]} == 0)); then
  echo "No open PRs target ${base}."
  exit 0
fi

reconciled=()
skipped=()

supports_update_branch=0
if gh pr update-branch --help >/dev/null 2>&1; then
  supports_update_branch=1
fi

for pr in "${prs[@]}"; do
  if ((dry_run)); then
    printf 'DRY-RUN #%s: would request branch update from %s\n' "$pr" "$base"
    continue
  fi

  output=""
  status=0

  if ((supports_update_branch)); then
    output="$(gh pr update-branch "$pr" -R "$repo" 2>&1)" || status=$?
  else
    # GitHub REST: Update a pull request branch. A non-2xx response is a per-PR skip.
    output="$(gh api -X PUT "repos/${repo}/pulls/${pr}/update-branch" 2>&1)" || status=$?
  fi

  if ((status == 0)); then
    reconciled+=("$pr")
    printf 'OK   #%s' "$pr"
    [[ -n "$output" ]] && printf ': %s' "$(printf '%s' "$output" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')"
    printf '\n'
  else
    reason="$(printf '%s' "$output" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')"
    [[ -n "$reason" ]] || reason="GitHub rejected the branch update"
    skipped+=("#$pr: $reason")
    printf 'SKIP #%s: %s\n' "$pr" "$reason" >&2
  fi
done

if ((dry_run)); then
  printf 'Summary: discovered=%d dry_run=%d\n' "${#prs[@]}" "${#prs[@]}"
  exit 0
fi

printf 'Summary: discovered=%d reconciled=%d skipped=%d\n' \
  "${#prs[@]}" "${#reconciled[@]}" "${#skipped[@]}"

if ((${#skipped[@]})); then
  echo "Skipped PRs:"
  printf '  %s\n' "${skipped[@]}"
fi

# Individual PR failures are expected in a best-effort sweep. Exit zero unless setup/listing failed.
exit 0
