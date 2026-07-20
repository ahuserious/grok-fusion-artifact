# Provenance

## Release source

- Plugin repository: `https://github.com/ahuserious/relentless-inception-grok`
- Tested feature commit: `4c9c64712cf4d34cc7a221d04ce857260ac3dccb`
- Merged release commit: `1a5321b49ce1695701cf64bbb9c3429b2c6c917a`
- Shared tested/merged tree: `1b5c10ef0835d8c6f5eb9db9aa45bac3e8d3e3c3`
- Plugin version: `0.4.1`
- Tested source tree SHA-256: `b79e1624b60cad40a1f0995b15a7ee314aa353c3cf731187ee38843368cb9ffa`
- Installed plugin tree SHA-256: `b79e1624b60cad40a1f0995b15a7ee314aa353c3cf731187ee38843368cb9ffa`
- Grok Build: `0.2.106 (bde89716f679)`

The matching source/installed tree hashes cover relative paths, executable modes, and per-file SHA-256 while excluding Git metadata, bytecode, and `.DS_Store`.

## Direct xAI run

- Run ID: `grok-040-frontier-smoke-003`
- Created: `2026-07-20T05:36:35.487821+00:00`
- Completed: `2026-07-20T05:40:54.333431+00:00`
- Config hash: `f19fb803c7fcf1e041d4645f4e14e4a42951f5ee77f5b59fcce4302b0d9f4139`
- Input hash: `524b3e10fc09c84cdb5a77b54a37080f865b20075894726835aafafcf395ba08`
- Task hash: `78191a29e94f6073d1138a88e70f610012c99ee3faa2ec4c394f27eb936962c9`
- Gated synthesis SHA-256: `c6dd3c8ae4da342592dab0814a9f1020288fa0e2a3dd17806532c286306d627a`

The published run excludes the mutable lock and local aggregate `result.json`. All semantic artifacts and response files referenced by the ledger are retained. The run was created on the 0.4.0 release candidate; 0.4.1 changed native-host metadata only.

## Native Grok Build smoke

Both attempts used the installed `agents/adversarial-review.md` profile and requested exact `grok-4.5` at `high`, the strongest effort exposed by Grok Build 0.2.106. Host telemetry identified the served build as `grok-4.5-build`.

Private source commitments:

| Attempt | Chat SHA-256 | Updates SHA-256 |
|---|---|---|
| 1 | `0173c38af14ddb951d1360ce040fa12d88ec1963dcfed02ed56e0136b10efc55` | `2d00021f09467eff06df391bd7a267d232923a7f8f0bff9792dd31bbb7bfa13f` |
| 2 | `7128aee7483417d25f0463f05716933a42ac5165e9bd49ef5350534523447e60` | `a4414d33315110081f0a2d2ece24cf831aa9bbe788cfb86e8dcead9c61599838` |

The raw files remain private for system-prompt, encrypted-session, tool-payload, and local-context safety.
