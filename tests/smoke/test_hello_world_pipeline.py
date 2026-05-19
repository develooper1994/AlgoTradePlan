from __future__ import annotations

import subprocess
import sys
import unittest


class HelloWorldSmokeTest(unittest.TestCase):
    def test_terminal_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/hello_world_e2e.py", "--mode", "terminal", "--dry-run"],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("hello_world_e2e_ok", completed.stdout)

    def test_notebook_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/hello_world_e2e.py", "--mode", "notebook", "--dry-run"],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("hello_world_e2e_ok", completed.stdout)

    def test_notebook_workflow_structure_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/notebook_smoke_check.py"],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("notebook_smoke_ok", completed.stdout)


if __name__ == "__main__":
    unittest.main()
