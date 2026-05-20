from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.algotradeplan.data import DataHub
from src.algotradeplan.data.capabilities import canonical_dataset_name
from src.algotradeplan.strategies.catalog import strategy_summary


@dataclass(frozen=True)
class PreflightResult:
    can_run: bool
    source: str
    symbol: str
    strategy: str
    datasets: dict[str, str]
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    recommended_sources: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PreflightChecker:
    def __init__(self, hub: DataHub | None = None) -> None:
        self._hub = hub or DataHub()

    def check(
        self,
        *,
        source: str,
        symbol: str,
        datasets: list[str],
        strategy: str,
        allow_api_key: bool = True,
    ) -> PreflightResult:
        source_name = source.lower().strip()
        requested = [canonical_dataset_name(item) for item in datasets]
        dataset_statuses = {dataset: self._hub.dataset_status(source_name, dataset) for dataset in requested}
        summary = self._hub.source_summary(source_name)
        strategy_info = strategy_summary(strategy)

        blocking_issues: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []
        recommended_sources: list[dict[str, str]] = []

        required = {item.lower() for item in strategy_info["required_datasets"]}
        optional = {item.lower() for item in strategy_info["optional_datasets"]}
        requested_set = set(requested)
        missing_required = sorted(required - requested_set)
        if missing_required:
            blocking_issues.append(f"strategy requires datasets: {', '.join(missing_required)}")

        unknown_for_strategy = sorted(requested_set - required - optional)
        if unknown_for_strategy:
            warnings.append(f"strategy may ignore datasets: {', '.join(unknown_for_strategy)}")

        source_assets = {item.lower() for item in summary.get("asset_classes", [])}
        supported_assets = {item.lower() for item in strategy_info["supported_asset_classes"]}
        if source_assets and supported_assets and source_assets.isdisjoint(supported_assets):
            blocking_issues.append(
                f"strategy {strategy_info['strategy_id']} asset classes {sorted(supported_assets)} do not match source asset classes {sorted(source_assets)}"
            )

        notes_text = str(summary.get("notes") or "")
        for dataset, status in dataset_statuses.items():
            if status == "unsupported":
                blocking_issues.append(f"{dataset} unsupported by {source_name}")
                suggestions.extend(self._suggest_for_dataset(dataset, allow_api_key=allow_api_key))
                recommended_sources.extend(
                    self._hub.best_sources_for(
                        dataset=dataset,
                        allow_api_key=allow_api_key,
                        include_metadata_only=False,
                        limit=3,
                    )
                )
                continue
            if status == "metadata_only":
                blocking_issues.append(f"{dataset} is metadata_only for {source_name}")
            if status in {"api_key", "api_key_or_plan"} and not allow_api_key:
                env = self._hub.api_key_env(source_name)
                env_suffix = f" ({env})" if env else ""
                blocking_issues.append(f"{dataset} requires API key{env_suffix}")
            if status in {"partial", "fallback"}:
                warnings.append(f"{source_name} {dataset} status is {status}")

            extra_metadata = summary.get("extra_metadata", {}).get(dataset, {})
            if isinstance(extra_metadata, dict) and extra_metadata.get("synthetic_ohlcv"):
                warnings.append(f"{source_name} {dataset} is synthetic/derived OHLCV")
            if "synthetic" in notes_text.lower() and dataset == "kline":
                warnings.append(notes_text)

        dedup_suggestions = list(dict.fromkeys(suggestions))
        dedup_blocking = list(dict.fromkeys(blocking_issues))
        dedup_warnings = list(dict.fromkeys(warnings))
        dedup_recommended = self._dedup_recommended(recommended_sources)

        return PreflightResult(
            can_run=not dedup_blocking,
            source=source_name,
            symbol=symbol,
            strategy=strategy_info["strategy_id"],
            datasets=dataset_statuses,
            blocking_issues=dedup_blocking,
            warnings=dedup_warnings,
            suggestions=dedup_suggestions,
            recommended_sources=dedup_recommended,
        )

    def _suggest_for_dataset(self, dataset: str, *, allow_api_key: bool) -> list[str]:
        best = self._hub.best_sources_for(
            dataset=dataset,
            allow_api_key=allow_api_key,
            include_metadata_only=False,
            limit=3,
        )
        if not best:
            return [f"No current recommended source for dataset={dataset}"]
        return [f"Use {item['source']} for dataset={dataset} ({item['dataset_status']})" for item in best]

    @staticmethod
    def _dedup_recommended(items: list[dict[str, str]]) -> list[dict[str, str]]:
        deduped: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            key = (item.get("source", ""), item.get("dataset_status", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped
