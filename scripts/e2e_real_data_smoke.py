"""Run real-data E2E smoke for autonomous pipeline validation."""

from __future__ import annotations

import argparse
import pathlib
import sys
from pathlib import Path

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.orchestration.real_data_autopilot import (
    RealDataSmokeError,
    run_real_data_autopilot,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-path", default="artifacts/real_data_smoke_report.json")
    parser.add_argument("--max-symbols", type=int, default=5)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    report = run_real_data_autopilot(
        report_path=Path(args.report_path),
        max_symbols_per_source=max(1, args.max_symbols),
        allow_partial=args.allow_partial,
    )

    print(
        "real_data_smoke_ok "
        f"market_sources={len(report.market_sources)} "
        f"news_story_count={report.news_story_count} "
        f"macro_series_count={report.macro_series_count} "
        f"signal={report.intent.get('action')}"
    )


if __name__ == "__main__":
    try:
        main()
    except RealDataSmokeError as exc:
        raise SystemExit(f"real_data_smoke_failed: {exc}")
