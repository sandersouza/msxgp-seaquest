## Goal
Extract original constants, event ordering and transitions for movement, firing, enemies, rescue, oxygen, scoring, death, progression, reset, attract and both player modes. Use the 2600 as authority.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #2: Reconstruct Atari 2600 disassembly and map differences in the Atari 800 port

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Every rule cites source addresses or captured evidence. Cover surfacing with 0/1/5/6 divers, oxygen depletion/refill, both firing difficulties, patrol, bonus and score/life limits; mark unknowns explicitly.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-03
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 12 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/3

## Delivery evidence
- Static source contract merged in https://github.com/sandersouza/msxgp-seaquest/pull/20; GitHub CI passed.
- docs/gameplay-contract.md records original addresses, state/event order, constants, arithmetic and required trace fixtures.
- Independent original-listing review corrected patrol table indexing, wave-wrap behavior and held-select repeat timing.
- Runtime timing, raster collision capture and native acquisition alignment remain explicitly assigned to #6/#7/#8/#14; this issue does not claim runtime gameplay acceptance.
