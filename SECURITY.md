# Security and Redaction Policy

This repository was generated from an explicit allowlist. It contains no auth files, API-key values, provider authorization headers, local private configuration, raw Grok sessions, prompt history, encrypted update material, or absolute private paths.

Only environment-variable names such as `XAI_API_KEY` appear. The verifier rejects common xAI/OpenAI/GitHub/private-key shapes, long base64url-like token strings, bearer values, absolute home paths, macOS per-user temporary paths, and generic POSIX temporary paths.

Direct-xAI response artifacts retain non-secret xAI request IDs so their exact response hashes and receipt chain remain auditable. The native receipt does not expose private session IDs or file locations; it publishes only cryptographic commitments and non-secret telemetry.

Do not open a public issue containing a credential. Use private vulnerability reporting where available, and rotate any credential that was pasted into chat or logs even when repository scans are clean.
