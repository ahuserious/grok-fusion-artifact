#!/bin/sh
set -eu

if [ "${1:-}" != "--execute" ]; then
  echo "Refusing Grok Build run. Review this script, then pass --execute." >&2
  exit 2
fi

plugin_path=$(grok plugin list --json | jq -r '.[] | select(.name == "relentless-inception-grok") | .path')
if [ -z "$plugin_path" ] || [ ! -f "$plugin_path/agents/adversarial-review.md" ]; then
  echo "Installed relentless-inception-grok profile not found." >&2
  exit 1
fi

exec grok \
  --agent "$plugin_path/agents/adversarial-review.md" \
  --model grok-4.5 \
  --reasoning-effort high \
  --max-turns 1 \
  --no-subagents \
  --disable-web-search \
  --no-plan \
  --tools '' \
  --verbatim \
  --prompt-file "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/task.txt"
