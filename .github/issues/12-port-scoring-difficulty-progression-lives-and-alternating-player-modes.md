## Goal
Implement score arithmetic, enemy/diver value progression and caps, oxygen bonus, extra lives, wave difficulty, patrol unlocks, game over and alternating players.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #11: Port oxygen, diver rescue, surfacing and refill transitions

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Validate thresholds, caps, score limits, death/restart, independent player state and full progression against reference evidence, including late-game scenarios.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-12
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 15 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/12

## Implementation and evidence

Delivery PR: https://github.com/sandersouza/msxgp-seaquest/pull/28.

The original source score block now fits dense late-game bonuses while preserving
individual scoring calls, decimal carry, caps, returned A/X/Y/C/N/Z and observable
event order. The64,981-cycle original worst case now takes58,291. NMOS79+01→80/N=1
is explicitly verified. No enemies, visibility, pixels or simulation frequency
were reduced.

55,243 original/native contract records pass, including25,072 score status checks,
seven-field player swaps, all256 group/wave values, patrol cadence, simultaneous
scoring/death/extra-life/bonus events and8,800 seeded chained ticks.264 original
display/core executions audit omitted logical inputs.39,328 combined state/pixel
cases pass at maximum59,311/59,736 cycles,425 free;240 paced frames have no skips.
The32KiB cartridge retains1,536 padding bytes and64KiB RAM/16KiB VRAM operation.

6,262 cold-boot actual-control updates match original CPU/TIA without game-RAM
reloads:14 death-driven player switches, two game overs, one restart,16 deaths
and all4 difficulty settings. Late-game/full-bonus coverage is explicitly seeded;
it is not relabeled natural play. Native/input/collision/oxygen/graphics regressions,
39 host tests and local synthetic CI pass. Intentional runtime score corruption
fails immediately, followed by a passing normal contract.

Independent read-only follow-up at53ea3d3e79d41ad477b2a850e9db2afc45ecbc68 found
no actionable findings, recomputing every contract expectation, all6,262 natural
updates and504 dense late-bonus states, and verifying both ROM hashes/timing.
Both implementation-head remote checks passed; final delivery-head CI is required
before integration and closure.

See [phase and reproduction](https://github.com/sandersouza/msxgp-seaquest/blob/main/docs/scoring-progression.md)
and [exact evidence/review](https://github.com/sandersouza/msxgp-seaquest/tree/main/references/progression).
Original-derived data, art, ROMs, listings and replays stay local and ignored.
HUD/background remain synthetic; PSG audio, full-game, PAL and physical MSX
acceptance remain later work. Successor handoff: docs/handoffs/issue-13.md.
