#!/usr/bin/env python3
"""Render a deterministic compact report from the public campaign summary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "evidence" / "campaign-summary.json"


def main() -> int:
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    print(f"artifact: {data['artifact']}")
    print(f"scope: {data['claim_scope']}")
    print("runs:")
    for run in data["runs"]:
        cost = run.get("known_cost_usd", "n/a")
        print(f"- {run['id']}: {run['status']}; reported cost={cost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
