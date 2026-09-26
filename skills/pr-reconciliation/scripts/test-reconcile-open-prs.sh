#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
subject="$script_dir/reconcile-open-prs.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/bin"

cat > "$tmp/bin/gh" <<'GH'
#!/usr/bin/env bash
set -u

if [[ "${1-}" == "repo" && "${2-}" == "view" ]]; then
  echo "acme/widgets"
  exit 0
fi

if [[ "${1-}" == "api" && "${2-}" == "--paginate" ]]; then
  printf '11\n12\n13\n'
  exit 0
fi

if [[ "${1-}" == "pr" && "${2-}" == "update-branch" && "${3-}" == "--help" ]]; then
  exit 0
fi

if [[ "${1-}" == "pr" && "${2-}" == "update-branch" ]]; then
  case "${3-}" in
    11) echo "updated"; exit 0 ;;
    12) echo "merge conflict" >&2; exit 1 ;;
    13) echo "already up to date"; exit 0 ;;
  esac
fi

echo "unexpected fake gh invocation: $*" >&2
exit 99
GH
chmod +x "$tmp/bin/gh"

output="$(PATH="$tmp/bin:$PATH" "$subject" 2>&1)"

grep -Fq 'PR reconciliation: repo=acme/widgets base=main open=3' <<< "$output"
grep -Fq 'OK   #11' <<< "$output"
grep -Fq 'SKIP #12: merge conflict' <<< "$output"
grep -Fq 'OK   #13' <<< "$output"
grep -Fq 'Summary: discovered=3 reconciled=2 skipped=1' <<< "$output"

output="$(PATH="$tmp/bin:$PATH" "$subject" --repo acme/widgets --base develop --dry-run 2>&1)"
grep -Fq 'base=develop open=3' <<< "$output"
grep -Fq 'DRY-RUN #11: would request branch update from develop' <<< "$output"
grep -Fq 'Summary: discovered=3 dry_run=3' <<< "$output"

echo "reconcile-open-prs tests PASS"
