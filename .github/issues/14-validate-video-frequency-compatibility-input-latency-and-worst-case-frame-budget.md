## Goal
Implement and measure 50/60 Hz timing policy against the identified reference cadence. Exercise worst-case graphics, sound and game-state load on unexpanded MSX1.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #12: Port scoring, difficulty progression, lives and alternating-player modes
- #13: Reproduce original HUD, attract flow and PSG sound event timing

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [ ] Record exact ROM, machines, rates, cycles, RAM high-water marks, frame pacing and input latency. Preserve simulation speed; document differences in presentation and sampling without claiming identical latency across refresh rates.
- [ ] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [ ] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-14
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 15 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/14

## Implementation readiness
Dependencies #12/#13 are Closed/Done; PR #29 merged at 5a797b6e142c9fc1f946411081dd6a16e37301c3. The verified NTSC4K reference advances one source update per262 raster lines in6,000 ALE0.12.1 observations. Implementation and PAL/NTSC source/pixel/audio/pacing/latency validation are tracked in docs/video-frequency.md on codex/enhancement/14-video-cadence. Physical-machine/full-game release acceptance remains #15.
