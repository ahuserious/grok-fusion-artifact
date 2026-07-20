# Reproduce

## Offline artifact verification

```bash
python3 scripts/verify_artifact.py
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
```

## Billable replays

The scripts in [`jigs/`](jigs/) refuse to run without `--execute`. Review them first. Direct fusion uses xAI API credits; the native smoke uses Grok Build usage. Provider/model/build behavior may drift, so publish a new immutable artifact rather than overwriting this campaign's receipts.
