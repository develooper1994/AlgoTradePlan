from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.deploy_check import check_readiness, main


class DeployCheckTest(unittest.TestCase):
    def test_real_repo_passes_readiness_check(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        issues = check_readiness(repo_root)
        self.assertEqual(issues, [], msg=f"unexpected readiness issues: {issues}")

    def test_missing_files_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = check_readiness(Path(tmp))
        self.assertTrue(issues)
        self.assertTrue(any("missing required file" in issue for issue in issues))

    def test_cli_returns_zero_on_real_repo(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.assertEqual(main(["--repo-root", str(repo_root)]), 0)


if __name__ == "__main__":
    unittest.main()
