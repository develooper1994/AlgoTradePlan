"""Optional TEFAS adapter backed by external tefas-cli or FFI."""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable


OperationMap = dict[str, list[str]]

_DATASET_OPERATIONS: OperationMap = {
    "fund_nav": ["fonFiyatBilgiGetir"],
    "fund_profile": ["fonBilgiGetir", "fonProfilDtyGetir", "fonDetayGetir", "fundPageParse"],
    "fund_return": ["fonGetiriBazliBilgiGetir", "fonTurDnmGetiriGetir"],
    "fund_allocation": ["dagilimSiraliGetirT", "fundPageParse"],
    "fund_size": ["fonBuyuklukBazliBilgiGetir"],
    "fund_fee": ["fonYonetimBazliBilgiGetir"],
    "fund_announcement": ["fonTefasDuyuruGetir"],
    "fund_statistics": [
        "getFplFonList",
        "getFplFonBazliIslemHacmi",
        "getFplMkkStokBakiye",
        "getFplToplamIslemHacmi",
        "getFplUyeBazliIslemHacmi",
        "getBefasToplamIslemHacmi",
    ],
}


class TefasCliAdapter:
    source = "tefas_public"

    def __init__(self) -> None:
        self._ffi_query: Callable[[str, dict[str, Any]], Any] | None = self._load_ffi_query()

    def discover_assets(self, limit: int = 10, **filters: Any) -> list[str]:
        query = str(filters.get("query") or filters.get("keyword") or "").strip()
        if not self._is_fetch_available():
            return [query.upper()][:limit] if query else []
        payload = self._query_operation("fonUnvanAra", {"query": query, "limit": max(1, limit)})
        rows = self._rows(payload)
        codes: list[str] = []
        for row in rows:
            code = str(
                row.get("fonKodu")
                or row.get("fund_code")
                or row.get("kod")
                or row.get("symbol")
                or ""
            ).strip()
            if code:
                codes.append(code.upper())
        if not codes and query:
            codes.append(query.upper())
        return codes[:limit]

    def fetch_raw(
        self,
        symbol: str,
        datasets: list[str],
        *,
        timeframe: str = "1d",  # noqa: ARG002
        limit: int = 500,  # noqa: ARG002
    ) -> dict[str, Any]:
        normalized_symbol = str(symbol).strip().upper()
        if not self._is_fetch_available():
            return {
                "__issues__": {dataset: "optional_dependency_missing:tefas-cli" for dataset in datasets},
                "__suggestions__": {
                    "tefas_public": "Build tefas-cli and set TEFAS_CLI_BIN or TEFAS_FFI_LIB."
                },
            }

        result: dict[str, Any] = {}
        for dataset in datasets:
            operations = _DATASET_OPERATIONS.get(dataset, [])
            if not operations:
                continue
            responses: list[dict[str, Any]] = []
            for operation in operations:
                payload = self._query_operation(
                    operation,
                    {"symbol": normalized_symbol, "fund_code": normalized_symbol},
                )
                if payload is None:
                    continue
                responses.append({"operation": operation, "data": payload})
            if len(responses) == 1:
                result[dataset] = responses[0]["data"]
            elif responses:
                result[dataset] = responses
        return result

    def _is_fetch_available(self) -> bool:
        return bool(self._ffi_query or self._resolve_cli_bin())

    def _resolve_cli_bin(self) -> str | None:
        configured = str(os.getenv("TEFAS_CLI_BIN", "")).strip()
        if not configured:
            return None
        path = Path(configured)
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
        resolved = shutil.which(configured)
        return resolved if resolved else None

    def _query_operation(self, operation: str, params: dict[str, Any]) -> Any:
        if self._ffi_query is not None:
            ffi_payload = self._ffi_query(operation, params)
            if ffi_payload is not None:
                return ffi_payload
        return self._query_operation_via_cli(operation, params)

    def _query_operation_via_cli(self, operation: str, params: dict[str, Any]) -> Any:
        cli_bin = self._resolve_cli_bin()
        if not cli_bin:
            return None
        params_json = json.dumps(params, ensure_ascii=False)
        symbol = str(params.get("symbol") or params.get("fund_code") or "")
        variants: list[tuple[list[str], str | None]] = [
            ([cli_bin, "query", "--operation", operation, "--params", params_json, "--json"], None),
            ([cli_bin, "query-operation", operation, "--params", params_json, "--json"], None),
            ([cli_bin, "query", "--operation", operation, "--json"], params_json),
            ([cli_bin, "operation", operation, "--symbol", symbol, "--json"], None),
            ([cli_bin, "--operation", operation, "--symbol", symbol, "--json"], None),
            ([cli_bin, operation, "--symbol", symbol, "--json"], None),
        ]
        for command, stdin_payload in variants:
            completed = subprocess.run(
                command,
                input=stdin_payload,
                capture_output=True,
                text=True,
                check=False,
                timeout=25,
            )
            if completed.returncode != 0:
                continue
            decoded = _decode_json_output(completed.stdout)
            if decoded is not None:
                return decoded
        return None

    def _load_ffi_query(self) -> Callable[[str, dict[str, Any]], Any] | None:
        ffi_path = str(os.getenv("TEFAS_FFI_LIB", "")).strip()
        if not ffi_path:
            return None
        path = Path(ffi_path)
        if not path.exists():
            return None
        try:
            lib = ctypes.CDLL(str(path))
        except OSError:
            return None
        for function_name in ("tefas_query_operation_json", "query_operation_json"):
            query_func = getattr(lib, function_name, None)
            if query_func is None:
                continue
            query_func.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            query_func.restype = ctypes.c_char_p

            def _caller(operation: str, params: dict[str, Any], _func: Any = query_func) -> Any:
                payload = json.dumps(params, ensure_ascii=False).encode("utf-8")
                raw = _func(operation.encode("utf-8"), payload)
                if not raw:
                    return None
                text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
                return _decode_json_output(text)

            return _caller
        return None

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            for key in ("resultList", "rows", "data", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
            return [payload]
        return []


def _decode_json_output(text: str) -> Any:
    output = text.strip()
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        for line in reversed(output.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None
