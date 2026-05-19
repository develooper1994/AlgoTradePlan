# Usage with Jupyter Notebooks

1. Create environment and install project dependencies.
2. Start JupyterLab: `jupyter lab`
3. Open `notebooks/algotrade_e2e_demo.ipynb`
4. Run cells top-to-bottom:
   - baseline checks (`make lint`, `make test`, `make smoke`)
   - autonomous phase runner (`scripts/run_all_phases.py`)
   - real-data smoke pipeline (`scripts/e2e_real_data_smoke.py`)
   - report inspection from `artifacts/real_data_smoke_report.json`

The notebook uses real upstream APIs for discovery and data pulls (market, news,
macro). It does not use sample fixtures for the live smoke path.
