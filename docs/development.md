# Development environment

Target: MSX1 with **64 KiB RAM, 16 KiB VRAM**, TMS9918-family VDP, standard Z80
and PSG. No disk drive, RAM expansion, turbo or extra sound hardware is required.

## macOS setup

Install Xcode Command Line Tools and Homebrew first. Then:

```sh
make environment-dry-run
make environment
make environment-check
make diagnostic-build
make test
make smoke
make diagnostic-run
```

Setup supports macOS ARM and Intel. ARM was exercised here; Intel is prepared
but remains **untested**. Other operating systems fail explicitly. The setup uses
Homebrew for missing openMSX/Stella/DASM, creates `.venv` only if absent, and builds
pinned local sjasmplus and DiStella under ignored `.tools`. It verifies the pinned
MADS download by SHA-256 before execution. It does not replace an existing venv,
reset existing tool checkouts or touch reference ROMs. If an existing tool differs,
repair it explicitly or preserve/move it aside before rerunning setup.

Python >=3.11 is required; the tested interpreter is Homebrew Python 3.14.7.
Base build/check scripts use the standard library. The optional reference capture
adds the pinned backend from `requirements-reference.txt`; see
[reference traces](reference-traces.md). New venvs receive current pip/setuptools/wheel. Existing environments
are checked rather than upgraded implicitly. Homebrew packages may vary with its
catalogue; pinned assembler revisions and reference byte-identity checks establish
the reproducible binary boundary, not a claim of fully locked host software.

`--check` and `--dry-run` do not install tools or create project environments.
`--check` reports missing/incorrect dependencies with failure status; `--dry-run`
describes the preparation steps without applying changes.

## Commands and files

| Command | Result |
|---|---|
| `make build` / `make` | complete game: `outputs/disk/SEAQUEST32.ROM`, 32 KiB Normal |
| `make run` | build and open the game on C-BIOS_MSX1; `MACHINE=C-BIOS_MSX1_EU` for PAL |
| `make build FORMAT=com` | native MSX-DOS 1 executable: `outputs/disk/SEAQUEST.COM` |
| `make run FORMAT=com MACHINE=my_msx1_disk DOS_DISK=/path/to/dos1.dsk` | boot a temporary DOS1 disk copy with the current COM; requires your BIOS/system disk |
| `make diagnostic-build` / `make diagnostic-run` | build / open the separate synthetic hardware diagnostic |
| `make smoke` | bounded headless C-BIOS_MSX1 boot, `outputs/smoke-result.json` |
| `make test` | synthetic unit tests, no original ROM inputs needed |
| `make reference-check` | verify all local originals against the immutable manifest |
| `make disassemble` | byte-identical local reference rebuilds and address metadata |
| `make render-bench` | synthetic renderer pixel/SAT/timing checks on openMSX |
| `make render-native-bench` | local original/native state plus renderer feasibility checks |
| `make controls-run` | continuous original input/collision integration diagnostic |
| `make collision-contract` | original TIA occupancy, Z80 acquisition and ordered resolution |
| `make render-collision-bench` | full-density collision/input/graphics timing and VRAM checks |
| `make progression-contract` | original score registers/BCD, lives, late-game and player-state comparisons |
| `make render-progression-bench` | combined oxygen/progression/graphics density, pixels and frame timing |
| `make progression-natural` | device-only alternating-player exhaustion, game over and restart |
| `make presentation-run` | original HUD/background/PSG integration,64KiB ASCII16 in openMSX |
| `make presentation-check` | integrated timing/pixels plus font/palette/water and ordered sound checks |
| `make presentation-natural` | cold device-only replay, original CPU/TIA and every sound store |

Use `PYTHON=/path/to/python` with make to override the local venv interpreter.
Game builds require the documented local original inputs and reference
dependencies; see [native build and launch instructions](native-delivery.md).
The synthetic diagnostic, host tests and CI do not require those inputs.
`references/tools-lock.json` pins reference research tools; sjasmplus is pinned to
v1.24.0 commit `d379eeac9ad3857fb48fd3a3929175d0a56038ce`, built with `USE_LUA=0`.
Generated outputs are ignored. Keep source files under `src/`, tests under `tests/`
and tooling under `scripts/`; create core/video/audio modules as their issues start.

## Diagnostic acceptance

This cartridge is **not Seaquest gameplay**. It enters SCREEN 2 through the BIOS,
initializes pattern/color/name tables and writes the `$5351` boot signature at
`$C000/$C001`. `$C002` advances on BIOS interrupts. It uses a conventional stack
below BIOS workspace at `$F380` and does not install custom interrupt hooks.

`make smoke` starts its own openMSX process, explicitly powers it on, and checks
the signature, VRAM pattern/color/name bytes and interrupt advancement. It requires
a fresh pass record and kills only its own process on timeout. It does not interact
with other openMSX sessions. The selected C-BIOS_MSX1 machine has a TMS9918A,
64 KiB RAM, 16 KiB VRAM and 60 Hz interrupts, with a plain 32 KiB cartridge.

On macOS ARM / openMSX 21.0, diagnostic ROM SHA-256
`62131a8d9f569d2799445d94e898df09004797ed292bf12f1b924d0754497791`
passed this automated boot check. Snapshot: `references/msx1-smoke.json`.
No original-BIOS matrix, visual gameplay, PAL behavior or physical-machine
acceptance is implied. The separate [renderer feasibility benchmark](renderer-feasibility.md)
records its own performance evidence and limitations.

Local original graphics research uses `make graphics-reference-check` (source
extraction plus ALE pixels) and `make render-graphics-bench` (native core plus
original sprites in openMSX). See [the graphics contract](original-graphics.md)
for palette, clipping, exact evidence and tight CPU/ROM constraints. These targets
require the verified local original ROM and never run or upload art in public CI.
The [collision contract](collision-contract.md) describes the current integrated
hardware phase and its independent Atari/openMSX checks.
