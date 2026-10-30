.DEFAULT_GOAL := build
PYTHON ?= .venv/bin/python
.PHONY: environment environment-check environment-dry-run build run smoke test reference-check reference-trace-check native-contract render-bench render-native-bench graphics graphics-reference-check render-graphics-bench render-input-bench controls controls-run input-contract input-natural disassemble
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
render-input-bench:
	@$(PYTHON) -B scripts/render_bench.py --input
controls:
	@$(PYTHON) -B scripts/render_bench.py --controls --collisions --build-only
controls-run: controls
	@openmsx -machine C-BIOS_MSX1 -cart outputs/render/controls.rom
input-contract:
	@$(PYTHON) -B scripts/input_contract.py
input-natural: input-contract
	@$(PYTHON) -B scripts/input_natural.py
collision-contract:
	@$(PYTHON) -B scripts/collision_contract.py
render-collision-bench:
	@$(PYTHON) -B scripts/render_bench.py --collisions
oxygen-contract:
	@$(PYTHON) -B scripts/oxygen_contract.py
render-oxygen-bench:
	@$(PYTHON) -B scripts/render_bench.py --oxygen
oxygen-natural: input-contract
	@$(PYTHON) -B scripts/input_natural.py --rescue
disassemble:
	@$(PYTHON) -B scripts/reference_rebuild.py
