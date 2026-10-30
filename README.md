# Seaquest MSX1

Native Seaquest port targeting MSX1 with **64 KiB RAM, 16 KiB VRAM**, standard
Z80 and PSG, with no expansions. The Atari 2600 original is the gameplay authority.

Development is tracked in [MSX Game Ports](https://github.com/users/sandersouza/projects/7).
See the [roadmap](docs/superpowers/specs/2026-10-30-seaquest-msx1-design.md),
[reference inventory](docs/reference-inventory.md) and [local issue copies](.github/issues/).
The [reference disassembly](docs/reference-disassembly.md) documents byte-identical
rebuilds of both supplied binaries and hardware differences in the Atari 800 port.

Current delivery: verified references, byte-identical research rebuilds, a macOS
toolchain and a bootable MSX1 hardware diagnostic. A playable Seaquest ROM is not
available yet. Original ROMs/source must be supplied locally; they are not distributed here.

See [development setup and commands](docs/development.md) to build/run the diagnostic.
See [delivery and CI conventions](docs/project-workflow.md) for automated checks and
the boundary between diagnostic, emulator and physical-machine acceptance.
The [original gameplay contract](docs/gameplay-contract.md) records source-derived
rules and the scenarios required for later runtime trace acceptance.
The [native gameplay contract](docs/native-core.md) passes independent original-CPU
comparisons, including continuous replay. The [SCREEN 2 feasibility gate](docs/renderer-feasibility.md)
records full-density renderer and native-core timing; complete assets and playable
integration remain subsequent work.

```sh
python3 -B scripts/reference_inventory.py
python3 -B -m unittest discover -s tests -v
python3 -B scripts/reference_rebuild.py  # requires the documented research tools
```
