# Issue #10 verification

Local platform: macOS ARM, Python3.14.7, ALE0.12.1 (Stella), py65 1.2.0,
openMSX21.0, C-BIOS_MSX1 NTSC, standard3,579,545Hz Z80,64KiB RAM/16KiB VRAM,
plain32KiB cartridge. Original SHA-256 and pinned sjasmplus revision are recorded
in render-result.json. All outputs are diagnostics; full gameplay, HUD/audio,
PAL, host input latency, visible scanout and physical MSX are not accepted here.

| Command | Evidence / outcome |
|---|---|
| `make collision-contract` | contract-result.json;34,148 acquisition/resolution cases,17,074 original TIA scenarios;256 phases/waves/seeds and96 legal Y values |
| `make render-collision-bench` | render-result.json;10,622 pixel/state/timing cases and240 paced frames;59,087/59,736 cycles |
| `make input-natural` | input-regression.json and natural-result.json;5,660 actual-device cases and659 continuous cold-boot updates; no RAM reloads/skips |
| `make native-contract` | native-regression.json;2,707 independent original CPU cases |
| `make render-graphics-bench` | graphics-regression.json;6,526 cases,52,104 cycles maximum |
| `make render-input-bench` | neutral-input-render-regression.json;9,598 isolated adapter cases,58,727 cycles maximum |
| `scripts/graphics_reference.py` | graphics-reference.json;500 source-shape scenarios and299 edge cases |
| `make test` / `bash scripts/ci.sh` |35 host tests pass; diagnostic, synthetic renderer/input and synthetic collision assemblies pass |
| `SEAQUEST_COLLISION_CORRUPT=1 make collision-contract` | negative-control.json; rejected first acquisition at B6/C0B6, expected255/actual254; subsequent normal contract passes |

Contact-combination bits in contract-result.json correspond to any enemy/ball,
missile/enemy, player/enemy, player/ball and patrol. Explicit simultaneous cases
include normal/hostile balls, both facings, all lanes and zero/six divers aboard.
Patrol cases exercise normal/refill/bonus resolution. Guarded contract and paced
runs retain stack minimum F370 and an intact D000..F2FF guard.

Raw local evidence remains ignored: outputs/collision/cases.bin and case-index.json,
outputs/render/cases.bin, state.bin, vram.bin and prepared.bin, plus
outputs/input/natural.bin and natural-timing.jsonl. Original-derived art/tables,
ROMs, listings and emulator replays must not be published as CI artifacts.

The timed probe is055fb51c9a12993140838ca04a1a0980098eca6e57dcd3c5d9f441b66cd823ff;
the cold-boot diagnostic is3f2a05b3d5810d1d74a8753155dfefc69aac3e744e9b0777319c1be2e24750b5.
See docs/collision-contract.md for phase, geometry, limits and reproduction.
