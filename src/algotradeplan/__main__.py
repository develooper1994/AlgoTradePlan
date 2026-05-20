"""Entry point for ``python -m algotradeplan``."""
from __future__ import annotations

import sys

try:
    from algotradeplan.cli import main
except ImportError:
    from src.algotradeplan.cli import main  # type: ignore[no-redef]

sys.exit(main())
