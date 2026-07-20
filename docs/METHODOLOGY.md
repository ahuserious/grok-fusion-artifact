# Methodology

## Evidence selection

Files were admitted through an explicit allowlist after schema, content, path, credential, requested/actual model, cost, gate, and version review. Raw native sessions were excluded even though their hashes are committed publicly.

## Direct replay

The ledger is the source of truth for calls, model provenance, usage, cost, warnings, and unknown-cost status. The manifest is the source of truth for stage completion. Semantic artifacts and every normalized response referenced by the receipt chain are published exactly; the mutable lock and local aggregate result are excluded.

## Native receipt

The curated receipt records two attempts independently. It does not merge the cancelled attempt into the successful one. Requested model/effort, actual telemetry model, usage, cost, stop reason, verdict, and private-file commitments are preserved.

## Version comparison

Direct orchestration was run on the 0.4.0 release candidate. Source review established that 0.4.1 changed native Grok metadata/schema constraints, not provider or fusion code. The artifact reports that review as provenance, not as a physical rerun.

## Checksums

`scripts/verify_artifact.py --refresh` lists each non-circular payload file with size and SHA-256 and writes `checksums/SHA256SUMS`. The manifest and checksum file are anchored by the Git commit/tag.
