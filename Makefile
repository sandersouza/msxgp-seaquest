.DEFAULT_GOAL := build
PYTHON ?= .venv/bin/python
.PHONY: environment environment-check environment-dry-run build run smoke test reference-check reference-trace-check native-contract render-bench render-native-bench graphics graphics-reference-check render-graphics-bench disassemble
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
reference-trace-check:
	@$(PYTHON) -B scripts/verify_reference_trace.py
native-contract:
	@$(PYTHON) -B scripts/native_contract.py
render-bench:
	@$(PYTHON) -B scripts/render_bench.py
render-native-bench:
	@$(PYTHON) -B scripts/render_bench.py --native
graphics:
	@$(PYTHON) -B scripts/original_graphics.py
graphics-reference-check: graphics
	@$(PYTHON) -B scripts/graphics_reference.py
render-graphics-bench:
	@$(PYTHON) -B scripts/render_bench.py --graphics
disassemble:
	@$(PYTHON) -B scripts/reference_rebuild.py
