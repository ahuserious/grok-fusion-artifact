# Limitations

## Cost-limited sample

This is a small release-engineering artifact. It contains one completed direct-xAI fusion, two native-agent attempts on one synthetic review task, and two transparent direct-provider preflight failures. It has no repeated tasks, randomization, solo baseline, confidence interval, blinded judge, or significance test.

The selected receipts are not a complete development billing statement. Only retained telemetry with an exact reported cost is added to the published selected total.

## Version binding

The direct-xAI run exercised the `0.4.0` release-candidate external fusion path. Version `0.4.1` subsequently corrected native Grok model/effort metadata and schema constraints; it did not change provider or orchestration code. The native Grok Build smoke exercised the `0.4.1` installed profile. The direct replay must not be called an exact `0.4.1` config-blob run.

## Model and provider coverage

All completed external calls used exact Grok 4.5 through direct xAI. Role diversity is not model-family diversity. Direct OpenAI, direct Anthropic, OpenRouter, OpenRouter native Fusion, and TrustedRouter-compatible endpoints were not live-tested with funded credentials.

Grok Build was validated on version `0.2.106`. Later versions require compatibility retesting; this artifact does not promise forward compatibility.

## No Grok-host benchmark run

No Terminal-Bench or DeepSWE task was executed with Grok Build as the host during this campaign. Codex-hosted harness traces elsewhere may invoke Grok API seats, but they are not Grok-host benchmark evidence.

## Native evidence redaction

Raw native chat histories and update streams contain full system/project instructions, tool payloads, encrypted session material, and local context. They are withheld. The public receipt records their SHA-256 commitments, requested/actual model telemetry, usage, cost, stop reason, and verdict. A commitment allows later byte comparison; it does not make the private content reproducible from this repository.

## Integrity boundary

SHA-256 detects drift and inconsistent partial artifacts. It is not a signature against an attacker able to rewrite the whole repository and recompute hashes. The immutable Git commit/tag is the publication anchor.
