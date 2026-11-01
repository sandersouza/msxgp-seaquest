.DEFAULT_GOAL := build
PYTHON ?= .venv/bin/python
FORMAT ?= rom
MACHINE ?= C-BIOS_MSX1
DOS_DISK ?=
.PHONY: environment environment-check environment-dry-run build run smoke test reference-check reference-trace-check native-contract render-bench render-native-bench graphics graphics-reference-check render-graphics-bench render-input-bench controls controls-run input-contract input-natural disassemble
.PHONY: progression-contract render-progression-bench progression-natural
.PHONY: presentation presentation-run presentation-check presentation-natural
.PHONY: video-build video-check
.PHONY: acceptance-check
.PHONY: disk-build plain32-build
.PHONY: diagnostic-build diagnostic-run
disk-build plain32-build:
	@$(PYTHON) -B scripts/build_disk.py
environment:
	@bash scripts/setup.sh
environment-check:
	@bash scripts/setup.sh --check
environment-dry-run:
	@bash scripts/setup.sh --dry-run
build:
	@$(PYTHON) -B scripts/play.py build --format "$(FORMAT)"
run: build
	@$(PYTHON) -B scripts/play.py run --format "$(FORMAT)" --machine "$(MACHINE)" --disk "$(DOS_DISK)"
diagnostic-build:
	@$(PYTHON) -B scripts/rom.py build
diagnostic-run: diagnostic-build
	@$(PYTHON) -B scripts/rom.py run
smoke: diagnostic-build
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
progression-contract:
	@$(PYTHON) -B scripts/progression_contract.py
render-progression-bench:
	@$(PYTHON) -B scripts/render_bench.py --progression
progression-natural: input-contract
	@$(PYTHON) -B scripts/input_natural.py --progression
presentation:
	@$(PYTHON) -B scripts/render_bench.py --palette --controls --build-only
presentation-run: presentation
	@openmsx -machine C-BIOS_MSX1 -cart outputs/render/presentation-controls.rom -romtype ASCII16
presentation-check: presentation-natural
	@$(PYTHON) -B scripts/render_bench.py --palette --progression
	@$(PYTHON) -B scripts/presentation_sweep.py
	@$(PYTHON) -B scripts/presentation_attract.py
	@$(PYTHON) -B scripts/presentation_attract.py --force-generation-wrap
	@$(PYTHON) -B scripts/presentation_attract.py --ready-generation-wrap
	@$(PYTHON) -B scripts/audio_contract.py
presentation-natural: presentation
	@$(PYTHON) -B scripts/input_natural.py --audio --progression
video-build:
	@$(PYTHON) -B scripts/video_check.py --build-only
acceptance-check:
	@$(PYTHON) -B scripts/full_game_check.py
video-check:
	@$(MAKE) presentation-check
	@$(MAKE) video-build
	@$(PYTHON) -B scripts/video_reference.py
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1_EU
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1_EU --scenario burst --frames 112
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1_EU --generation wrap
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1_EU --generation ready
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1_EU --scenario dense
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1_EU --scenario cold --frames 1200
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1 --scenario dense
	@$(PYTHON) -B scripts/video_check.py --machine C-BIOS_MSX1 --scenario cold --frames 1200
disassemble:
	@$(PYTHON) -B scripts/reference_rebuild.py
