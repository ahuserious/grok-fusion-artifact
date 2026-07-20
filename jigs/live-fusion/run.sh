#!/bin/sh
set -eu

: "${RI_GROK_SOURCE:?Set RI_GROK_SOURCE to the pinned plugin checkout}"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
compatibility_commit=4c9c64712cf4d34cc7a221d04ce857260ac3dccb
resolved_commit=$(git -C "$RI_GROK_SOURCE" rev-parse HEAD 2>/dev/null || true)
if ! git -C "$RI_GROK_SOURCE" cat-file -e "$compatibility_commit^{commit}" 2>/dev/null; then
  echo "RI_GROK_SOURCE does not contain tested compatibility commit $compatibility_commit." >&2
  exit 1
fi
if ! git -C "$RI_GROK_SOURCE" diff --quiet "$compatibility_commit" -- config/default.json schemas runtime; then
  echo "RI_GROK_SOURCE config/schema/runtime differs from tested compatibility commit $compatibility_commit." >&2
  exit 1
fi

preview() {
  env \
    PYTHONPATH="$RI_GROK_SOURCE/runtime" \
    RELENTLESS_INCEPTION_CONFIG="$script_dir/config.override.json" \
    RELENTLESS_INCEPTION_DATA_DIR="${RI_RUN_DATA_DIR:-<required-for-execution>}" \
    python3 -m relentless_inception config validate
  echo "Compatibility run only: the historical task/config bytes were not published."
  echo "Source compatibility: $resolved_commit matches tested config/schema/runtime at $compatibility_commit."
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
