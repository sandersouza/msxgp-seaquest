## Goal
Extract source graphic shapes and lettering with provenance; map colors and display coordinates for SCREEN 2 while retaining canonical game coordinates.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #7: Benchmark worst-case SCREEN 2 rendering and approve sprite strategy

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Reproducible extraction outputs match reference shapes. Document clipping, bounds, palette and coordinate mapping. Visual adaptation does not change collision masks or movement; no substituted branding.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [ ] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-08
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: M
- Estimate: 9 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/8

## Delivery evidence

- [Graphics contract](../../docs/original-graphics.md) and [metadata-only evidence](../../references/graphics/).
- 251 assets/display variants; 467 original ALE shape/lettering scenarios plus 260 edge cases pass.
- 6,526 native/background/sprite/palette cases pass; max 59,211/59,736 cycles, 240 paced frames without skips, 29-cycle minimum VRAM spacing. 27 host tests and 2,707 continuous native cases pass; both corruption controls fail as intended.
- Original-derived data remain ignored local research outputs. HUD/background color composition, natural gameplay/input/audio, PAL and physical hardware remain unverified.
- Independent review, remote CI and integrated delivery are still required before closure.
