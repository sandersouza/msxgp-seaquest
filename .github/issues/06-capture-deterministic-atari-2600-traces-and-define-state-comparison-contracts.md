## Goal
Validate an emulator capture backend and produce replayable inputs, aligned resets/seeds and canonical state snapshots. Compare frames/ticks and report the first mismatch.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #2: Reconstruct Atari 2600 disassembly and map differences in the Atari 800 port
- #3: Specify original gameplay rules, state transitions and edge cases
- #4: Bootstrap reproducible macOS toolchain and MSX1 ROM scaffold

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] A known short sequence proves reset, seed, input-sampling and tick-boundary alignment. Capture positions, RNG, timers, oxygen, score, lives, enemies, divers and shots. Demonstrate a deliberately introduced mismatch is detected.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-06
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 18 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/6

## Progress — initial partial delivery
- https://github.com/sandersouza/msxgp-seaquest/pull/21 adds optional ALE 0.12.1 solo post-frame capture and a strict reference-replay comparator.
- Two independent 209-snapshot B/B runs match; frame-byte stepping, refill/movement, B/A firing and an injected real-trace mismatch were verified. Fourteen synthetic tests and fresh independent review pass.
- Initial frame67/seed204 reflects explicitly recorded ALE warmup/soft resets, not cold frame zero.
- Remaining: native canonical-field/phase mapping, source clock/scanlines, reset/select/alternate-player and additional switch adapters, full collision/oxygen/rescue/score/death fixture catalogue. This was the initial delivery's remaining work; see the completed logical contract below.
- Evidence and reproduction: docs/reference-traces.md and references/trace-probe-summary.json. No full gameplay or hardware acceptance claimed.

## Delivery — native logical phase contract
- Completed in https://github.com/sandersouza/msxgp-seaquest/pull/22 (merged 1ff1616).
- 2,707 original-6502/native-Z80 RAM comparisons pass, including reset plus 480 continuous updates without reloading native game state, sampled controls, Select/Reset, frame rollover, death and player switching.
- Named boundary is original PC F5B8→F00E. Original PRNG seeds, BCD scores, timers, lane arrays, oxygen, diver and shot state are compared. Injected X corruption is detected at chain tick13, RAM C6, expected76/actual77.
- Fresh review's continuity gap was resolved with a real chained replay. Synthetic CI passes; no original/generated sources are published.
- Physical raster/clock/refresh validation and full natural-game coverage remain the renderer, #14 and #15 gates; this closure certifies the logical state/input-phase contract rather than claiming full gameplay acceptance.
