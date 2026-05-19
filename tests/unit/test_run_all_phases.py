from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "run_all_phases.py"
    spec = importlib.util.spec_from_file_location("run_all_phases", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RunAllPhasesScriptTest(unittest.TestCase):
    def test_run_all_phases_stops_after_failure(self) -> None:
        module = _load_module()

        class _Result:
            def __init__(self, returncode: int):
                self.returncode = returncode
                self.stdout = "ok"
                self.stderr = ""

        sequence = [_Result(0), _Result(1), _Result(0)]

        with patch.object(module.subprocess, "run", side_effect=sequence) as mocked_run:
            results = module.run_all_phases(include_live_smoke=False, allow_partial=False)

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])
        self.assertEqual(mocked_run.call_count, 2)

    def test_main_writes_report(self) -> None:
        module = _load_module()

        class _Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "phases.json"
            argv = [
                "run_all_phases.py",
                "--report-path",
                str(report_path),
            ]
            with patch.object(module.subprocess, "run", return_value=_Result()):
                with patch.object(module.sys, "argv", argv):
                    module.main()

            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()
