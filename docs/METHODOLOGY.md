# Methodology

## Evidence selection

Files were admitted through an explicit allowlist after schema, content, path, credential, requested/actual model, cost, gate, and version review. Raw native sessions were excluded even though their hashes are committed publicly.

## Direct replay

The ledger is the source of truth for calls, model provenance, usage, cost, warnings, and unknown-cost status. The manifest is the source of truth for stage completion. Semantic artifacts and every normalized response referenced by the receipt chain are published exactly; the mutable lock and local aggregate result are excluded.

## Native receipt

The curated receipt records two attempts independently. It does not merge the cancelled attempt into the successful one. Requested model/effort, actual telemetry model, usage, cost, stop reason, verdict, and private-file commitments are operator-attested observations. The receipt explicitly lists which invocation semantics remain publicly unbound.

## Version comparison

The direct receipts do not contain a source commit. Chronology identifies a post-run commit as a candidate; source diffing shows the external provider/orchestration implementation files match the tested 0.4.1 commit. This supports a compatibility claim only, not exact replay or exact source attribution.

## Checksums

`scripts/verify_artifact.py --refresh` lists each non-circular payload file with size and SHA-256 and writes `checksums/SHA256SUMS`. The manifest and checksum file are anchored by the Git commit/tag.

Separately, `scripts/tree_hash.py` computes `ri-tree-sha256-v1` over the published 102-file input list. The aggregate is SHA-256 of canonical JSON records containing relative path, executable-normalized mode, byte size, and raw-file SHA-256.
