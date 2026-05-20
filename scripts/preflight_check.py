from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub
from src.algotradeplan.research import PreflightChecker


def _render_markdown(result: dict[str, object]) -> str:
    return (
        "# Preflight Check\n\n"
        f"- can_run: `{result['can_run']}`\n"
        f"- source: `{result['source']}`\n"
        f"- symbol: `{result['symbol']}`\n"
        f"- strategy: `{result['strategy']}`\n"
        f"- datasets: `{result['datasets']}`\n\n"
        "## Blocking issues\n\n"
        f"`{result['blocking_issues']}`\n\n"
        "## Warnings\n\n"
        f"`{result['warnings']}`\n\n"
        "## Suggestions\n\n"
        f"`{result['suggestions']}`\n\n"
        "## Recommended sources\n\n"
        f"`{result['recommended_sources']}`\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--datasets", nargs="+", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--allow-api-key", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checker = PreflightChecker(DataHub())
    result = checker.check(
        source=args.source,
        symbol=args.symbol,
        datasets=args.datasets,
        strategy=args.strategy,
        allow_api_key=args.allow_api_key,
    ).to_dict()
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(_render_markdown(result))


if __name__ == "__main__":
    main()
