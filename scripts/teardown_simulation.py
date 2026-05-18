"""Clean local simulation artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    for path in (Path("artifacts"), Path("logs"), Path("data")):
        if path.exists():
            shutil.rmtree(path)
    print("Simulation teardown complete")


if __name__ == "__main__":
    main()
