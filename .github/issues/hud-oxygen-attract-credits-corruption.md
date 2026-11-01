# Refine oxygen color and attract credits; fix cycling HUD corruption

Type: Bug (native issue-type persistence is unavailable in this repository).
Priority: P2. Size: M. Estimate: 8 hours, provisional until the attract corruption is reproduced.
Project: MSX Game Ports #7. Milestone: none, following repository convention.

## Owner request and approval boundary

The owner requests a new dedicated issue/chat for three presentation changes:
1. Make the filled oxygen bar yellow, matching our player submarine. Preserve the current appearance of the depleted/empty portion and oxygen depletion behavior.
2. Outside active gameplay, add the exact credit text `retrowork 2026` to the existing lower-screen Activision logo/text alternation. Retain the existing Activision presentation in the cycle.
3. Reproduce and fix the reported lower HUD graphics corruption while colors cycle outside gameplay (attract/game-over). Root cause is not yet established.

Implement and validate a local candidate, then deliver the ROM/COM for the owner to test. **Do not create a PR (including draft PR), merge into main, tag, or publish a new release until the owner tests and explicitly approves this candidate.** After approval, proceed with PR/review/merge and a new release, preserving the current release's base text and adding the new corrections. Keep this issue open until its delivery/approval conditions are met.

## Context and dependencies

Base: main at `e315927ff846e9b019c1a68467523e35119decd8` (PR #39). Issue #35 is delivered. The complete Normal 32 KiB ROM is the default for `make build` / `make run`; `FORMAT=com` selects the DOS1 executable. The original 128 KiB ASCII16 artifact remains separately available.

Target remains an original MSX1 with 64 KiB RAM, 16 KiB VRAM, standard Z80/PSG/VDP and no expansions. ROM must remain <=32,768 bytes. DOS1 naturally requires its disk interface/system disk. Preserve original gameplay/input/oxygen mechanics and the existing depleted-bar appearance. Do not modify or publish original Atari research ROMs or BIOS.

## Reproduction and investigation

Owner observed corruption at the bottom of the screen outside gameplay while HUD colors cycle. Reproduce on the current native cartridge and COM, capture the affected palette phase/frame, and trace pattern/color/name-table writes, palette staging/cache generations and logo transitions before selecting a fix. No screenshot or exact phase was supplied, so record actual observations rather than assuming a cause.

## Scope

- Inspect HUD oxygen roles, lower credit glyphs and attract/game-over palette generation/commit paths, including compact native tables and the older banked path where shared code changes.
- Match filled-bar color to the player submarine, retaining depleted graphics, lengths, thresholds and timing.
- Add readable native-grid `retrowork 2026` to the existing lower credit alternation outside gameplay.
- Repair the measured corruption without disabling the intended palette cycle or hiding the faulty area.
- Validate PAL/NTSC through complete attract/color/logo cycles, game-over, restart and active gameplay; test final ROM and COM through actual loading.
- Recheck original-state equivalence, pixels/sprites/audio, immutable RAM, stack/VRAM guards and full-density timing/generation boundaries. Record intentional visual differences narrowly in comparison expectations; do not broadly weaken the oracle.
- Produce reproducible candidate artifacts and concise before/after visuals with exact hashes, commands and evidence limitations. Keep runtime/reference-derived outputs local and ignored.
- After owner approval only: independent review, PR, merge and new-release publication with the existing release narrative retained and corrections appended.

## Definition of Ready

- [x] Owner specified all three changes and authorized implementation in another issue/chat.
- [x] Main/default native build and prior qualification receipts are available locally.
- [x] Owner testing before PR/merge/release is an explicit gate.
- [ ] Corruption is reproduced and its affected phases/root cause are measured (investigation work).

## Definition of Done

- [ ] Filled oxygen is the submarine's yellow; depleted/empty appearance and mechanics remain unchanged.
- [ ] `retrowork 2026` alternates with the existing lower Activision presentation only outside gameplay.
- [ ] Reported cycling-HUD corruption is reproduced, explained and fixed across full palette/credit cycles.
- [ ] Final Normal ROM stays <=32 KiB; ROM and COM work on the original 64 KiB MSX1 target with measured PAL/NTSC timing and guard/state/presentation regressions passing.
- [ ] Candidate artifacts and before/after evidence are delivered for owner testing, with automated/manual/physical evidence kept separate.
- [ ] Owner explicitly approves the tested candidate before any PR, merge or release.
- [ ] Independent review, PR checks and integration pass after that approval.
- [ ] New release is published after approval, retaining base release text and adding these fixes; GitHub/local handoff/status agree.
