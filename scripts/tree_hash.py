#!/usr/bin/env python3
"""Compute the artifact's reproducible plugin-tree digest.

The aggregate is SHA-256 over canonical JSON encoding of the ordered ``files``
array.  Each record binds a POSIX relative path, normalized Git-style executable
mode, byte length, and SHA-256 of the file bytes.  No path normalization beyond
``Path.as_posix()`` is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ALGORITHM_ID = "ri-tree-sha256-v1"
EXCLUDED_DIRECTORY_NAMES = frozenset({".git", "__pycache__"})
EXCLUDED_FILE_NAMES = frozenset({".DS_Store"})
EXCLUDED_FILE_SUFFIXES = frozenset({".pyc"})


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_entries(root: Path) -> list[dict[str, object]]:
    resolved_root = root.resolve(strict=True)
    entries: list[dict[str, object]] = []
    for path in resolved_root.rglob("*"):
        relative = path.relative_to(resolved_root)
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symbolic links are unsupported: {relative.as_posix()}")
        if not path.is_file():
            continue
        if path.name in EXCLUDED_FILE_NAMES or path.suffix in EXCLUDED_FILE_SUFFIXES:
            continue
        executable = bool(path.stat().st_mode & 0o111)
        entries.append(
            {
                "mode": "100755" if executable else "100644",
                "path": relative.as_posix(),
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return sorted(entries, key=lambda entry: str(entry["path"]))


def aggregate_sha256(entries: list[dict[str, object]]) -> str:
    return hashlib.sha256(canonical_json(entries).encode("utf-8")).hexdigest()


def receipt(entries: list[dict[str, object]]) -> dict[str, object]:
    return {
        "aggregate_sha256": aggregate_sha256(entries),
        "algorithm": {
            "aggregate": "sha256(utf8(canonical_json(files)))",
            "canonical_json": (
                "JSON sort_keys=true, separators=(',', ':'), ensure_ascii=false, "
                "allow_nan=false"
            ),
            "excluded_directory_names": sorted(EXCLUDED_DIRECTORY_NAMES),
            "excluded_file_names": sorted(EXCLUDED_FILE_NAMES),
            "excluded_file_suffixes": sorted(EXCLUDED_FILE_SUFFIXES),
            "file_digest": "sha256(raw_file_bytes)",
            "id": ALGORITHM_ID,
            "mode": "100755 when any executable bit is set; otherwise 100644",
            "ordering": "ascending POSIX relative path; no Unicode normalization",
            "symlinks": "rejected",
        },
        "files": entries,
        "schema_version": 1,
    }


def validate_input_receipt(value: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return ["tree inputs have an unsupported schema"]
    algorithm = value.get("algorithm")
    expected_algorithm = receipt([])["algorithm"]
    if algorithm != expected_algorithm:
        failures.append("tree input algorithm declaration mismatch")
    files = value.get("files")
    if not isinstance(files, list):
        return failures + ["tree input files must be an array"]
    expected_paths: list[str] = []
    for index, entry in enumerate(files):
        if not isinstance(entry, dict) or set(entry) != {"mode", "path", "sha256", "size_bytes"}:
            failures.append(f"tree input file {index} schema mismatch")
            continue
        path = entry.get("path")
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or "\\" in path
        ):
            failures.append(f"tree input file {index} has an unsafe relative path")
        else:
            expected_paths.append(path)
        if entry.get("mode") not in {"100644", "100755"}:
            failures.append(f"tree input file {index} has an invalid mode")
        digest = entry.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            failures.append(f"tree input file {index} has an invalid SHA-256")
        size = entry.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            failures.append(f"tree input file {index} has an invalid size")
    if expected_paths != sorted(expected_paths) or len(expected_paths) != len(set(expected_paths)):
        failures.append("tree input paths must be unique and sorted")
    if value.get("aggregate_sha256") != aggregate_sha256(files):
        failures.append("tree input aggregate SHA-256 mismatch")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--expect")
    parser.add_argument("--compare-inputs", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        entries = tree_entries(args.root)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    value = receipt(entries)
    failures: list[str] = []
    if args.expect is not None and value["aggregate_sha256"] != args.expect:
        failures.append(
            f"tree digest {value['aggregate_sha256']} does not match expected {args.expect}"
        )
    if args.compare_inputs is not None:
        expected = json.loads(args.compare_inputs.read_text(encoding="utf-8"))
        failures.extend(validate_input_receipt(expected))
        if expected.get("files") != entries:
            failures.append("tree files differ from the published input manifest")
    if args.json:
        print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(value["aggregate_sha256"])
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
