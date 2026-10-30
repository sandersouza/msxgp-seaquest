## Goal
Implement Z80 player movement, facing, diagonal input, boundaries, keyboard/joystick sampling, torpedo behavior and both difficulty-switch firing cadences.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #3: Specify original gameplay rules, state transitions and edge cases
- #6: Capture deterministic Atari 2600 traces and define state comparison contracts
- #7: Benchmark worst-case SCREEN 2 rendering and approve sprite strategy

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Aligned reference replays match player state, movement and firing events. Verify held fire, reversal, diagonal input and boundaries; measure input latency on the target.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-09
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: M
- Estimate: 12 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/9

## Implementation and evidence

Delivery PR: https://github.com/sandersouza/msxgp-seaquest/pull/25.

The controls adapter samples actual MSX keyboard/joystick devices at original
F6A7 and retains the translated movement/firing algorithm. Independent original
CPU comparisons pass: 5,660 input cases (including both players' A/B held-fire
chains), 659 uninterrupted cold-boot updates and 2,707 native core cases.
All 9,598 full-density input/graphics cases pass at up to 59,369/59,736 cycles,
with 240 paced frames without skips and 29-cycle minimum VRAM spacing.
Event-to-state latency is at most18.6709 ms; completed SAT upload at most32.2447 ms.

See [controls and reproduction](https://github.com/sandersouza/msxgp-seaquest/blob/main/docs/input-controls.md)
and [exact evidence](https://github.com/sandersouza/msxgp-seaquest/tree/main/references/input).
The controls diagnostic uses neutral collision contacts; full collision
acquisition, audio/HUD integration, PAL and physical MSX remain later gates.
Source-derived ROMs/art/listings and replay snapshots remain local and ignored.
