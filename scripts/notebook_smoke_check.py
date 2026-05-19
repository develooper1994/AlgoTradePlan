"""Smoke checks for notebook onboarding workflow coverage."""

from __future__ import annotations

import json
from pathlib import Path


def _load_notebook(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - CLI smoke guard
        raise SystemExit(f"Notebook not found at {path}.") from exc


def _joined_sources(cells: list[dict[str, object]], cell_type: str) -> str:
    joined: list[str] = []
    for cell in cells:
        if cell.get("cell_type") != cell_type:
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            joined.append("".join(str(part) for part in source))
        else:
            joined.append(str(source))
    return "\n".join(joined)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    notebook_expectations = {
        "01_real_data_smoke.ipynb": {
            "markdown": ["DataHub", "coverage table", "source issues"],
            "code": [
                "from algotradeplan.data import DataHub",
                "coverage_table(",
                "discover_assets(",
                "ingest(",
            ],
        },
        "02_strategy_backtest_portfolio.ipynb": {
            "markdown": ["ETL", "signal -> intent -> risk -> execution -> portfolio", "ledger"],
            "code": [
                "from algotradeplan.data import ETL",
                "load_market_data(",
                "TradeFlow",
                "PortfolioManager",
            ],
        },
        "03_multi_source_asset_coverage.ipynb": {
            "markdown": ["multi-source", "coverage", "unsupported dataset"],
            "code": [
                "coverage_table(",
                "sources()",
                "unsupported",
                "allow_partial=True",
            ],
        },
    }

    for notebook_name, expectation in notebook_expectations.items():
        notebook = _load_notebook(repo_root / "notebooks" / notebook_name)
        cells = notebook.get("cells")
        if not isinstance(cells, list) or not cells:
            raise SystemExit(f"Notebook validation failed: No cells found in {notebook_name}.")
        markdown_text = _joined_sources(cells, "markdown")
        code_text = _joined_sources(cells, "code")
        missing_markdown_sections = [token for token in expectation["markdown"] if token not in markdown_text]
        missing_code_tokens = [token for token in expectation["code"] if token not in code_text]
        if missing_markdown_sections or missing_code_tokens:
            raise SystemExit(
                f"{notebook_name} missing required coverage: "
                f"markdown={missing_markdown_sections} code={missing_code_tokens}"
            )

    docs_path = repo_root / "docs" / "usage_with_notebooks.md"
    onboarding_path = repo_root / "ONBOARDING.md"
    onboarding_10min_path = repo_root / "docs" / "onboarding_10min.md"
    readme_path = repo_root / "README.md"

    docs_text = docs_path.read_text(encoding="utf-8")
    onboarding_text = onboarding_path.read_text(encoding="utf-8")
    onboarding_10min_text = onboarding_10min_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")
    for notebook_name in notebook_expectations:
        notebook_ref = f"notebooks/{notebook_name}"
        if notebook_ref not in docs_text:
            raise SystemExit(f"usage_with_notebooks.md must reference {notebook_ref}")
        if notebook_ref not in readme_text:
            raise SystemExit(f"README.md must reference {notebook_ref}")
    if "docs/usage_with_notebooks.md" not in onboarding_text:
        raise SystemExit("ONBOARDING.md must reference docs/usage_with_notebooks.md")
    if "docs/usage_with_notebooks.md" not in onboarding_10min_text:
        raise SystemExit("docs/onboarding_10min.md must reference docs/usage_with_notebooks.md")
    if "docs/usage_with_notebooks.md" not in readme_text:
        raise SystemExit("README.md must reference docs/usage_with_notebooks.md")

    print("notebook_smoke_ok")


if __name__ == "__main__":
    main()
