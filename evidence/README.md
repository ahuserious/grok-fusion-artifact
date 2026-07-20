# Evidence

`campaign-summary.json` indexes the campaign. `runs/` contains the exact safe artifacts retained from the direct-xAI run; its jig is compatibility coverage, not exact replay. `preflight/` preserves safe metadata from two failed attempts. `native-build/` contains an operator-attested curated receipt and hash commitments rather than private session contents. `source-history/` documents the direct source-binding gap, and `source-tree/` publishes the reproducible tree-hash inputs.

The exclusion policy is explicit in `SECURITY.md` and `LIMITATIONS.md`; omitted private bytes are not represented as published.
