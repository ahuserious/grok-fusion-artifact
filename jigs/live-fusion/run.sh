#!/bin/sh
set -eu

: "${RI_GROK_SOURCE:?Set RI_GROK_SOURCE to the pinned plugin checkout}"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
pinned_commit=7c7649aa7c0356ce344097e1ce344ae654f1b360
pinned_git_tree=7912e454a8bee1b1d9a04b69079f3e9c61631f4e
resolved_commit=$(git -C "$RI_GROK_SOURCE" rev-parse HEAD 2>/dev/null || true)
resolved_git_tree=$(git -C "$RI_GROK_SOURCE" rev-parse 'HEAD^{tree}' 2>/dev/null || true)
if [ "$resolved_commit" != "$pinned_commit" ] || [ "$resolved_git_tree" != "$pinned_git_tree" ]; then
  echo "RI_GROK_SOURCE must be checked out at release commit $pinned_commit (tree $pinned_git_tree)." >&2
  exit 1
fi
if ! git -C "$RI_GROK_SOURCE" diff --quiet "$pinned_commit" -- config/default.json schemas runtime; then
  echo "RI_GROK_SOURCE has tracked changes in config/schema/runtime." >&2
  exit 1
fi
untracked_runtime_files=$(git -C "$RI_GROK_SOURCE" ls-files --others --exclude-standard -- config/default.json schemas runtime)
ignored_runtime_files=$(git -C "$RI_GROK_SOURCE" ls-files --others --ignored --exclude-standard -- config/default.json schemas runtime)
if [ -n "$untracked_runtime_files" ] || [ -n "$ignored_runtime_files" ]; then
  echo "RI_GROK_SOURCE has untracked or ignored files in config/schema/runtime." >&2
  exit 1
fi

preview() {
  env \
    PYTHONPATH="$RI_GROK_SOURCE/runtime" \
    RELENTLESS_INCEPTION_CONFIG="$script_dir/config.override.json" \
    RELENTLESS_INCEPTION_DATA_DIR="${RI_RUN_DATA_DIR:-<required-for-execution>}" \
    python3 -m relentless_inception config validate
  echo "Compatibility run only: the historical task/config bytes were not published."
  echo "Source pin: release commit $resolved_commit and tree $resolved_git_tree with clean config/schema/runtime roots."
  echo "Billable ceiling: 7 dispatch attempts; observed-cost stop at USD 0.50 overall/xAI."
  echo "Caveat: in-flight calls can cross an observed-cost threshold; USD 0.50 is not a prepaid provider cap."
  echo "Historical selected direct run: USD 0.1822328 for 7 calls."
}

case "${1:---preview}" in
  --preview)
    preview
    exit 0
    ;;
  --execute)
    if [ "${2:-}" != "--acknowledge-observed-cost-cap-usd-0.50" ]; then
      echo "Refusing billable run. Re-run with --execute --acknowledge-observed-cost-cap-usd-0.50." >&2
      exit 2
    fi
    ;;
  *)
    echo "Usage: RI_GROK_SOURCE=... $0 [--preview | --execute --acknowledge-observed-cost-cap-usd-0.50]" >&2
    exit 2
    ;;
esac

: "${XAI_API_KEY:?Set XAI_API_KEY without writing it to this repository}"
: "${RI_RUN_DATA_DIR:?Set RI_RUN_DATA_DIR to an isolated output directory}"
mkdir -p "$RI_RUN_DATA_DIR"

exec env \
  PYTHONPATH="$RI_GROK_SOURCE/runtime" \
  RELENTLESS_INCEPTION_CONFIG="$script_dir/config.override.json" \
  RELENTLESS_INCEPTION_DATA_DIR="$RI_RUN_DATA_DIR" \
  python3 -m relentless_inception fuse \
  --task-file "$script_dir/task.txt" \
  --profile maximum_intelligence
