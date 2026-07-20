#!/usr/bin/env python3
"""Verify or refresh the curated artifact manifest using only stdlib."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "artifact-manifest.json"
CHECKSUMS = ROOT / "checksums" / "SHA256SUMS"
EXCLUDED = {
    "manifests/artifact-manifest.json",
    "checksums/SHA256SUMS",
}
SECRET_PATTERNS = {
    "xai_key": re.compile(rb"\bxai-[A-Za-z0-9_-]{12,}"),
    "openai_key": re.compile(rb"\bsk-[A-Za-z0-9_-]{16,}"),
    "github_token": re.compile(rb"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}"),
    "bearer_value": re.compile(rb"\bBearer\s+[A-Za-z0-9._~-]{12,}", re.I),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "long_urlsafe_token": re.compile(rb"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{90,}(?![A-Za-z0-9_-])"),
}
PRIVATE_PATH_PATTERNS = (b"/Users/", b"/var/folders/")


def payload_paths() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if path.is_file() and relative.as_posix() not in EXCLUDED:
            paths.append(path)
    return sorted(paths, key=lambda value: value.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_entries() -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in payload_paths()
    ]


def scan_payloads(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        content = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        if relative != "scripts/verify_artifact.py":
            for private_path in PRIVATE_PATH_PATTERNS:
                if private_path in content:
                    failures.append(f"{relative}: private absolute path")
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(content):
                    failures.append(f"{relative}: credential pattern {name}")
        if path.suffix == ".json":
            try:
                json.loads(content)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                failures.append(f"{relative}: invalid JSON: {exc}")
    return failures


def refresh() -> None:
    entries = public_entries()
    manifest = {
        "schema_version": 1,
        "artifact": "grok-fusion-artifact",
        "generated_by": "scripts/verify_artifact.py --refresh",
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CHECKSUMS.write_text(
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries),
        encoding="utf-8",
    )


def verify() -> list[str]:
    failures: list[str] = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_header = {
        "schema_version": 1,
        "artifact": "grok-fusion-artifact",
        "generated_by": "scripts/verify_artifact.py --refresh",
    }
    for key, value in expected_header.items():
        if manifest.get(key) != value:
            failures.append(f"manifest {key} mismatch")

    expected_entries = public_entries()
    if manifest.get("files") != expected_entries:
        failures.append("manifest file list, size, or SHA-256 differs; run --refresh after review")
    expected_checksums = "".join(
        f"{entry['sha256']}  {entry['path']}\n" for entry in expected_entries
    )
    if CHECKSUMS.read_text(encoding="utf-8") != expected_checksums:
        failures.append("checksums/SHA256SUMS differs from payload")

    summary = json.loads((ROOT / "evidence" / "campaign-summary.json").read_text(encoding="utf-8"))
    if summary.get("limited_due_to_api_cost") is not True:
        failures.append("campaign must retain limited_due_to_api_cost=true")
    if summary.get("openrouter_live_tested") is not False:
        failures.append("campaign must not claim a live OpenRouter test")
    run_by_id = {run.get("id"): run for run in summary.get("runs", [])}
    direct = run_by_id.get("grok-040-frontier-smoke-003", {})
    if direct.get("calls") != 7 or direct.get("actual_models") != ["grok-4.5"]:
        failures.append("direct fusion call/model invariant mismatch")
    if run_by_id.get("terminal-bench", {}).get("status") != "not_run_with_grok_build_host":
        failures.append("Terminal-Bench must remain marked not run")
    if run_by_id.get("deep-swe", {}).get("status") != "not_run_with_grok_build_host":
        failures.append("DeepSWE must remain marked not run")

    direct_root = ROOT / "evidence" / "runs" / "grok-040-frontier-smoke-003"
    direct_manifest = json.loads((direct_root / "manifest.json").read_text(encoding="utf-8"))
    direct_ledger = json.loads((direct_root / "ledger.json").read_text(encoding="utf-8"))
    direct_models = sorted({entry.get("actual_model") for entry in direct_ledger.get("entries", [])})
    if direct_manifest.get("status") != "completed" or direct_manifest.get("stages", {}).get("gate-0", {}).get("status") != "passed":
        failures.append("published direct manifest completion/gate mismatch")
    if direct_ledger.get("calls") != 7 or direct_models != ["grok-4.5"]:
        failures.append("published direct ledger call/model mismatch")
    if abs(float(direct_ledger.get("known_cost_usd", -1)) - 0.1822328) > 1e-9:
        failures.append("published direct ledger cost mismatch")

    native = json.loads((ROOT / "evidence" / "native-build" / "native-smoke-receipt.json").read_text(encoding="utf-8"))
    attempts = native.get("attempts", [])
    if len(attempts) != 2 or attempts[-1].get("verdict") != "pass":
        failures.append("native smoke attempt/verdict mismatch")
    if any(attempt.get("requested_model") != "grok-4.5" for attempt in attempts):
        failures.append("native requested model mismatch")
    if any(attempt.get("actual_model_telemetry") != "grok-4.5-build" for attempt in attempts):
        failures.append("native served-build telemetry mismatch")
    if abs(float(native.get("selected_known_cost_usd", -1)) - 0.2574256) > 1e-9:
        failures.append("native selected cost mismatch")

    failures.extend(scan_payloads(payload_paths()))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.refresh:
        refresh()
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"PASS: {len(public_entries())} payload files verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
