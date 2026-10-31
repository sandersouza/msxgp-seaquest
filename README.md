# Seaquest MSX1

Issue #15: [acceptance candidate and hardware procedure](docs/hardware-acceptance.md),
[observation record](docs/acceptance-observations.md). The frozen playable candidate
is 128 KiB ASCII16; physical acceptance and subjective sound remain pending.

Native Seaquest port targeting MSX1 with **64 KiB RAM, 16 KiB VRAM**, standard
Z80 and PSG, with no expansions. The Atari 2600 original is the gameplay authority.

Development is tracked in [MSX Game Ports](https://github.com/users/sandersouza/projects/7).
See the [roadmap](docs/superpowers/specs/2026-10-30-seaquest-msx1-design.md),
[reference inventory](docs/reference-inventory.md) and [local issue copies](.github/issues/).
The [reference disassembly](docs/reference-disassembly.md) documents byte-identical
rebuilds of both supplied binaries and hardware differences in the Atari 800 port.

Current integration runs original gameplay/HUD layout/backgrounds, refined MSX
score/OXYGEN lettering and ordered PSG sound. Build/run with `make presentation-run`;
original ROMs/source must be supplied locally and are not distributed here.
The [video timing policy](docs/video-frequency.md) preserves the measured NTSC4K
simulation speed on both 50 Hz and 60 Hz MSX1, with separately measured input
and presentation timing. Full-game release and physical-machine acceptance
remain in #15. The portable hardware diagnostic is also available.

See [development setup and commands](docs/development.md) to build/run the diagnostic.
See [delivery and CI conventions](docs/project-workflow.md) for automated checks and
the boundary between diagnostic, emulator and physical-machine acceptance.
The [original gameplay contract](docs/gameplay-contract.md) records source-derived
rules and the scenarios required for later runtime trace acceptance.
The [native gameplay contract](docs/native-core.md) passes independent original-CPU
comparisons, including continuous replay. The [SCREEN 2 feasibility gate](docs/renderer-feasibility.md)
records full-density renderer and native-core timing. The [original graphics
pipeline](docs/original-graphics.md) extracts and verifies source silhouettes,
surface/edge variants and lettering, with measured native sprite integration.
The [HUD/audio contract](docs/hud-audio.md) explains the MSX lettering adaptation,
palette/layout adaptation, PSG event fidelity and explicit timbre differences.
The [controls diagnostic](docs/input-controls.md) runs the original movement and
firing code with keyboard and both joystick ports, including measured input
latency. Build/run it locally with `make controls-run`; it acquires original raster
contacts and the logical oxygen alarm, with synthetic HUD/background colors.
The [score/progression contract](docs/scoring-progression.md) verifies original BCD,
reserve limits, late-game values, full bonuses and independent alternating players.

```sh
python3 -B scripts/reference_inventory.py
python3 -B -m unittest discover -s tests -v
python3 -B scripts/reference_rebuild.py  # requires the documented research tools
```
