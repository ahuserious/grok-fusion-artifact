# Limitations

## Cost-limited sample

This is a small release-engineering artifact. It contains one completed direct-xAI fusion, an operator-attested account of two native-agent attempts, one new synthetic native reproduction jig, and two transparent direct-provider preflight failures. It has no repeated tasks, randomization, solo baseline, confidence interval, blinded judge, or significance test.

The selected receipts are not a complete development billing statement. Only retained telemetry with an exact reported cost is added to the published selected total.

## Version binding

The direct receipts contain hashes for their resolved config, inputs, prompts, and responses, but no Git commit or source-tree hash. Commit `2963abb...` is only a chronological candidate: it was committed after the run completed. The public wrapper is **not an exact replay** because the exact historical task/config bytes were not published. External provider/orchestration implementation files are unchanged between that candidate and the tested `0.4.1` commit, which supports compatibility testing but does not repair the missing source binding.

## Model and provider coverage

All completed external calls used exact Grok 4.5 through direct xAI. Role diversity is not model-family diversity. Direct OpenAI, direct Anthropic, OpenRouter, OpenRouter native Fusion, and TrustedRouter-compatible endpoints were not live-tested with funded credentials.

Grok Build was validated on version `0.2.106`. Later versions require compatibility retesting; this artifact does not promise forward compatibility.

## No Grok-host benchmark run

Terminal-Bench and DeepSWE were **not run** with Grok Build as the host during this campaign. Codex-hosted harness traces elsewhere may invoke Grok API seats, but they are not Grok-host benchmark evidence.

## Native evidence redaction

Raw native chat histories and update streams contain full system/project instructions, tool payloads, encrypted session material, and local context. They are withheld. The public operator-attested receipt records SHA-256 commitments and the operator's model, effort, usage, cost, stop-reason, and verdict observations. A commitment allows later byte comparison; it does not let a public reviewer verify what prompt/profile/flags were used or interpret the private content.

The new native jig is a compatibility test over a fully published synthetic artifact and criteria. It is not a reconstruction of the historical private task.

## Spend-control boundary

The direct jig isolates configuration and lowers the runtime to seven dispatch attempts with an observed-cost stop at $0.50. Already in-flight calls can cross an observed threshold, so this is not a prepaid provider cap. Grok Build 0.2.106 exposes no dollar cap for the native command used here; the native jig is limited to one turn/no tools and requires acknowledgement of that uncapped-host boundary.

## Integrity boundary

SHA-256 detects drift and inconsistent partial artifacts. It is not a signature against an attacker able to rewrite the whole repository and recompute hashes. The immutable Git commit/tag is the publication anchor.
