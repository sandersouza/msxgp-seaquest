## Goal
Compare hardware sprites and hybrid tile/sprite rendering using the original's densest scenes, repeated enemies, crossing player, diver/shot lanes, surface patrol and HUD.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #2: Reconstruct Atari 2600 disassembly and map differences in the Atari 800 port
- #4: Bootstrap reproducible macOS toolchain and MSX1 ROM scaffold

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Record cycles, VRAM timing, scanline sprite occupancy, RAM use and frame pacing on standard MSX1. No enemy-count reduction, slower simulation or invisible collidable objects. Document the measured rendering choice and unresolved fidelity tradeoffs.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Verification and delivery

- Delivery PR: https://github.com/sandersouza/msxgp-seaquest/pull/23.
- [Measured renderer decision](https://github.com/sandersouza/msxgp-seaquest/blob/main/docs/renderer-feasibility.md): 240px hybrid SCREEN 2; twelve background enemies plus eight hardware sprites, at most four per scanline. Patrol bottom alignment preserves original raster position while avoiding the first diver lane.
- [Exact evidence](https://github.com/sandersouza/msxgp-seaquest/tree/main/references/renderer): 4,238 native/reference RAM and original-enemy pixel comparisons, maximum 54,179 cycles of 59,736; 240 paced frames without skips; minimum VRAM data spacing29 cycles; RAM guard and stack high-water record.
- Synthetic256 cases, 20 host tests, original/native2,707-case regression, intentional pixel corruption detection, and local synthetic CI pass. Fresh independent review completed; accumulator-marshalling finding fixed and verified.
- Original sprite/HUD artwork, palette/edge variants, full gameplay, input/audio/PAL integration and physical hardware remain later gates. Approximately5,557 cycles remain for integration; no playable-ROM claim.
- Merge/remote CI is the final delivery gate; close this issue only after its scoped PR is integrated.

## Tracking
- Roadmap ID: SQ-07
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 15 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/7
