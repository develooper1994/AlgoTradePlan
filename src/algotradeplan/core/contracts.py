"""Core protocols and contracts."""

from __future__ import annotations

from typing import Protocol


class Clock(Protocol):
    def now_iso(self) -> str:
        """Return current UTC timestamp as ISO string."""
