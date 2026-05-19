# Quickstart

## Terminal
```bash
bash scripts/bootstrap.sh
make lint
make test
python scripts/hello_world_e2e.py --mode terminal --dry-run
make runbook_check
python scripts/run_all_phases.py --include-live-smoke
```

## Notebook
Open `notebooks/algotrade_e2e_demo.ipynb` and run cells sequentially.
