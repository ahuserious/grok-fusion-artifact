#!/usr/bin/env python3
"""Verify or refresh the curated artifact with no network dependencies."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Iterable, Mapping

try:
    from tree_hash import aggregate_sha256, validate_input_receipt
except ImportError:  # Imported as scripts.verify_artifact by the mutation tests.
    from scripts.tree_hash import aggregate_sha256, validate_input_receipt


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_RELATIVE = Path("manifests/artifact-manifest.json")
CHECKSUMS_RELATIVE = Path("checksums/SHA256SUMS")
EXCLUDED = {MANIFEST_RELATIVE.as_posix(), CHECKSUMS_RELATIVE.as_posix()}
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def joined_bytes(*parts: bytes) -> bytes:
    return b"".join(parts)


# Construct sensitive prefixes in pieces so this verifier is scanned too.
SECRET_PATTERNS = {
    "xai_key": re.compile(joined_bytes(rb"\b", b"xai", rb"-[A-Za-z0-9_-]{24,}")),
    "openai_key": re.compile(joined_bytes(rb"\b", b"sk", rb"-(?:proj-)?[A-Za-z0-9_-]{16,}")),
    "anthropic_key": re.compile(joined_bytes(rb"\b", b"sk-ant", rb"-[A-Za-z0-9_-]{16,}")),
    "github_token": re.compile(joined_bytes(rb"\b(?:", b"ghp", rb"|github_pat)_[A-Za-z0-9_]{20,}")),
    "gitlab_token": re.compile(joined_bytes(rb"\b", b"glpat", rb"-[A-Za-z0-9_-]{16,}")),
    "aws_access_key": re.compile(joined_bytes(rb"\b", b"AKIA", rb"[A-Z0-9]{16}\b")),
    "bearer_value": re.compile(joined_bytes(rb"\b", b"Bearer", rb"\s+[A-Za-z0-9._~+/-]{12,}"), re.I),
    "basic_auth_url": re.compile(rb"[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@", re.I),
    "jwt": re.compile(joined_bytes(rb"\b", b"eyJ", rb"[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{8,}\b")),
    "private_key": re.compile(joined_bytes(b"-----BEGIN ", rb"(?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    "long_urlsafe_token": re.compile(rb"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{96,}(?![A-Za-z0-9_-])"),
}
PRIVATE_PATH_PATTERNS = {
    "macOS home path": re.compile(joined_bytes(b"/", b"Users", rb"/[^/\s]+/")),
    "Linux home path": re.compile(joined_bytes(b"/", b"home", rb"/[^/\s]+/")),
    "macOS temp path": re.compile(joined_bytes(b"/", b"(?:private/)?var/folders", rb"/")),
    "POSIX temp path": re.compile(joined_bytes(b"/", rb"(?:private/)?", b"tmp", rb"/")),
    "Windows home path": re.compile(joined_bytes(rb"[A-Za-z]:\\", b"Users", rb"\\[^\\\s]+\\"), re.I),
    "file URI": re.compile(joined_bytes(b"file", rb":/{2,3}(?:[^\s)>'\"]+)"), re.I),
}

DIRECT_RUN_ID = "grok-040-frontier-smoke-003"
DIRECT_COST = Decimal("0.1822328")
NATIVE_COST = Decimal("0.2574256")
COMBINED_COST = Decimal("0.4396584")
DIRECT_TOKENS = {
    "cached": 896,
    "input": 34254,
    "output": 19208,
    "reasoning": 6196,
    "total": 53462,
}
DIRECT_TOPOLOGY = [
    (0, "panel", "grok45_researcher"),
    (1, "panel", "grok45_adversary"),
    (2, "panel", "grok45_constraint_auditor"),
    (3, "judge", "grok45_judge"),
    (4, "synthesis", "grok45_synthesizer"),
    (5, "gate", "grok45_verifier"),
    (6, "gate", "grok45_constraint_auditor"),
]
TREE_SHA256 = "6d255775b39d4694c8e344f404c76a4b1516922e93b7a23b8b9b540ce9e81031"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_json_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    def reject_nonfinite(value: str) -> None:
        raise ValueError(f"non-finite number {value}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite)


def decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise InvalidOperation
    return Decimal(str(value))


def money_equal(left: Any, right: Any) -> bool:
    return abs(decimal(left) - decimal(right)) <= Decimal("0.000000001")


def payload_paths(root: Path = ROOT) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if path.is_symlink():
            paths.append(path)
        elif path.is_file() and relative.as_posix() not in EXCLUDED:
            paths.append(path)
    return sorted(paths, key=lambda value: value.relative_to(root).as_posix())


def public_entries(root: Path = ROOT) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in payload_paths(root):
        if path.is_symlink():
            continue
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return entries


def scan_payloads(paths: Iterable[Path], root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            failures.append(f"{relative}: symbolic links are not allowed")
            continue
        content = path.read_bytes()
        for name, pattern in PRIVATE_PATH_PATTERNS.items():
            if pattern.search(content):
                failures.append(f"{relative}: private path pattern {name}")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                failures.append(f"{relative}: credential pattern {name}")
        if path.suffix == ".json":
            try:
                load_json(path)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                failures.append(f"{relative}: invalid strict JSON: {exc}")
    return failures


def refresh(root: Path = ROOT) -> None:
    entries = public_entries(root)
    manifest = {
        "schema_version": 1,
        "artifact": "grok-fusion-artifact",
        "generated_by": "scripts/verify_artifact.py --refresh",
        "files": entries,
    }
    manifest_path = root / MANIFEST_RELATIVE
    checksums_path = root / CHECKSUMS_RELATIVE
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    checksums_path.write_text(
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries),
        encoding="utf-8",
    )


def verify_payload_manifest(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    manifest = load_json(root / MANIFEST_RELATIVE)
    expected_header = {
        "schema_version": 1,
        "artifact": "grok-fusion-artifact",
        "generated_by": "scripts/verify_artifact.py --refresh",
    }
    for key, value in expected_header.items():
        if manifest.get(key) != value:
            failures.append(f"manifest {key} mismatch")
    expected_entries = public_entries(root)
    if manifest.get("files") != expected_entries:
        failures.append("manifest file list, size, or SHA-256 differs; run --refresh after review")
    expected_checksums = "".join(
        f"{entry['sha256']}  {entry['path']}\n" for entry in expected_entries
    )
    if (root / CHECKSUMS_RELATIVE).read_text(encoding="utf-8") != expected_checksums:
        failures.append("checksums/SHA256SUMS differs from payload")
    return failures


def receipt_attempt_id(invocation_sha256: str, attempt_index: int) -> str:
    return canonical_json_hash(
        {
            "attempt_index": attempt_index,
            "invocation_sha256": invocation_sha256,
            "schema_version": 1,
        }
    )


def receipt_entry_id(attempt_id: str, invocation_sha256: str, response_sha256: str) -> str:
    return canonical_json_hash(
        {
            "attempt_id": attempt_id,
            "invocation_sha256": invocation_sha256,
            "response_sha256": response_sha256,
            "schema_version": 1,
        }
    )


def evidence_matches(expected: Any, actual: Any) -> bool:
    return canonical_json_hash(expected) == canonical_json_hash(actual)


def verify_direct_evidence(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    run_root = root / "evidence" / "runs" / DIRECT_RUN_ID
    manifest = load_json(run_root / "manifest.json")
    ledger = load_json(run_root / "ledger.json")
    panel = load_json(run_root / "panel.json")
    judge = load_json(run_root / "judge.json")
    synthesis = load_json(run_root / "synthesis.json")
    gate = load_json(run_root / "gate-0.json")
    handoff = load_json(run_root / "execution-handoff.json")

    if manifest.get("run_id") != DIRECT_RUN_ID or manifest.get("status") != "completed":
        failures.append("direct manifest run/status mismatch")
    expected_stages = {
        "panel": ("panel.json", "completed"),
        "judge": ("judge.json", "completed"),
        "synthesis": ("synthesis.json", "completed"),
        "gate-0": ("gate-0.json", "passed"),
    }
    for stage, (artifact, status) in expected_stages.items():
        stage_value = manifest.get("stages", {}).get(stage, {})
        if stage_value.get("artifact") != artifact or stage_value.get("status") != status:
            failures.append(f"direct manifest stage {stage} mismatch")

    attempts = ledger.get("attempt_entries", [])
    entries = ledger.get("entries", [])
    if (
        ledger.get("schema_version") != 3
        or ledger.get("attempts") != 7
        or ledger.get("calls") != 7
        or len(attempts) != 7
        or len(entries) != 7
    ):
        failures.append("direct ledger call/attempt cardinality mismatch")
    attempt_by_index = {
        item.get("attempt_index"): item for item in attempts if isinstance(item, Mapping)
    }
    if set(attempt_by_index) != set(range(7)):
        failures.append("direct attempt indexes are not exactly 0 through 6")
    actual_attempt_topology = [
        (item.get("attempt_index"), item.get("stage"), item.get("seat"))
        for item in attempts
        if isinstance(item, Mapping)
    ]
    if actual_attempt_topology != DIRECT_TOPOLOGY:
        failures.append("direct attempt topology mismatch")

    entry_by_id: dict[str, Mapping[str, Any]] = {}
    expected_response_paths: set[str] = set()
    usage_sums = {
        "cached_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "tool_calls": 0,
    }
    cost_sum = Decimal("0")
    for index, entry_value in enumerate(entries):
        if not isinstance(entry_value, Mapping):
            failures.append(f"direct ledger entry {index} is not an object")
            continue
        entry = dict(entry_value)
        entry_id = entry.get("entry_id")
        artifact_name = entry.get("response_artifact")
        if not isinstance(entry_id, str) or not HEX_SHA256.fullmatch(entry_id):
            failures.append(f"direct ledger entry {index} has invalid entry_id")
            continue
        if entry_id in entry_by_id:
            failures.append(f"direct ledger entry {entry_id} is duplicated")
        entry_by_id[entry_id] = entry
        if artifact_name != f"responses/{entry_id}.json":
            failures.append(f"direct ledger entry {entry_id} response path mismatch")
            continue
        artifact_parts = PurePosixPath(str(artifact_name)).parts
        if artifact_parts[:1] != ("responses",) or ".." in artifact_parts:
            failures.append(f"direct ledger entry {entry_id} has unsafe response path")
            continue
        expected_response_paths.add(str(artifact_name))
        artifact_path = run_root / str(artifact_name)
        if not artifact_path.is_file():
            failures.append(f"direct response artifact missing: {artifact_name}")
            continue
        artifact = load_json(artifact_path)
        if set(artifact) != {"schema_version", "invocation", "receipt", "response"} or artifact.get("schema_version") != 1:
            failures.append(f"direct response artifact {entry_id} schema mismatch")
            continue
        invocation = artifact.get("invocation")
        receipt = artifact.get("receipt")
        response = artifact.get("response")
        if not all(isinstance(value, Mapping) for value in (invocation, receipt, response)):
            failures.append(f"direct response artifact {entry_id} nested schema mismatch")
            continue
        invocation_hash = canonical_json_hash(invocation)
        response_hash = canonical_json_hash(response)
        attempt_index = entry.get("attempt_index")
        if not isinstance(attempt_index, int) or isinstance(attempt_index, bool):
            failures.append(f"direct ledger entry {entry_id} attempt index mismatch")
            continue
        attempt_id = receipt_attempt_id(invocation_hash, attempt_index)
        computed_entry_id = receipt_entry_id(attempt_id, invocation_hash, response_hash)
        expected_receipt = {
            "attempt_id": attempt_id,
            "entry_id": computed_entry_id,
            "invocation_sha256": invocation_hash,
            "response_sha256": response_hash,
            "schema_version": 1,
        }
        if dict(receipt) != expected_receipt:
            failures.append(f"direct response artifact {entry_id} receipt chain mismatch")
        if computed_entry_id != entry_id or artifact_path.stem != computed_entry_id:
            failures.append(f"direct response artifact {entry_id} derived entry id mismatch")
        expected_attempt = {
            "attempt_id": attempt_id,
            "attempt_index": attempt_index,
            "invocation_sha256": invocation_hash,
            "seat": invocation.get("seat_name"),
            "stage": invocation.get("stage"),
        }
        if attempt_by_index.get(attempt_index) != expected_attempt:
            failures.append(f"direct response artifact {entry_id} attempt binding mismatch")
        expected_entry_fields = {
            "actual_model": response.get("actual_model"),
            "attempt_id": attempt_id,
            "attempt_index": attempt_index,
            "entry_id": computed_entry_id,
            "invocation_sha256": invocation_hash,
            "latency_seconds": response.get("latency_seconds"),
            "provider": response.get("provider"),
            "raw_status": response.get("raw_status"),
            "request_id": response.get("request_id"),
            "requested_model": response.get("requested_model"),
            "response_artifact": str(artifact_name),
            "response_sha256": response_hash,
            "route": response.get("route"),
            "seat": invocation.get("seat_name"),
            "stage": invocation.get("stage"),
            "usage": response.get("usage"),
        }
        if entry != expected_entry_fields:
            failures.append(f"direct response artifact {entry_id} does not match ledger entry")
        if (
            invocation.get("run_id") != DIRECT_RUN_ID
            or invocation.get("config_sha256") != manifest.get("config_hash")
            or invocation.get("input_sha256") != manifest.get("input_hash")
        ):
            failures.append(f"direct response artifact {entry_id} run identity mismatch")
        if (
            response.get("provider") != "xai_direct"
            or response.get("requested_model") != "grok-4.5"
            or response.get("actual_model") != "grok-4.5"
            or response.get("raw_status") != "completed"
        ):
            failures.append(f"direct response artifact {entry_id} provider/model/status mismatch")
        usage = response.get("usage")
        if not isinstance(usage, Mapping):
            failures.append(f"direct response artifact {entry_id} usage missing")
            continue
        for field in usage_sums:
            value = usage.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                failures.append(f"direct response artifact {entry_id} invalid {field}")
            else:
                usage_sums[field] += value
        try:
            cost_sum += decimal(usage.get("cost_usd"))
        except InvalidOperation:
            failures.append(f"direct response artifact {entry_id} invalid cost")
        if (
            usage.get("accounting_error") is not None
            or usage.get("unknown_cost_fail_closed") is not False
            or usage.get("input_output_usage_complete") is not True
            or usage.get("raw_usage_invalid") is not False
        ):
            failures.append(f"direct response artifact {entry_id} accounting status mismatch")

    actual_response_paths = {
        path.relative_to(run_root).as_posix() for path in (run_root / "responses").glob("*.json")
    }
    if actual_response_paths != expected_response_paths:
        failures.append("direct response file set does not exactly match ledger receipts")
    aggregate_expectations = {
        "cached_tokens": DIRECT_TOKENS["cached"],
        "input_tokens": DIRECT_TOKENS["input"],
        "output_tokens": DIRECT_TOKENS["output"],
        "reasoning_tokens": DIRECT_TOKENS["reasoning"],
        "tool_calls": 0,
    }
    if usage_sums != aggregate_expectations:
        failures.append("direct response usage sum mismatch")
    for field, expected in aggregate_expectations.items():
        if ledger.get(field) != expected:
            failures.append(f"direct ledger aggregate {field} mismatch")
    if ledger.get("total_tokens") != DIRECT_TOKENS["input"] + DIRECT_TOKENS["output"]:
        failures.append("direct ledger 53,462 total-token invariant mismatch")
    try:
        if not money_equal(ledger.get("known_cost_usd"), cost_sum) or not money_equal(cost_sum, DIRECT_COST):
            failures.append("direct ledger cost sum mismatch")
        if not money_equal(ledger.get("provider_cost_usd", {}).get("xai_direct"), DIRECT_COST):
            failures.append("direct provider cost mismatch")
    except InvalidOperation:
        failures.append("direct ledger cost is invalid")
    if (
        ledger.get("unknown_cost_calls") != 0
        or ledger.get("accounting_failure") is not None
        or ledger.get("stop_reason") is not None
        or ledger.get("warnings") != []
    ):
        failures.append("direct ledger terminal accounting state mismatch")

    actual_entry_topology = [
        (entry.get("attempt_index"), entry.get("stage"), entry.get("seat"))
        for entry in entries
        if isinstance(entry, Mapping)
    ]
    if actual_entry_topology != DIRECT_TOPOLOGY:
        failures.append("direct completed-call topology mismatch")

    def check_semantic_response(label: str, container: Mapping[str, Any]) -> dict[str, Any]:
        evidence = container.get("response_evidence")
        response = container.get("response")
        if not isinstance(evidence, Mapping) or not isinstance(response, Mapping):
            failures.append(f"{label} response/evidence missing")
            return {}
        entry = entry_by_id.get(str(evidence.get("entry_id")))
        if entry is None:
            failures.append(f"{label} references an unknown ledger entry")
            return {}
        artifact = load_json(run_root / str(entry["response_artifact"]))
        if dict(evidence) != artifact.get("receipt") or not evidence_matches(response, artifact.get("response")):
            failures.append(f"{label} response is not bound to its raw receipt")
        invocation = artifact.get("invocation")
        if not isinstance(invocation, Mapping):
            failures.append(f"{label} receipt invocation is missing")
            return {}
        return {
            "entry": entry,
            "invocation": invocation,
            "receipt": artifact.get("receipt"),
            "response": artifact.get("response"),
        }

    panel_attempts = panel.get("attempts", [])
    panel_results = panel.get("results", [])
    if (
        set(panel) != {"attempts", "degraded", "failed_count", "live_count", "results"}
        or panel.get("live_count") != 3
        or panel.get("failed_count") != 0
        or panel.get("degraded") is not False
        or len(panel_attempts) != 3
        or len(panel_results) != 3
    ):
        failures.append("direct panel cardinality/status mismatch")

    panel_item_fields = {
        "anonymous_label",
        "error",
        "response",
        "response_evidence",
        "role",
        "seat_name",
        "status",
    }
    expected_panel_seats = [seat for _, stage, seat in DIRECT_TOPOLOGY if stage == "panel"]
    panel_attempt_by_entry: dict[str, Mapping[str, Any]] = {}
    panel_attempt_entry_ids: list[str] = []
    for index, attempt in enumerate(panel_attempts):
        if not isinstance(attempt, Mapping):
            failures.append(f"panel attempt {index} is not an object")
            continue
        bound = check_semantic_response(f"panel attempt {index}", attempt)
        invocation = bound.get("invocation", {})
        entry = bound.get("entry", {})
        expected_seat = expected_panel_seats[index] if index < len(expected_panel_seats) else None
        if (
            set(attempt) != panel_item_fields
            or attempt.get("anonymous_label") != ""
            or attempt.get("error") is not None
            or attempt.get("role") != "panel"
            or attempt.get("seat_name") != expected_seat
            or attempt.get("status") != "completed"
            or invocation.get("stage") != "panel"
            or invocation.get("seat_name") != expected_seat
            or entry.get("attempt_index") != index
        ):
            failures.append(f"panel attempt {index} outer topology/label/status mismatch")
        entry_id = str(entry.get("entry_id", ""))
        if entry_id:
            panel_attempt_entry_ids.append(entry_id)
            panel_attempt_by_entry[entry_id] = attempt

    expected_result_labels = {
        "grok45_constraint_auditor": "Seat A",
        "grok45_researcher": "Seat B",
        "grok45_adversary": "Seat C",
    }
    panel_result_entry_ids: list[str] = []
    for index, result in enumerate(panel_results):
        if isinstance(result, Mapping):
            bound = check_semantic_response(f"panel result {index}", result)
            invocation = bound.get("invocation", {})
            entry = bound.get("entry", {})
            bound_seat = invocation.get("seat_name")
            if (
                set(result) != panel_item_fields
                or result.get("error") is not None
                or result.get("role") != "panel"
                or result.get("seat_name") != bound_seat
                or result.get("anonymous_label") != expected_result_labels.get(str(bound_seat))
                or result.get("status") != "completed"
                or invocation.get("stage") != "panel"
                or bound_seat not in expected_panel_seats
            ):
                failures.append(f"panel result {index} outer topology/label/status mismatch")
            entry_id = str(entry.get("entry_id", ""))
            if entry_id:
                panel_result_entry_ids.append(entry_id)
                source_attempt = panel_attempt_by_entry.get(entry_id)
                if source_attempt is None:
                    failures.append(f"panel result {index} has no matching dispatch attempt")
                elif (
                    result.get("response_evidence") != source_attempt.get("response_evidence")
                    or not evidence_matches(result.get("response"), source_attempt.get("response"))
                ):
                    failures.append(f"panel result {index} differs from its dispatch attempt")
        else:
            failures.append(f"panel result {index} is not an object")
    if (
        panel_attempt_entry_ids != [
            str(entry.get("entry_id"))
            for entry in entries[:3]
            if isinstance(entry, Mapping)
        ]
        or len(set(panel_attempt_entry_ids)) != 3
        or set(panel_result_entry_ids) != set(panel_attempt_entry_ids)
        or len(set(panel_result_entry_ids)) != 3
        or {result.get("seat_name") for result in panel_results if isinstance(result, Mapping)}
        != set(expected_panel_seats)
    ):
        failures.append("direct panel attempts/results must bind three unique independent seats")

    judge_bound = check_semantic_response("judge", judge)
    judge_invocation = judge_bound.get("invocation", {})
    judge_response = judge.get("response", {})
    try:
        parsed_judgment = (
            json.loads(judge_response.get("text", ""))
            if isinstance(judge_response, Mapping)
            else None
        )
    except json.JSONDecodeError:
        parsed_judgment = None
    if (
        set(judge) != {"judgment", "response", "response_evidence"}
        or judge_invocation.get("stage") != "judge"
        or judge_invocation.get("seat_name") != "grok45_judge"
        or parsed_judgment != judge.get("judgment")
    ):
        failures.append("judge semantic judgment/topology mismatch")

    synthesis_bound = check_semantic_response("synthesis", synthesis)
    synthesis_invocation = synthesis_bound.get("invocation", {})
    synthesis_text = synthesis.get("text")
    synthesis_hash = text_hash(synthesis_text) if isinstance(synthesis_text, str) else ""
    if (
        set(synthesis)
        != {"author_seat", "mode", "response", "response_evidence", "sha256", "text"}
        or synthesis.get("author_seat") != "grok45_synthesizer"
        or synthesis.get("mode") != "client_orchestrated"
        or synthesis_invocation.get("stage") != "synthesis"
        or synthesis_invocation.get("seat_name") != "grok45_synthesizer"
        or not isinstance(synthesis.get("response"), Mapping)
        or synthesis.get("response", {}).get("text") != synthesis_text
        or synthesis.get("sha256") != synthesis_hash
    ):
        failures.append("synthesis text/SHA-256 mismatch")

    reviewers = gate.get("reviewers", [])
    passing_reviewers = 0
    gate_reviewer_entry_ids: list[str] = []
    expected_gate_seats = [seat for _, stage, seat in DIRECT_TOPOLOGY if stage == "gate"]
    for index, reviewer in enumerate(reviewers):
        if not isinstance(reviewer, Mapping):
            failures.append(f"gate reviewer {index} is not an object")
            continue
        bound = check_semantic_response(f"gate reviewer {index}", reviewer)
        invocation = bound.get("invocation", {})
        entry = bound.get("entry", {})
        expected_seat = expected_gate_seats[index] if index < len(expected_gate_seats) else None
        if (
            set(reviewer)
            != {"response", "response_evidence", "seat_name", "status", "verdict"}
            or reviewer.get("seat_name") != expected_seat
            or reviewer.get("status") != "completed"
            or invocation.get("stage") != "gate"
            or invocation.get("seat_name") != expected_seat
        ):
            failures.append(f"gate reviewer {index} outer topology/status mismatch")
        entry_id = str(entry.get("entry_id", ""))
        if entry_id:
            gate_reviewer_entry_ids.append(entry_id)
        verdict = reviewer.get("verdict")
        response = reviewer.get("response")
        try:
            parsed_verdict = json.loads(response.get("text", "")) if isinstance(response, Mapping) else None
        except json.JSONDecodeError:
            parsed_verdict = None
        if parsed_verdict != verdict:
            failures.append(f"gate reviewer {index} parsed verdict mismatch")
        if (
            isinstance(verdict, Mapping)
            and verdict.get("verdict") == "PASS"
            and verdict.get("artifact_sha256") == synthesis_hash
            and verdict.get("blocking_findings") == []
            and verdict.get("blind_spots") == []
        ):
            passing_reviewers += 1
    if (
        len(reviewers) != 2
        or len(set(gate_reviewer_entry_ids)) != 2
        or {reviewer.get("seat_name") for reviewer in reviewers if isinstance(reviewer, Mapping)}
        != set(expected_gate_seats)
        or passing_reviewers != 2
        or gate.get("artifact_sha256") != synthesis_hash
        or gate.get("pass_count") != passing_reviewers
        or gate.get("required_passes") != 2
        or gate.get("passed") is not True
        or gate.get("deterministic_blockers") != []
        or gate.get("mechanical_failures") != []
        or gate.get("schema_failures") != []
    ):
        failures.append("direct gate exact-hash/pass invariant mismatch")
    if (
        handoff.get("synthesis_gate") != {
            "artifact_sha256": synthesis_hash,
            "owner": "mcp_runtime",
            "passed": True,
        }
        or handoff.get("ready_for_host_workflow") is not True
        or handoff.get("mutation_authorized") is not False
    ):
        failures.append("direct execution handoff gate/authorization mismatch")
    return failures


def verify_native_evidence(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    native = load_json(root / "evidence/native-build/native-smoke-receipt.json")
    attestation = native.get("attestation", {})
    if (
        attestation.get("evidence_class") != "operator_attested_curated_observation"
        or attestation.get("publicly_self_verifying") is not False
        or not attestation.get("semantically_unbound_claims")
    ):
        failures.append("native evidence must remain explicitly operator-attested and non-self-verifying")
    attempts = native.get("attempts", [])
    expected_attempts = [
        {
            "actual_model_telemetry": "grok-4.5-build",
            "cost_usd": 0.1224548,
            "private_chat_sha256": "0173c38af14ddb951d1360ce040fa12d88ec1963dcfed02ed56e0136b10efc55",
            "private_updates_sha256": "2d00021f09467eff06df391bd7a267d232923a7f8f0bff9792dd31bbb7bfa13f",
            "reasoning_effort": "high",
            "requested_model": "grok-4.5",
            "stop_reason": "cancelled",
            "tokens": {"input": 63580, "output": 195, "reasoning": 42},
            "verdict": None,
        },
        {
            "actual_model_telemetry": "grok-4.5-build",
            "cost_usd": 0.1349708,
            "private_chat_sha256": "7128aee7483417d25f0463f05716933a42ac5165e9bd49ef5350534523447e60",
            "private_updates_sha256": "a4414d33315110081f0a2d2ece24cf831aa9bbe788cfb86e8dcead9c61599838",
            "reasoning_effort": "high",
            "requested_model": "grok-4.5",
            "stop_reason": "end_turn",
            "tokens": {"input": 65322, "output": 975, "reasoning": 879},
            "verdict": "pass",
        },
    ]
    if attempts != expected_attempts:
        failures.append("native attempt model/effort/stop/token/cost/verdict facts mismatch")
    try:
        attempt_cost = sum((decimal(attempt.get("cost_usd")) for attempt in attempts), Decimal("0"))
        if attempt_cost != NATIVE_COST or decimal(native.get("selected_known_cost_usd")) != attempt_cost:
            failures.append("native selected-cost arithmetic mismatch")
    except (InvalidOperation, AttributeError):
        failures.append("native attempt cost is invalid")
    invocation = native.get("operator_observed_invocation", {})
    if invocation != {
        "agent_profile": "agents/adversarial-review.md",
        "disable_web_search": True,
        "max_turns": 1,
        "no_plan": True,
        "no_subagents": True,
        "second_attempt_tools": "none",
        "verbatim": True,
    }:
        failures.append("native operator-observed invocation summary mismatch")
    profile = native.get("profile_source_candidate", {})
    if (
        profile.get("commit") != "4c9c64712cf4d34cc7a221d04ce857260ac3dccb"
        or profile.get("profile_sha256") != "611dbb5b8ebec3fadd767db89614226af546c1f84b442852061e1e98ad75ef1e"
    ):
        failures.append("native profile source candidate mismatch")

    summary = load_json(root / "results/native-build-summary.json")
    if summary != {
        "attempts": 2,
        "evidence_class": "operator_attested_curated_observation",
        "final_verdict": "pass",
        "known_cost_usd": 0.2574256,
        "requested_model": "grok-4.5",
        "requested_reasoning_effort": "high",
        "schema_version": 1,
        "served_model_telemetry": "grok-4.5-build",
        "status": "operator_observed_pass_after_visible_cancelled_attempt",
    }:
        failures.append("native published summary mismatch")
    return failures


def verify_native_jig(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    jig_root = root / "jigs/native-build"
    artifact = load_json(jig_root / "artifact.json")
    criteria = load_json(jig_root / "criteria.json")
    release = artifact.get("release", {})
    release_file = release.get("file", {})
    verification = artifact.get("verification", {})
    unit_tests = verification.get("unit_tests", {})
    secret_scan = verification.get("secret_scan", {})
    satisfied = [
        artifact.get("schema_version") == 1
        and artifact.get("claimed_status") == "ready"
        and isinstance(release.get("name"), str)
        and bool(release.get("name"))
        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", str(release.get("version"))) is not None
        and re.fullmatch(r"[0-9a-f]{40}", str(release.get("commit"))) is not None,
        isinstance(release_file.get("size_bytes"), int)
        and release_file.get("size_bytes", 0) > 0
        and HEX_SHA256.fullmatch(str(release_file.get("sha256"))) is not None,
        verification.get("artifact_sha256") == release_file.get("sha256"),
        unit_tests == {"exit_code": 0, "failed": 0, "passed": 120, "total": 120},
        secret_scan == {"findings": 0, "status": "passed"},
        verification.get("model") == "grok-4.5"
        and verification.get("reasoning_effort") == "high",
        len(artifact.get("known_limitations", [])) == 1
        and "cost-bounded" in artifact.get("known_limitations", [""])[0]
        and "one synthetic package" in artifact.get("known_limitations", [""])[0],
    ]
    acceptance = criteria.get("acceptance_criteria", [])
    if [item.get("id") for item in acceptance if isinstance(item, Mapping)] != [
        "AC1", "AC2", "AC3", "AC4", "AC5", "AC6", "AC7"
    ] or not all(satisfied):
        failures.append("native synthetic jig does not mechanically satisfy its seven criteria")
    rendered_task = (jig_root / "task.txt").read_text(encoding="utf-8")
    if "untrusted data" not in rendered_task or "every supplied acceptance criterion" not in rendered_task:
        failures.append("native jig task lacks its adversarial data/criteria contract")
    run_script = (jig_root / "run.sh").read_text(encoding="utf-8")
    for required in (
        "--preview",
        "--acknowledge-billable-host-without-dollar-cap",
        "--max-turns 1",
        "--no-subagents",
        "--disable-web-search",
        "--tools ''",
    ):
        if required not in run_script:
            failures.append(f"native jig is missing safeguard {required}")
    return failures


def verify_tree_evidence(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    inputs = load_json(root / "evidence/source-tree/tree-hash-inputs.json")
    observation = load_json(root / "evidence/source-tree/tree-hash-observation.json")
    failures.extend(validate_input_receipt(inputs))
    if (
        inputs.get("aggregate_sha256") != TREE_SHA256
        or aggregate_sha256(inputs.get("files", [])) != TREE_SHA256
        or len(inputs.get("files", [])) != 102
        or observation.get("algorithm_id") != "ri-tree-sha256-v1"
        or observation.get("reproducible_tree_sha256") != TREE_SHA256
        or observation.get("selected_file_count") != 102
        or observation.get("source")
        != {
            "commit": "7c7649aa7c0356ce344097e1ce344ae654f1b360",
            "git_tree": "7912e454a8bee1b1d9a04b69079f3e9c61631f4e",
            "repository": "https://github.com/ahuserious/relentless-inception-grok",
        }
        or observation.get("historical_value_reproducible_from_this_artifact") is not False
    ):
        failures.append("source/installed tree-hash evidence mismatch")
    return failures


def verify_summaries_and_jigs(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    summary = load_json(root / "evidence/campaign-summary.json")
    direct_summary = load_json(root / "results/direct-xai-summary.json")
    harness = load_json(root / "results/host-harness-status.json")
    run_by_id = {run.get("id"): run for run in summary.get("runs", []) if isinstance(run, Mapping)}
    direct = run_by_id.get(DIRECT_RUN_ID, {})
    native = run_by_id.get("native-grok-build-adversarial-review", {})
    if (
        summary.get("limited_due_to_api_cost") is not True
        or summary.get("openrouter_live_tested") is not False
        or summary.get("claim_scope") != "limited_engineering_validation"
    ):
        failures.append("campaign scope/cost/OpenRouter limitation mismatch")
    if (
        direct.get("calls") != 7
        or direct.get("actual_models") != ["grok-4.5"]
        or direct.get("requested_models") != ["grok-4.5"]
        or direct.get("tokens") != DIRECT_TOKENS
        or direct.get("gate") != direct_summary.get("gate")
        or direct_summary.get("calls") != 7
        or direct_summary.get("tokens") != DIRECT_TOKENS
        or direct_summary.get("reproduction_class") != "compatible_reproduction_not_exact_replay"
        or direct_summary.get("models") != {
            "actual": ["grok-4.5"], "requested": ["grok-4.5"]
        }
        or "not_exact_replay" not in str(direct.get("current_release_binding"))
    ):
        failures.append("direct campaign/result summary mismatch")
    try:
        if decimal(direct.get("known_cost_usd")) != DIRECT_COST or decimal(direct_summary.get("known_cost_usd")) != DIRECT_COST:
            failures.append("direct summary cost mismatch")
        if decimal(native.get("known_cost_usd")) != NATIVE_COST:
            failures.append("native campaign cost mismatch")
        if decimal(summary.get("combined_selected_known_cost_usd")) != COMBINED_COST:
            failures.append("combined selected cost mismatch")
        if DIRECT_COST + NATIVE_COST != COMBINED_COST:
            failures.append("combined direct/native arithmetic constant mismatch")
    except InvalidOperation:
        failures.append("campaign/result cost is invalid")
    if (
        native.get("evidence_class") != "operator_attested_curated_observation"
        or not str(native.get("status", "")).startswith("operator_observed_")
        or harness != {
            "deep_swe": "not_run_with_grok_build_host",
            "schema_version": 1,
            "terminal_bench": "not_run_with_grok_build_host",
        }
        or run_by_id.get("terminal-bench", {}).get("status") != "not_run_with_grok_build_host"
        or run_by_id.get("deep-swe", {}).get("status") != "not_run_with_grok_build_host"
    ):
        failures.append("native/harness limitation summary mismatch")
    source = summary.get("source", {})
    if source != {
        "current_release_commit": "7c7649aa7c0356ce344097e1ce344ae654f1b360",
        "current_release_git_tree": "7912e454a8bee1b1d9a04b69079f3e9c61631f4e",
        "current_release_tree_file_count": 102,
        "current_release_tree_sha256": TREE_SHA256,
        "feature_merge_commit": "1a5321b49ce1695701cf64bbb9c3429b2c6c917a",
        "grok_build_version": "0.2.106",
        "historical_native_profile_candidate_commit": "4c9c64712cf4d34cc7a221d04ce857260ac3dccb",
        "historical_operator_recorded_tree_sha256": "b79e1624b60cad40a1f0995b15a7ee314aa353c3cf731187ee38843368cb9ffa",
        "repository": "https://github.com/ahuserious/relentless-inception-grok",
        "version": "0.4.1",
    }:
        failures.append("campaign source tree digest mismatch")
    binding = load_json(root / "evidence/source-history/direct-run-binding.json")
    manifest = load_json(root / f"evidence/runs/{DIRECT_RUN_ID}/manifest.json")
    binding_run = binding.get("direct_run", {})
    if (
        binding.get("jig_classification") != "compatible_reproduction_not_exact_replay"
        or binding.get("receipt_bound_source_commit") is not None
        or binding_run.get("run_id") != manifest.get("run_id")
        or binding_run.get("config_sha256") != manifest.get("config_hash")
        or binding_run.get("input_sha256") != manifest.get("input_hash")
        or binding_run.get("task_sha256") != manifest.get("task_hash")
    ):
        failures.append("direct source-binding disclosure mismatch")
    direct_config = load_json(root / "jigs/live-fusion/config.override.json")
    budgets = direct_config.get("profiles", {}).get("maximum_intelligence", {}).get("budgets", {})
    if (
        budgets.get("enforcement") != "hard_stop"
        or budgets.get("max_calls") != 7
        or decimal(budgets.get("max_cost_usd")) != Decimal("0.5")
        or decimal(budgets.get("per_provider_max_cost_usd", {}).get("xai_direct")) != Decimal("0.5")
        or direct_config.get("secret_env_files") != []
    ):
        failures.append("direct jig isolation/cost cap mismatch")
    direct_run_script = (root / "jigs/live-fusion/run.sh").read_text(encoding="utf-8")
    for required in (
        "--preview",
        "--acknowledge-observed-cost-cap-usd-0.50",
        "RELENTLESS_INCEPTION_CONFIG",
        "RELENTLESS_INCEPTION_DATA_DIR",
    ):
        if required not in direct_run_script:
            failures.append(f"direct jig is missing safeguard {required}")
    source_guard_requirements = (
        "pinned_commit=7c7649aa7c0356ce344097e1ce344ae654f1b360",
        "pinned_git_tree=7912e454a8bee1b1d9a04b69079f3e9c61631f4e",
        '[ "$resolved_commit" != "$pinned_commit" ] || [ "$resolved_git_tree" != "$pinned_git_tree" ]',
        'diff --quiet "$pinned_commit" -- config/default.json schemas runtime',
        'ls-files --others --exclude-standard -- config/default.json schemas runtime',
        'ls-files --others --ignored --exclude-standard -- config/default.json schemas runtime',
    )
    if not all(requirement in direct_run_script for requirement in source_guard_requirements):
        failures.append("direct jig source pin/cleanliness guard mismatch")
    readme = (root / "README.md").read_text(encoding="utf-8")
    limitations = (root / "LIMITATIONS.md").read_text(encoding="utf-8")
    for required in ("Limited-cost", "operator-attested", "compatible", "$0.4396584"):
        if required not in readme:
            failures.append(f"README is missing required disclosure {required}")
    for required in ("not an exact replay", "operator-attested", "OpenRouter", "not run"):
        if required not in limitations:
            failures.append(f"LIMITATIONS is missing required disclosure {required}")
    return failures


def verify(root: Path = ROOT, *, include_payload_manifest: bool = True) -> list[str]:
    failures: list[str] = []
    checks = [
        verify_direct_evidence,
        verify_native_evidence,
        verify_native_jig,
        verify_tree_evidence,
        verify_summaries_and_jigs,
    ]
    if include_payload_manifest:
        checks.insert(0, verify_payload_manifest)
    for check in checks:
        try:
            failures.extend(check(root))
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError, InvalidOperation) as exc:
            failures.append(f"{check.__name__} could not verify malformed evidence: {exc}")
    failures.extend(scan_payloads(payload_paths(root), root))
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
    print(f"PASS: {len(public_entries())} payload files and semantic evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
