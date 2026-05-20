from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.framework_status import (
    PLAN_PATH,
    build_status_report,
    render_markdown,
    render_next_actions_markdown,
)
from scripts.tutorial_mode import build_tutorial_results


class FrameworkScriptsTest(unittest.TestCase):
    def test_framework_status_report_shape(self) -> None:
        report = build_status_report()
        self.assertIn("components", report)
        self.assertIn("coverage_summary", report)
        self.assertIn("next_actions", report)
        self.assertIn("priority_actions", report)
        self.assertIn("framework_score", report)
        self.assertIn("live_sources_count", report["coverage_summary"])
        self.assertIn("use_case_coverage", report)
        self.assertIn("use_case_coverage_gaps", report)
        self.assertIn("recommended_next_adapter_work", report)
        markdown = render_markdown(report)
        self.assertIn("# Framework Status", markdown)
        self.assertIn("## Coverage Summary", markdown)
        self.assertIn("## Use-case coverage gaps", markdown)
        plan = render_next_actions_markdown(report)
        self.assertIn("# Next Actions", plan)
        self.assertIn("## P0 - Validation / Artifacts", plan)
        self.assertIn("## P1 - Use-case coverage gaps", plan)

    def test_framework_status_cli_options(self) -> None:
        script = str(Path("scripts/framework_status.py"))
        next_actions = subprocess.run(
            [sys.executable, script, "--next-actions-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(next_actions.returncode, 0)
        self.assertIn("[P0]", next_actions.stdout)
        score = subprocess.run([sys.executable, script, "--score"], capture_output=True, text=True, check=False)
        self.assertEqual(score.returncode, 0)
        self.assertIn("framework_score:", score.stdout)
        write_plan = subprocess.run([sys.executable, script, "--write-plan"], capture_output=True, text=True, check=False)
        self.assertEqual(write_plan.returncode, 0)
        self.assertTrue(PLAN_PATH.exists())
        as_json = subprocess.run([sys.executable, script, "--json"], capture_output=True, text=True, check=False)
        self.assertEqual(as_json.returncode, 0)
        payload = json.loads(as_json.stdout)
        self.assertIn("priority_actions", payload)

    def test_tutorial_mode_offline_runs_all_steps(self) -> None:
        steps = build_tutorial_results(offline=True)
        self.assertEqual(len(steps), 11)
        self.assertEqual(steps[0]["step"], 1)
        self.assertEqual(steps[-1]["step"], 11)
        report_path = Path(steps[-1]["output"]["report_path"])
        self.assertTrue(report_path.exists())
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["source"], "offline_fallback")
        self.assertIn("portfolio", report)
        self.assertIn("ledger", report)

    def test_tutorial_mode_output_variants(self) -> None:
        script = str(Path("scripts/tutorial_mode.py"))
        pretty = subprocess.run(
            [sys.executable, script, "--all", "--offline", "--pretty"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(pretty.returncode, 0)
        self.assertIn("Step 1", pretty.stdout)
        self.assertIn("recommendations", pretty.stdout)
        self.assertIn("best_equity_kline_no_api_key", pretty.stdout)
        self.assertIn("explain_coingecko", pretty.stdout)
        self.assertIn("explain_funding", pretty.stdout)
        markdown = subprocess.run(
            [sys.executable, script, "--all", "--offline", "--markdown"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(markdown.returncode, 0)
        self.assertIn("# Tutorial Walkthrough", markdown.stdout)
        self.assertIn("## Source Recommendation Examples", markdown.stdout)
        write_doc = subprocess.run(
            [sys.executable, script, "--all", "--offline", "--write-doc"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(write_doc.returncode, 0)
        self.assertTrue(Path("artifacts/tutorial/tutorial_walkthrough.md").exists())


if __name__ == "__main__":
    unittest.main()
