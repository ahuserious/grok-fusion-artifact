# Reproduction Jigs

Both wrappers require `--execute`; neither embeds credentials or silently installs dependencies.

- `live-fusion/run.sh` calls the pinned runtime's maximum-intelligence direct-xAI profile.
- `native-build/run.sh` resolves the installed plugin path and runs its native adversarial-review profile with exact `grok-4.5` at `high` and no tools.

The original task text was synthetic release-review material. `live-fusion/task.txt` and `native-build/task.txt` provide equivalent bounded tasks, not a claim of byte-identical private prompts.
