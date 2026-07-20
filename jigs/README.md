# Reproduction Jigs

Both wrappers require `--execute`; neither embeds credentials or silently installs dependencies.

- `live-fusion/run.sh` requires the exact current release commit and Git tree, then rejects tracked, untracked, or ignored files in the executable/config/schema roots. It ignores mutable user config, uses an isolated data directory, and caps dispatch at seven attempts with an observed-$0.50 stop. Run `RI_GROK_SOURCE=/path/to/checkout ./jigs/live-fusion/run.sh --preview` first.
- `native-build/run.sh` renders a fully published synthetic artifact and seven criteria, resolves the installed plugin path, and runs its native adversarial-review profile with exact `grok-4.5` at `high`, one turn, and no tools. Its preview discloses that the host command has no dollar hard cap.

`live-fusion/task.txt` is an equivalent bounded task, not the historical task bytes. The current source pin makes the wrapper reproducible against the published release tree; it does not turn the replacement task into an exact replay. The native task, artifact, and criteria are a new self-contained compatibility fixture. Neither wrapper claims byte-identical replay of private prompts or outputs.
