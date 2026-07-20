#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

case "${1:---preview}" in
  --preview)
    python3 "$script_dir/render_prompt.py"
    echo "Historical successful attempt: USD 0.1349708; two-attempt native total: USD 0.2574256." >&2
    echo "Grok Build exposes no per-invocation dollar hard cap here; execution is bounded to one turn with no tools." >&2
    exit 0
    ;;
  --execute)
    if [ "${2:-}" != "--acknowledge-billable-host-without-dollar-cap" ]; then
      echo "Refusing billable run. Re-run with --execute --acknowledge-billable-host-without-dollar-cap." >&2
      exit 2
    fi
    ;;
  *)
    echo "Usage: $0 [--preview | --execute --acknowledge-billable-host-without-dollar-cap]" >&2
    exit 2
    ;;
esac

plugin_path=$(grok plugin list --json | python3 -c '
import json, sys
plugins = json.load(sys.stdin)
matches = [plugin.get("path", "") for plugin in plugins if plugin.get("name") == "relentless-inception-grok"]
print(matches[0] if len(matches) == 1 else "")
')
if [ -z "$plugin_path" ] || [ ! -f "$plugin_path/agents/adversarial-review.md" ]; then
  echo "Installed relentless-inception-grok profile not found." >&2
  exit 1
fi

prompt_file=$(mktemp "${TMPDIR:-/tmp}/grok-native-fusion-prompt.XXXXXX")
trap 'rm -f "$prompt_file"' EXIT HUP INT TERM
python3 "$script_dir/render_prompt.py" > "$prompt_file"

grok \
  --agent "$plugin_path/agents/adversarial-review.md" \
  --model grok-4.5 \
  --reasoning-effort high \
  --max-turns 1 \
  --no-subagents \
  --disable-web-search \
  --no-plan \
  --tools '' \
  --verbatim \
  --prompt-file "$prompt_file"
