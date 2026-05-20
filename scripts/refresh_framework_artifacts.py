from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _run_step(command: list[str]) -> tuple[bool, str]:
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-live", action="store_true")
    args = parser.parse_args()

    steps: list[tuple[str, list[str], bool]] = [
        ("coverage_and_recommendations_doc", [sys.executable, "scripts/generate_data_coverage_doc.py"], True),
        ("tutorial_walkthrough", [sys.executable, "scripts/tutorial_mode.py", "--all", "--offline", "--write-doc"], True),
        ("framework_status", [sys.executable, "scripts/framework_status.py", "--write-doc", "--write-plan"], True),
        (
            "offline_data_health",
            [
                sys.executable,
                "scripts/data_health_report.py",
                "--source",
                "offline_fallback",
                "--symbol",
                "BTCUSDT",
                "--datasets",
                "kline",
                "funding",
                "--offline",
                "--json",
            ],
            True,
        ),
        (
            "offline_experiment_demo",
            [
                sys.executable,
                "scripts/run_experiment.py",
                "--source",
                "offline_fallback",
                "--symbol",
                "BTCUSDT",
                "--strategy",
                "ema_cross_atr_stop",
                "--offline",
                "--json",
            ],
            True,
        ),
        (
            "recipe_dry_run",
            [sys.executable, "scripts/run_recipe.py", "recipes/crypto_momentum.yaml", "--dry-run", "--json"],
            True,
        ),
    ]
    if not args.skip_live:
        steps.append(
            (
                "real_data_smoke",
                [sys.executable, "scripts/e2e_real_data_smoke.py", "--interactive", "--allow-partial"],
                False,
            )
        )

    has_failure = False
    for name, command, required in steps:
        ok, output = _run_step(command)
        status = "ok" if ok else "failed"
        print(f"refresh_step:{name}:{status}")
        if output:
            print(output)
        if not ok and not required:
            has_failure = True
            print("live_smoke_failed: non-live artifacts were still refreshed. Re-run with --skip-live in CI/offline environments.")
        if not ok and required:
            raise SystemExit(f"refresh_failed:{name}")

    if has_failure:
        raise SystemExit("refresh_completed_with_live_failure")


if __name__ == "__main__":
    main()
