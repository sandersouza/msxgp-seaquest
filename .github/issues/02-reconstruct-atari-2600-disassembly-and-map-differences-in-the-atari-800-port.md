## Goal
Produce a code/data map and annotated 2600 listing. Compare the Atari 800 logic, hardware adapters and self-modifying code with the original; establish correspondence with the supplied XEX.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #1: Inventory reference binaries and verify Atari 2600 revision and region

## Definition of Ready
- [ ] Required dependency evidence is available; unresolved inputs are documented.
- [ ] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [ ] Scope and acceptance criteria below are understood.

## Definition of Done
- [ ] Document entry points, RAM variables, tables and platform differences. Validate reassembly against the 2600 binary and Atari 800 load segments where feasible; explain every unresolved difference.
- [ ] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [ ] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-02
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 18 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/2
