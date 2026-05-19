"""Deterministic structured logger with correlation id and PII safety."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

_SENSITIVE_KEYS = frozenset({"password", "token", "secret", "api_key", "authorization"})


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("***" if k.lower() in _SENSITIVE_KEYS else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


@dataclass(frozen=True)
class StructuredLogEntry:
    level: str
    event: str
    correlation_id: str
    fields: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "level": self.level,
                "event": self.event,
                "correlation_id": self.correlation_id,
                "fields": self.fields,
            },
            sort_keys=True,
        )


class StructuredLogger:
    """In-memory structured logger that redacts sensitive fields."""

    def __init__(self, correlation_id: str) -> None:
        self.correlation_id = correlation_id
        self.entries: list[StructuredLogEntry] = []

    def log(self, level: str, event: str, **fields: Any) -> StructuredLogEntry:
        safe_fields = _redact(fields)
        entry = StructuredLogEntry(
            level=level,
            event=event,
            correlation_id=self.correlation_id,
            fields=safe_fields,
        )
        self.entries.append(entry)
        return entry

    def info(self, event: str, **fields: Any) -> StructuredLogEntry:
        return self.log("info", event, **fields)

    def error(self, event: str, **fields: Any) -> StructuredLogEntry:
        return self.log("error", event, **fields)
