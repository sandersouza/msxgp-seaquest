# Development environment

Target: MSX1 with **64 KiB RAM, 16 KiB VRAM**, TMS9918-family VDP, standard Z80
and PSG. No disk drive, RAM expansion, turbo or extra sound hardware is required.

## macOS setup

Install Xcode Command Line Tools and Homebrew first. Then:

```sh
make environment-dry-run
make environment
make environment-check
make build
make test
make smoke
make run
```

Setup supports macOS ARM and Intel. ARM was exercised here; Intel is prepared
but remains **untested**. Other operating systems fail explicitly. The setup uses
Homebrew for missing openMSX/Stella/DASM, creates `.venv` only if absent, and builds
pinned local sjasmplus and DiStella under ignored `.tools`. It verifies the pinned
MADS download by SHA-256 before execution. It does not replace an existing venv,
reset existing tool checkouts or touch reference ROMs. If an existing tool differs,
repair it explicitly or preserve/move it aside before rerunning setup.

Python >=3.11 is required; the tested interpreter is Homebrew Python 3.14.7.
All project scripts use the standard library; no game-analysis dependencies are
needed yet. New venvs receive current pip/setuptools/wheel. Existing environments
are checked rather than upgraded implicitly. Homebrew packages may vary with its
catalogue; pinned assembler revisions and reference byte-identity checks establish
the reproducible binary boundary, not a claim of fully locked host software.

`--check` and `--dry-run` do not install tools or create project environments.
`--check` reports missing/incorrect dependencies with failure status; `--dry-run`
describes the preparation steps without applying changes.

## Commands and files

| Command | Result |
|---|---|
| `make build` | `outputs/seaquest-diagnostic.rom` and hash manifest |
| `make run` | build and open the diagnostic on C-BIOS_MSX1 |
| `make smoke` | bounded headless C-BIOS_MSX1 boot, `outputs/smoke-result.json` |
| `make test` | synthetic unit tests, no original ROM inputs needed |
| `make reference-check` | verify all local originals against the immutable manifest |
| `make disassemble` | byte-identical local reference rebuilds and address metadata |

Use `PYTHON=/path/to/python` with make to override the local venv interpreter.
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
No original-BIOS matrix, visual gameplay, PAL behavior, performance benchmark or
physical-machine acceptance is implied. These are later issue deliverables.
