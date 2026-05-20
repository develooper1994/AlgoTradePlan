from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.framework_status import build_status_report, render_markdown
from scripts.tutorial_mode import build_tutorial_results


class FrameworkScriptsTest(unittest.TestCase):
    def test_framework_status_report_shape(self) -> None:
        report = build_status_report()
        self.assertIn("components", report)
        self.assertIn("coverage_summary", report)
        self.assertIn("next_actions", report)
        self.assertIn("live_sources_count", report["coverage_summary"])
        markdown = render_markdown(report)
        self.assertIn("# Framework Status", markdown)
        self.assertIn("## Coverage Summary", markdown)

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


if __name__ == "__main__":
    unittest.main()
