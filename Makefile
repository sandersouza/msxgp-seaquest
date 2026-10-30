.DEFAULT_GOAL := build
PYTHON ?= .venv/bin/python
.PHONY: environment environment-check environment-dry-run build run smoke test reference-check disassemble
environment:
	@bash scripts/setup.sh
environment-check:
	@bash scripts/setup.sh --check
environment-dry-run:
	@bash scripts/setup.sh --dry-run
build:
	@$(PYTHON) -B scripts/rom.py build
run: build
	@$(PYTHON) -B scripts/rom.py run
smoke: build
	@$(PYTHON) -B scripts/smoke.py
test:
	@$(PYTHON) -B -m unittest discover -s tests -v
reference-check:
	@$(PYTHON) -B scripts/reference_inventory.py
disassemble:
	@$(PYTHON) -B scripts/reference_rebuild.py
