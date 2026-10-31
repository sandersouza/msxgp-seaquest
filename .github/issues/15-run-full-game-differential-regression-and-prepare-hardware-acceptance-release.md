## Goal
Run natural full games and controlled boundary replays across modes/difficulties, verify visuals/audio, package the exact tested ROM and prepare hardware acceptance instructions.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. The measured presentation catalog uses a 128 KiB ASCII16 cartridge. Preserve the owner's approved MSX score/OXYGEN lettering.

## Dependencies
- #6: Capture deterministic Atari 2600 traces and define state comparison contracts
- #14: Validate video-frequency compatibility, input latency and worst-case frame budget

## Definition of Ready
- [x] Required dependency evidence is available; #6 and #14 are Closed/Done, PR #31 integrated in `19940e8`.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified in `docs/handoffs/issue-15.md` and `docs/plans/issue-15.md`.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [ ] Link reproducible traces and regression verdicts, release ROM hash and machine/cartridge instructions. Separate automated, manual emulator and physical-machine evidence. Keep physical acceptance pending until actually tested.
- [ ] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [ ] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-15
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 18 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/15

## Delivery progress

- Branch: `codex/chore/15-full-game-acceptance`, based on `19940e8`; runtime unchanged.
- Matrix: device-only complete game over/restart for both modes, all four independent difficulties and both video standards, plus natural rescue/oxygen routes. Every source update, sampled pixels, ordered PSG stores, clock, pacing, RAM and stack are checked.
- Independent review findings in the validator were corrected; final matrix, replay reproduction and delivery CI are being completed.
- Candidate: 131,072-byte ASCII16 SHA256 `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
- Manual emulator viewing/listening and physical machine acceptance remain pending actual observation; the deliverable prepares their procedure and record.
