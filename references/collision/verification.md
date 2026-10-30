# Issue #10 verification

Local platform: macOS ARM, Python3.14.7, ALE0.12.1 (Stella), py65 1.2.0,
openMSX21.0, C-BIOS_MSX1 NTSC, standard3,579,545Hz Z80,64 KiB RAM/16 KiB VRAM,
plain32 KiB cartridge. Original SHA-256 and pinned sjasmplus revision are recorded
in render-result.json. All outputs are diagnostics; full gameplay, HUD/audio,
PAL, host input latency, visible scanout and physical MSX are not accepted here.

| Command | Evidence / outcome |
|---|---|
| `make collision-contract` | contract-result.json;40,748 acquisition/resolution cases,20,374 original TIA scenarios;256 phases/waves/seeds and 96 legal Y values |
| `make render-collision-bench` | render-result.json;10,622 pixel/state/timing cases and240 paced frames;59,370/59,736 cycles |
| `make input-natural` | input-regression.json and natural-result.json;5,660 actual-device cases and659 continuous cold-boot updates; no RAM reloads/skips |
| `make native-contract` | native-regression.json;2,707 independent original CPU cases |
| `make render-graphics-bench` | graphics-regression.json;6,526 cases,52,134 cycles maximum |
| `make render-input-bench` | neutral-input-render-regression.json;9,598 isolated adapter cases,58,757 cycles maximum |
| `scripts/graphics_reference.py` | graphics-reference.json;647 source-shape scenarios and299 edge cases |
| `make test` / `bash scripts/ci.sh` |36 host tests pass; diagnostic, synthetic renderer/input and synthetic collision assemblies pass |
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

The timed probe is 0990365dec54574eb3a17ead3838dd8d064a1d4049052e5c957211bb55ab14f2;
the cold-boot diagnostic is c6fd8c4271d160527ed6e0e3f5459f4eda1fbaa56e66a55d8eb28989da411dee.
See docs/collision-contract.md for phase, geometry, limits and reproduction.
