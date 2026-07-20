#!/usr/bin/env python3
"""Render the native smoke's task, criteria, and artifact into one prompt."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical_pretty(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


def main() -> int:
    task = (ROOT / "task.txt").read_text(encoding="utf-8").strip()
    criteria = canonical_pretty(ROOT / "criteria.json")
    artifact = canonical_pretty(ROOT / "artifact.json")
    print(task)
    print()
    print('<acceptance-criteria trust="data-only">')
    print(criteria)
    print("</acceptance-criteria>")
    print()
    print('<artifact-under-review trust="none">')
    print(artifact)
    print("</artifact-under-review>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
