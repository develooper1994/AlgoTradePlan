PYTHON ?= python

.PHONY: bootstrap lint test smoke docs

bootstrap:
	bash scripts/bootstrap.sh

lint:
	$(PYTHON) -m compileall src tests scripts

test:
	$(PYTHON) scripts/run_tests.py

smoke:
	$(PYTHON) scripts/hello_world_e2e.py --mode terminal --dry-run

docs:
	@echo "Use mkdocs serve/build when mkdocs is installed"
