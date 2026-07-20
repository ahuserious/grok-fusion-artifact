# Reproduce

## Offline artifact verification

```bash
python3 scripts/verify_artifact.py
python3 -m unittest discover -s tests -v
python3 analysis/report.py
```

These commands use only the Python standard library and make no network or model calls.

## Source verification

```bash
git clone https://github.com/ahuserious/relentless-inception-grok.git
cd relentless-inception-grok
git checkout 4c9c64712cf4d34cc7a221d04ce857260ac3dccb
python3 -m unittest discover -s tests -v
python3 -m compileall -q runtime tests
grok plugin validate .
python3 /path/to/grok-fusion-artifact/scripts/tree_hash.py . \
  --expect 6d255775b39d4694c8e344f404c76a4b1516922e93b7a23b8b9b540ce9e81031 \
  --compare-inputs /path/to/grok-fusion-artifact/evidence/source-tree/tree-hash-inputs.json
```

## Billable replays

The scripts in [`jigs/`](jigs/) default to `--preview` and refuse to execute without an explicit acknowledgement. Review them first. The direct jig uses an isolated override with seven-attempt and observed-$0.50 stops; in-flight calls can cross that threshold. The native jig has a one-turn/no-tools bound, but Grok Build exposes no command-level dollar hard cap for this invocation.

The direct jig is compatible reproduction coverage, not an exact replay: the historical resolved config/task bytes were not published. The native jig publishes a new synthetic artifact and seven concrete criteria; it is not the private historical task. Provider/model/build behavior may drift, so publish a new immutable artifact rather than overwriting this campaign's receipts.
