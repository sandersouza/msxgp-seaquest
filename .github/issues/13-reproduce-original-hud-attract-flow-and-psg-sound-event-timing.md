## Goal
Integrate original HUD, lettering, score/life/diver/oxygen displays, attract/start flow and TIA-to-PSG sound event translation.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #8: Extract original graphics and map MSX1 coordinates and palette
- #12: Port scoring, difficulty progression, lives and alternating-player modes

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] HUD matches canonical state and original layout as hardware permits. Audio event onset, duration and priority match traces; document timbre differences and verify alerts, rescue, firing, death and bonus.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-13
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: L
- Estimate: 15 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/13

## Delivery candidate — local acceptance complete

[PR29](https://github.com/sandersouza/msxgp-seaquest/pull/29) integrates original
HUD/font/score/lives/divers/oxygen/logo, start/attract flow and source-ordered PSG
playback on unexpanded MSX1/64KiB RAM/16KiB VRAM. The measured128KiBASCII16 backend
preserves original actors/simulation and192enemy-pattern/352display-name bytes
per frame. Exact palette/colour queues, hidden font warming and source-preserving
native folds keep actual transitions within the frame budget.

The owner's invisible diver/hostile-shot and static-water findings are fixed:
source86/92 retain contrast with90water. R7 supplies water through colour0; the
external MSX border follows water. Opaque black remains1. Standard PSG timbre,
shared noise and oscillator-phase differences remain documented.

Reproduced on timed SHA256
`0942a040aa4bc4cb72df7db39445c2f96f237719bf8e63d1ed962ca13eca0910`:

- 39,328native/source/pixel cases at59,110/59,736cycles;240paced dense frames pass.
- 1,129focused HUD/font/palette/ripple/all8sprite checks, including24-byte triple
 glyph upload and precommit R1/R7/visible-VRAM protection.
- 111,264source updates across three183-chain attract modes, including all129
 counter boundaries, input/Reset/Select exits, B/W, cache rebases and a prepared
 token240 across activation into the next epoch.10,980RGB/spriteframes, no skips
 or visible commits; max59,583busy/10,324commitcycles.
- 7,982audio ticks/34,692ordered stores/44observed sites, including2,400persistent chain ticks.
- 6,422cold device-only CPU/TIA updates/15,807sound stores, noRAMreload/skip,
 max49,007busycycles on controls SHA256
 `f6b8e010db183e31f76533763fd195c452dc7933aff9c0ff51bb0b2a51b169c3`.
- Native2,963/input5,660/collision40,748/oxygen24,605/progression55,243 regressions,
 48host checks and local original-free CI pass.

Independent read-only review found/fixed source/cache/mapping risks and reports
no remaining material correctness finding. Final immutable-head review, remote
CI and integration remain PR gates; this issue stays open until integrated.
Detailed evidence/reproduction: references/presentation/verification.md and
 docs/hud-audio.md. #14 owns cadence/50Hz; #15 owns full-game/hardware acceptance.
The owner's original playtest artifacts remain local; original ROMs/art/tables
and playable cartridges are not published.
