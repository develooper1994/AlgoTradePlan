"""Deterministic id utilities."""

from __future__ import annotations

import hashlib


def make_stable_id(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
