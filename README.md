# Grok Fusion Artifact

This repository is the public, curated evidence package for the limited-cost release campaign of [Relentless Inception for Grok Build](https://github.com/ahuserious/relentless-inception-grok). It uses the replay/result/jig organization of the [TrustedRouter Fusion DRACO artifact](https://github.com/ahuserious/trustedrouter-fusion-artifact), with added schemas, file-level SHA-256 manifests, secret/path scans, and CI verification.

> **Limited-cost engineering validation — not a benchmark leaderboard.** The campaign intentionally stopped after a small number of paid calls. It has no repeated task sample, matched baseline, confidence interval, or statistical-power claim.

## Headline results

The direct-xAI fusion run `grok-040-frontier-smoke-003` completed seven receipt-bound calls: three independent panelists, one comparative judge, one generative synthesizer, and two exact-artifact reviewers. Every call requested and returned exact `grok-4.5`; the gate passed 2/2; the ledger reports **$0.1822328**, 53,462 total tokens, and zero unknown-cost calls.

The Grok Build native-agent smoke required two visible attempts. Both requested `grok-4.5` at `high`; host telemetry resolved the served build as `grok-4.5-build`. The first attempt stopped `cancelled` after a one-turn tool attempt ($0.1224548). The corrected tool-less attempt ended normally with a structured `pass` verdict ($0.1349708). Native total was **$0.2574256**; combined selected direct/native spend was **$0.4396584**.

## Published outcomes

| Surface | Published observation | Interpretation |
|---|---|---|
| Direct xAI fusion | 7/7 exact `grok-4.5`; gate 2/2 `PASS`; $0.1822328 | External fusion, accounting, receipts, and exact-hash gate worked live |
| Native Grok Build | Attempt 1 cancelled; attempt 2 ended with structured `pass`; requested `grok-4.5`/`high`, telemetry `grok-4.5-build`; $0.2574256 total | Installed native profile worked after correcting the one-turn/tool invocation |
| Preflight attempts | One missing-key zero-call failure; one transport/DNS attempt set with no completed calls or recorded spend | Preserved failures, not model-quality results |
| Terminal-Bench | Not run with Grok Build as host | No Grok-host benchmark claim |
| DeepSWE | Not run with Grok Build as host | No Grok-host benchmark claim |
| OpenRouter | Not called live | Mock/request-shape coverage is not provider acceptance evidence |

The external panel was several role-diverse Grok 4.5 calls. That is multi-agent deliberation, not cross-model diversity. A separately funded GPT/Claude/router seat is required to demonstrate cross-model fusion.

## Evidence map

- [`evidence/campaign-summary.json`](evidence/campaign-summary.json) is the machine-readable campaign index.
- [`evidence/runs/grok-040-frontier-smoke-003/`](evidence/runs/grok-040-frontier-smoke-003/) contains the exact publishable direct-xAI run and all seven response receipts.
- [`evidence/preflight/`](evidence/preflight/) retains safe zero-result attempt metadata.
- [`evidence/native-build/native-smoke-receipt.json`](evidence/native-build/native-smoke-receipt.json) is a curated native receipt with SHA-256 commitments to withheld private session files.
- [`jigs/`](jigs/) contains explicit opt-in direct and native reproduction wrappers.
- [`docs/FINDINGS.md`](docs/FINDINGS.md), [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md), and [`LIMITATIONS.md`](LIMITATIONS.md) define what may and may not be inferred.
- [`manifests/artifact-manifest.json`](manifests/artifact-manifest.json) and [`checksums/SHA256SUMS`](checksums/SHA256SUMS) bind every published payload file.

## Verify without API spend

```bash
python3 scripts/verify_artifact.py
python3 analysis/report.py
```

The verifier checks payload hashes, JSON syntax, campaign cross-references, private paths, and common credential/token shapes. Live jigs require `--execute` and can incur xAI or Grok Build usage.

## License status

No distribution license has been selected for this artifact or its source plugin. Public visibility is not a grant of reuse rights. See [`NOTICE.md`](NOTICE.md).
