from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.algotradeplan.data import DataHub
from src.algotradeplan.research import generate_data_health_report, write_data_health_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--datasets", nargs="+", required=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    source = "offline_fallback" if args.offline else args.source
    hub = DataHub()
    report = generate_data_health_report(
        hub=hub,
        source=source,
        symbol=args.symbol,
        datasets=args.datasets,
        allow_partial=args.allow_partial or args.offline,
    )
    path = write_data_health_markdown(report)
    payload = report.to_dict()
    payload["artifact_path"] = str(path)

    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(report.to_markdown())
    print(f"artifact_path: {path}")


if __name__ == "__main__":
    main()
