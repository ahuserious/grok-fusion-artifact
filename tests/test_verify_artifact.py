from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts import verify_artifact


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class ArtifactMutationTests(unittest.TestCase):
    def copied_repository(self, temporary: str) -> Path:
        destination = Path(temporary) / "artifact"
        shutil.copytree(
            ROOT,
            destination,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return destination

    def test_published_direct_receipt_chain_is_valid(self) -> None:
        self.assertEqual(verify_artifact.verify_direct_evidence(ROOT), [])

    def test_mutated_response_breaks_receipt_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            response_path = next(
                (root / "evidence/runs/grok-040-frontier-smoke-003/responses").glob("*.json")
            )
            response = verify_artifact.load_json(response_path)
            response["response"]["text"] += "\nmutation"
            write_json(response_path, response)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertTrue(any("receipt chain mismatch" in failure for failure in failures))

    def test_mutated_token_total_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            ledger_path = root / "evidence/runs/grok-040-frontier-smoke-003/ledger.json"
            ledger = verify_artifact.load_json(ledger_path)
            ledger["total_tokens"] += 1
            write_json(ledger_path, ledger)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn(
                "direct ledger 53,462 total-token invariant mismatch",
                failures,
            )

    def test_mutated_gate_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            gate_path = root / "evidence/runs/grok-040-frontier-smoke-003/gate-0.json"
            gate = verify_artifact.load_json(gate_path)
            gate["artifact_sha256"] = "0" * 64
            write_json(gate_path, gate)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn("direct gate exact-hash/pass invariant mismatch", failures)

    def test_mutated_native_stop_reason_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            receipt_path = root / "evidence/native-build/native-smoke-receipt.json"
            receipt = verify_artifact.load_json(receipt_path)
            receipt["attempts"][1]["stop_reason"] = "cancelled"
            write_json(receipt_path, receipt)
            failures = verify_artifact.verify_native_evidence(root)
            self.assertIn(
                "native attempt model/effort/stop/token/cost/verdict facts mismatch",
                failures,
            )

    def test_mutated_combined_cost_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            summary_path = root / "evidence/campaign-summary.json"
            summary = verify_artifact.load_json(summary_path)
            summary["combined_selected_known_cost_usd"] = 0.44
            write_json(summary_path, summary)
            failures = verify_artifact.verify_summaries_and_jigs(root)
            self.assertIn("combined selected cost mismatch", failures)

    def test_tree_input_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            inputs_path = root / "evidence/source-tree/tree-hash-inputs.json"
            inputs = verify_artifact.load_json(inputs_path)
            inputs["files"][0]["size_bytes"] += 1
            write_json(inputs_path, inputs)
            failures = verify_artifact.verify_tree_evidence(root)
            self.assertTrue(any("aggregate" in failure for failure in failures))

    def test_scanner_rejects_secret_and_private_path_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.txt"
            secret = b"xai" + b"-" + b"A" * 32
            private_path = b"/" + b"Users" + b"/example/private.txt"
            candidate.write_bytes(secret + b"\n" + private_path + b"\n")
            failures = verify_artifact.scan_payloads([candidate], root)
            self.assertTrue(any("credential pattern" in failure for failure in failures))
            self.assertTrue(any("private path pattern" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
