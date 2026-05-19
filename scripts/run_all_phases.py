"""Self-boot runner that executes all phase checkpoints without manual continue."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PhaseCommand:
    checkpoint: str
    command: list[str]


def _run_phase(command: PhaseCommand) -> dict[str, object]:
    completed = subprocess.run(command.command, check=False, text=True, capture_output=True)
    return {
        "checkpoint": command.checkpoint,
        "command": " ".join(command.command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "passed": completed.returncode == 0,
    }


def run_all_phases(*, include_live_smoke: bool, allow_partial: bool) -> list[dict[str, object]]:
    phases = [
        PhaseCommand("V0_bootstrap", ["make", "lint"]),
        PhaseCommand("V1_unit_and_adapter", ["make", "test"]),
        PhaseCommand("V2_smoke_terminal_notebook", ["make", "smoke"]),
        PhaseCommand("V3_runbook_guard", ["make", "runbook_check"]),
    ]
    if include_live_smoke:
        cmd = [sys.executable, "scripts/e2e_real_data_smoke.py"]
        if allow_partial:
            cmd.append("--allow-partial")
        phases.append(PhaseCommand("Vfinal_real_data_autopilot", cmd))

    results: list[dict[str, object]] = []
    for phase in phases:
        result = _run_phase(phase)
        results.append(result)
        if not result["passed"]:
            break
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-live-smoke", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--report-path", default="artifacts/run_all_phases_report.json")
    args = parser.parse_args()

    results = run_all_phases(
        include_live_smoke=args.include_live_smoke,
        allow_partial=args.allow_partial,
    )

    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")

    first_failure = next((result for result in results if not result["passed"]), None)
    if first_failure:
        raise SystemExit(
            f"run_all_phases_failed checkpoint={first_failure['checkpoint']} "
            f"command={first_failure['command']}"
        )

    print(f"run_all_phases_ok checkpoints={len(results)}")


if __name__ == "__main__":
    main()
