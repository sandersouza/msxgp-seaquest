## Goal
Hash and document both supplied binaries; identify the 2600 revision, region, frame cadence and switch defaults. Preserve original inputs and document provenance.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
None.

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Reference manifests contain byte sizes and SHA-256 hashes; region/revision conclusions cite evidence or remain explicitly unresolved. Original files are unchanged.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-01
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: S
- Estimate: 3 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/1

## Delivery evidence
- Implemented and merged in https://github.com/sandersouza/msxgp-seaquest/pull/16.
- Six synthetic tests passed; all three local originals match hash/structure manifest.
- Stella 7.0c identifies the exact 2600 hash as NTSC/4K. Measured cadence and source provenance limitations are explicit in docs/reference-inventory.md.
- Independent review clean. No gameplay or physical-hardware acceptance claimed.
