# Grok Fusion Artifact

This repository is the public, curated evidence package for the limited-cost release campaign of [Relentless Inception for Grok Build](https://github.com/ahuserious/relentless-inception-grok). It uses the replay/result/jig organization of the [TrustedRouter Fusion DRACO artifact](https://github.com/ahuserious/trustedrouter-fusion-artifact), with added schemas, file-level SHA-256 manifests, secret/path scans, and CI verification.

> **Limited-cost engineering validation — not a benchmark leaderboard.** The campaign intentionally stopped after a small number of paid calls. It has no repeated task sample, matched baseline, confidence interval, or statistical-power claim.

## Headline results

The direct-xAI fusion run `grok-040-frontier-smoke-003` completed seven receipt-bound calls: three independent panelists, one comparative judge, one generative synthesizer, and two exact-artifact reviewers. Every call requested and returned exact `grok-4.5`; the gate passed 2/2; the ledger reports **$0.1822328**, 53,462 total tokens, and zero unknown-cost calls. The public wrapper is a **compatible reproduction, not an exact replay**: the receipts do not bind a source commit, and the exact historical task/config bytes were not published.

The Grok Build native-agent smoke has an **operator-attested**, curated receipt for two visible attempts. The operator recorded both as requesting `grok-4.5` at `high`, with host telemetry naming `grok-4.5-build`. Attempt 1 stopped `cancelled` ($0.1224548); attempt 2 ended `end_turn` with a structured `pass` ($0.1349708). Native total was **$0.2574256**; combined selected direct/native spend was **$0.4396584**. Private-file hashes are byte commitments, not public proof of the invocation semantics.

## Published outcomes

| Surface | Published observation | Interpretation |
|---|---|---|
| Direct xAI fusion | 7/7 exact `grok-4.5`; gate 2/2 `PASS`; $0.1822328 | External fusion, accounting, receipts, and exact-hash gate worked live |
| Native Grok Build | Operator-observed attempt 1 cancelled; attempt 2 ended with structured `pass`; requested `grok-4.5`/`high`, telemetry `grok-4.5-build`; $0.2574256 total | Curated smoke observation; not independently reproducible from public bytes |
| Preflight attempts | One missing-key zero-call failure; one transport/DNS attempt set with no completed calls or recorded spend | Preserved failures, not model-quality results |
| Terminal-Bench | Not run with Grok Build as host | No Grok-host benchmark claim |
| DeepSWE | Not run with Grok Build as host | No Grok-host benchmark claim |
| OpenRouter | Not called live | Mock/request-shape coverage is not provider acceptance evidence |

The external panel was several role-diverse Grok 4.5 calls. That is multi-agent deliberation, not cross-model diversity. A separately funded GPT/Claude/router seat is required to demonstrate cross-model fusion.

## Evidence map

- [`evidence/campaign-summary.json`](evidence/campaign-summary.json) is the machine-readable campaign index.
- [`evidence/runs/grok-040-frontier-smoke-003/`](evidence/runs/grok-040-frontier-smoke-003/) contains the exact publishable direct-xAI run and all seven response receipts.
- [`evidence/preflight/`](evidence/preflight/) retains safe zero-result attempt metadata.
- [`evidence/native-build/native-smoke-receipt.json`](evidence/native-build/native-smoke-receipt.json) is an operator-attested native receipt with SHA-256 commitments to withheld private session files and an explicit list of semantically unbound claims.
- [`evidence/source-history/direct-run-binding.json`](evidence/source-history/direct-run-binding.json) explains why the direct jig is compatibility coverage rather than an exact replay.
- [`evidence/source-tree/`](evidence/source-tree/) publishes the complete 102-file hash input list and exact aggregate algorithm.
- [`jigs/`](jigs/) contains explicit opt-in direct and native reproduction wrappers.
- [`docs/FINDINGS.md`](docs/FINDINGS.md), [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md), and [`LIMITATIONS.md`](LIMITATIONS.md) define what may and may not be inferred.
- [`manifests/artifact-manifest.json`](manifests/artifact-manifest.json) and [`checksums/SHA256SUMS`](checksums/SHA256SUMS) bind every published payload file.

## Verify without API spend

```bash
python3 scripts/verify_artifact.py
python3 analysis/report.py
```

The verifier recomputes the direct receipt chain, ledger accounting, semantic response bindings, synthesis/gate hashes, all reported totals, native attestation arithmetic, source-tree aggregate, synthetic jig criteria, payload hashes, private paths, and broad credential/token shapes. Both jigs default to `--preview`; execution requires a surface-specific cost acknowledgement.

## License status

No distribution license has been selected for this artifact or its source plugin. Public visibility is not a grant of reuse rights. See [`NOTICE.md`](NOTICE.md).
