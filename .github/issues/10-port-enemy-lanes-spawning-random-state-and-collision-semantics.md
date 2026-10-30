## Goal
Port enemy/diver/shot lane state, RNG and spawn order, repeated enemies, movement and hardware-equivalent collision masks and ordering.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #9: Port player movement, input sampling and original firing cadence

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Reference comparisons cover seeds, spawns, lane transitions, clipping, repeated enemies and simultaneous collisions. Do not replace original collision behavior with unverified bounding boxes.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-10
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 18 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/10

## Implementation and evidence

Delivery PR: https://github.com/sandersouza/msxgp-seaquest/pull/26.

The continuous controls diagnostic now acquires original raster contacts before
the existing F5B8→F00E native update. It preserves original lane/RNG/spawn and
ordered resolution, repeated/clipped shapes, invisible X0 copies and circular
edges. Patrol selection includes both early death and the source lives-kernel
carry for zero/one reserve with no death.

20,374 original TIA scenarios and 40,748 native acquisition/resolution cases pass,
covering all 256 phases/waves/seeds and 96 legal player Y values. All 10,622
integrated input/collision/graphics cases pass at up to 59,370/59,736 cycles,
with 240 paced frames without skips and minimum VRAM spacing of 29 cycles.
659 uninterrupted cold-boot updates match Atari latches and the original CPU,
with no RAM reloads or skipped VDP frames. The cartridge remains 32 KiB on
unexpanded MSX1, with 1,536 padding bytes and only 366 measured CPU cycles free.

See [phase, limits and reproduction](https://github.com/sandersouza/msxgp-seaquest/blob/main/docs/collision-contract.md)
and [exact evidence](https://github.com/sandersouza/msxgp-seaquest/tree/main/references/collision).
Original-derived ROMs, tables, art, listings and replays remain local and ignored.
HUD/background remain synthetic; audio, full-game, PAL and physical MSX acceptance
remain later work. Independent follow-up review at89514e0d5405dff8201b5003b19b819335316e34
found no remaining actionable issues, independently checking all10,622 pixel/state
cases,10,621 visible-VRAM transitions,659 natural updates and504 patrol carry
combinations. Integration requires passing checks at the final PR head.
