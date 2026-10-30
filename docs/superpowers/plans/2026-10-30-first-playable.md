# First Playable MSX1 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task-by-task, with a fresh branch review before integration.

**Goal:** Deliver an actual playable Seaquest slice on unexpanded MSX1/openMSX, preserving the original gameplay algorithm.
**Architecture:** Statically translate the manifest-verified original 6502 gameplay blocks to Z80. Maintain a canonical byte RAM image, preserve 6502 status/BCD semantics and validate it against a separate 6502 CPU model. Hardware raster code is replaced by measured SCREEN 2 rendering and original-mask collision extraction; no runtime 6502 interpreter ships in the ROM.
**Tech Stack:** sjasmplus/Z80, Python generation/tests, py65 1.2.0 and ALE for reference validation, openMSX runtime probes.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md and ../../gameplay-contract.md

## Global constraints

- MSX1 64 KiB RAM / 16 KiB VRAM, standard clock, BIOS keyboard/joystick, plain cartridge.
- Canonical original coordinates/state are independent of display adaptation.
- Originals and generated original-derived listings/data stay local under ignored outputs.
- Public CI still builds the synthetic diagnostic without original ROMs; local playable build requires verified originals.
- Preserve enemies and collidable visibility; benchmark the maximum density before choosing renderer.
- No full-game/hardware acceptance from boot or a narrow comparison; GitHub issues close only on their own DoD.

## Tasks / interfaces

1. #6: generate gameplay-only native blocks; failing instruction/canonical-state tests → native differential tests; specify source and native phase mapping.
2. #7: benchmark full-density SCREEN 2 hybrid renderer; record cycles/VRAM cost and approve strategy.
3. #8: extract original silhouettes, animation, lettering and masks reproducibly, map canonical coordinates to display.
4. #9: integrate original input/movement/firing logic and verify native/reference state cases.
5. #10/#11: integrate original lane/RNG/collision resolution plus oxygen/diver/surface transitions for a playable loop.
6. #12/#13: original score/lives/progression/HUD/sound as feasible for the first playable milestone; keep uncovered modes explicit.
7. Verify openMSX natural controls and deterministic scenarios, capture screenshots, package exact ROM/hash and update GitHub.

## Review focus

6502 carry/zero/negative preservation (including comparisons and loads); BCD score
carry; indexed zero-page wrapping; original frame phase and collision latch window;
renderer must not exceed VDP limits or hide live enemies; original assets must
remain byte-derived rather than substituted; no diagnostic-only result called playable.

## Ledger / rulings

- 2026-10-30: continuing at clean main 8daf5e2; #6 In progress, #7 Ready; #1–#5 delivered.
- Ruling: generate native Z80 from original gameplay basic blocks instead of a new
  high-level rule rewrite. This preserves event order/byte semantics and allows
  independent CPU differential validation. Runtime CPU interpretation is excluded;
  performance remains a measured gate before gameplay integration.
- Preflight: #6 canonical state feeds #9–#11; #7 renderer/collision mask interface
  feeds #8/#10. Keep phase boundaries explicit so hardware replacement cannot silently
  move collision resolution or input sampling to another original tick.
