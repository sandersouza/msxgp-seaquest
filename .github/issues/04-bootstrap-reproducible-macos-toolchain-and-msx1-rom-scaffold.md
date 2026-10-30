## Goal
Prepare pinned Z80 tools, local Python environment, reference emulator tools and openMSX. Add setup --check/--dry-run and build/run/test interfaces, with Apple Silicon and Intel handling.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #1: Inventory reference binaries and verify Atari 2600 revision and region

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] A clean supported Mac can prepare and build a bootable MSX1 cartridge. Check mode is read-only; existing environments are preserved. Verify BIOS/slot handling, 64 KiB RAM, 16 KiB VRAM and no expansion requirement; record untested hosts.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-04
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: M
- Estimate: 9 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/4

## Delivery evidence
- Merged in https://github.com/sandersouza/msxgp-seaquest/pull/18.
- macOS ARM preparation/check/dry-run, ten tests, shellcheck and both unchanged reference rebuilds passed.
- Fresh openMSX 21.0 C-BIOS_MSX1 diagnostic passed: 64 KiB RAM, 16 KiB VRAM, TMS9918A, signature/VRAM/advancing interrupts. See references/msx1-smoke.json.
- ROM SHA-256: 62131a8d9f569d2799445d94e898df09004797ed292bf12f1b924d0754497791.
- Fresh independent review clean. Intel, gameplay, original BIOS matrix, PAL and physical hardware are not validated.
