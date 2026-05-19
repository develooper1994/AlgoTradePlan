PYTHON ?= python

.PHONY: bootstrap lint test smoke smoke_real autopilot docs onboarding runbook_check

bootstrap:
	bash scripts/bootstrap.sh

lint:
	$(PYTHON) -m compileall src tests scripts

test:
	$(PYTHON) scripts/run_tests.py

smoke:
	$(PYTHON) scripts/hello_world_e2e.py --mode terminal --dry-run

smoke_real:
	$(PYTHON) scripts/e2e_real_data_smoke.py

autopilot:
	$(PYTHON) scripts/run_all_phases.py --include-live-smoke

onboarding:
	@echo "See ONBOARDING.md and docs/onboarding_10min.md"
	@echo "Recommended flow: make bootstrap && make lint && make test && make smoke && make runbook_check"
	@echo "Autonomous run: python scripts/run_all_phases.py --include-live-smoke"

runbook_check:
	test -f docs/runbook_masterlist.md || { echo "Error: docs/runbook_masterlist.md not found. Please create it or verify docs layout."; exit 1; }
	test -f docs/runbooks/README.md || { echo "Error: docs/runbooks/README.md not found. Please create it or verify docs layout."; exit 1; }
	@echo "runbook_check_ok"

docs:
	@echo "Use mkdocs serve/build when mkdocs is installed"
