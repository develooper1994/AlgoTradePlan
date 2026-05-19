from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.security_check import check_policy, main


class SecurityCheckTest(unittest.TestCase):
    def test_real_repo_passes_policy(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        issues = check_policy(repo_root)
        self.assertEqual(issues, [], msg=f"unexpected policy issues: {issues}")

    def test_missing_pyproject_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = check_policy(Path(tmp))
        self.assertIn("pyproject.toml not found", issues)

    def test_cli_returns_zero_on_real_repo(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.assertEqual(main(["--repo-root", str(repo_root)]), 0)


if __name__ == "__main__":
    unittest.main()
