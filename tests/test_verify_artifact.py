from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
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

    def test_duplicate_panel_results_are_rejected_by_semantic_layer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            panel_path = root / "evidence/runs/grok-040-frontier-smoke-003/panel.json"
            panel = verify_artifact.load_json(panel_path)
            panel["results"] = [panel["results"][0], panel["results"][0], panel["results"][0]]
            write_json(panel_path, panel)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn(
                "direct panel attempts/results must bind three unique independent seats",
                failures,
            )

    def test_duplicate_gate_reviewers_are_rejected_by_semantic_layer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            gate_path = root / "evidence/runs/grok-040-frontier-smoke-003/gate-0.json"
            gate = verify_artifact.load_json(gate_path)
            gate["reviewers"] = [gate["reviewers"][0], gate["reviewers"][0]]
            write_json(gate_path, gate)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn("direct gate exact-hash/pass invariant mismatch", failures)

    def test_forged_panel_attempt_outer_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            panel_path = root / "evidence/runs/grok-040-frontier-smoke-003/panel.json"
            panel = verify_artifact.load_json(panel_path)
            panel["attempts"][0]["seat_name"] = "grok45_adversary"
            panel["attempts"][0]["role"] = "judge"
            panel["attempts"][0]["status"] = "failed"
            write_json(panel_path, panel)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn("panel attempt 0 outer topology/label/status mismatch", failures)

    def test_forged_panel_result_outer_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            panel_path = root / "evidence/runs/grok-040-frontier-smoke-003/panel.json"
            panel = verify_artifact.load_json(panel_path)
            panel["results"][0]["seat_name"] = "grok45_researcher"
            panel["results"][0]["role"] = "judge"
            panel["results"][0]["status"] = "failed"
            write_json(panel_path, panel)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn("panel result 0 outer topology/label/status mismatch", failures)

    def test_contradictory_judgment_object_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            judge_path = root / "evidence/runs/grok-040-frontier-smoke-003/judge.json"
            judge = verify_artifact.load_json(judge_path)
            judge["judgment"]["final_guidance"] = ["forged semantic replacement"]
            write_json(judge_path, judge)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn("judge semantic judgment/topology mismatch", failures)

    def test_mutated_attempt_topology_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            ledger_path = root / "evidence/runs/grok-040-frontier-smoke-003/ledger.json"
            ledger = verify_artifact.load_json(ledger_path)
            ledger["attempt_entries"][0]["seat"] = "grok45_adversary"
            write_json(ledger_path, ledger)
            failures = verify_artifact.verify_direct_evidence(root)
            self.assertIn("direct attempt topology mismatch", failures)

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

    def test_tree_commit_tree_and_file_count_cross_binding_is_rejected(self) -> None:
        mutations = (
            ("source.commit", "4c9c64712cf4d34cc7a221d04ce857260ac3dccb"),
            ("source.git_tree", "1b5c10ef0835d8c6f5eb9db9aa45bac3e8d3e3c3"),
            ("selected_file_count", 98),
        )
        for dotted_path, replacement in mutations:
            with self.subTest(dotted_path=dotted_path), tempfile.TemporaryDirectory() as temporary:
                root = self.copied_repository(temporary)
                observation_path = root / "evidence/source-tree/tree-hash-observation.json"
                observation = verify_artifact.load_json(observation_path)
                current = observation
                segments = dotted_path.split(".")
                for segment in segments[:-1]:
                    current = current[segment]
                current[segments[-1]] = replacement
                write_json(observation_path, observation)
                failures = verify_artifact.verify_tree_evidence(root)
                self.assertIn("source/installed tree-hash evidence mismatch", failures)

    def test_scanner_rejects_secret_and_private_path_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.txt"
            secret = b"xai" + b"-" + b"A" * 32
            private_path = b"/" + b"Users" + b"/example/private.txt"
            posix_temp_path = b"/" + b"tmp" + b"/private-output.json"
            private_posix_temp_path = b"/" + b"private" + b"/" + b"tmp" + b"/private-output.json"
            candidate.write_bytes(secret + b"\n" + private_path + b"\n")
            first_temp_candidate = root / "first-temp-candidate.txt"
            first_temp_candidate.write_bytes(posix_temp_path + b"\n")
            second_temp_candidate = root / "second-temp-candidate.txt"
            second_temp_candidate.write_bytes(private_posix_temp_path + b"\n")
            failures = verify_artifact.scan_payloads(
                [candidate, first_temp_candidate, second_temp_candidate],
                root,
            )
            self.assertTrue(any("credential pattern" in failure for failure in failures))
            self.assertTrue(any("private path pattern" in failure for failure in failures))
            self.assertEqual(
                sum("private path pattern POSIX temp path" in failure for failure in failures),
                2,
            )

    def test_refresh_cannot_bless_posix_temp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_repository(temporary)
            leaked_path = b"/" + b"tmp" + b"/private-output.json"
            (root / "evidence/leaked-path.txt").write_bytes(leaked_path + b"\n")
            verify_artifact.refresh(root)
            failures = verify_artifact.verify(root)
            self.assertTrue(
                any("private path pattern POSIX temp path" in failure for failure in failures)
            )

    def test_live_jig_rejects_later_commit_and_untracked_runtime_files(self) -> None:
        pinned_commit = "7c7649aa7c0356ce344097e1ce344ae654f1b360"
        pinned_git_tree = "7912e454a8bee1b1d9a04b69079f3e9c61631f4e"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            source = root / "source"
            source.mkdir()
            fake_git = fake_bin / "git"
            fake_git.write_text(
                """#!/bin/sh
case "$*" in
  *"rev-parse HEAD") printf '%s\\n' "${FAKE_COMMIT:?}" ;;
  *"rev-parse HEAD^{tree}") printf '%s\\n' "${FAKE_TREE:?}" ;;
  *"diff --quiet"*) exit "${FAKE_DIFF_EXIT:-0}" ;;
  *"ls-files --others --exclude-standard"*) printf '%s' "${FAKE_UNTRACKED:-}" ;;
  *"ls-files --others --ignored --exclude-standard"*) printf '%s' "${FAKE_IGNORED:-}" ;;
  *) exit 64 ;;
esac
""",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            fake_python = fake_bin / "python3"
            fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_python.chmod(0o755)
            base_environment = {
                "PATH": f"{fake_bin}:/usr/bin:/bin",
                "RI_GROK_SOURCE": str(source),
                "FAKE_COMMIT": pinned_commit,
                "FAKE_TREE": pinned_git_tree,
            }
            run_script = ROOT / "jigs/live-fusion/run.sh"
            clean = subprocess.run(
                [str(run_script), "--preview"],
                env=base_environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(clean.returncode, 0, clean.stderr)

            later_commit_environment = dict(base_environment)
            later_commit_environment["FAKE_COMMIT"] = "f" * 40
            later_commit = subprocess.run(
                [str(run_script), "--preview"],
                env=later_commit_environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(later_commit.returncode, 0)

            untracked_environment = dict(base_environment)
            untracked_environment["FAKE_UNTRACKED"] = "runtime/shadow.py"
            untracked = subprocess.run(
                [str(run_script), "--preview"],
                env=untracked_environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(untracked.returncode, 0)

            ignored_environment = dict(base_environment)
            ignored_environment["FAKE_IGNORED"] = "runtime/shadow.pyc"
            ignored = subprocess.run(
                [str(run_script), "--preview"],
                env=ignored_environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(ignored.returncode, 0)


if __name__ == "__main__":
    unittest.main()
