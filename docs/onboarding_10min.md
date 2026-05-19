# Onboarding in 10 Minutes

1. `make bootstrap`
2. `make lint`
3. `make test`
4. `make smoke`
5. `make runbook_check`
6. Open `notebooks/algotrade_e2e_demo.ipynb`
7. Run `python scripts/hello_world_e2e.py --mode terminal --dry-run`
8. Run `python scripts/run_all_phases.py --include-live-smoke`

If failures occur, run with `--debug` and check redacted logs under `artifacts/`.

Then read:
- `ONBOARDING.md`
- `docs/PHASE_RECAP.md`
