# Issue #15 — complete games and acceptance package

Runtime base: `19940e8fb08ac8269990725b88a70e8c56156e16` after PR #31.
No runtime code, generated cartridge data, mapper, approved lettering, input or
renderer changed in this issue. The candidate is the frozen issue #14 final ROM:

- ROM: 131,072 bytes ASCII16, SHA256
  `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
- Symbols SHA256:
  `b8678e849d6169e8efb9e0626c243ef6d5fc8b6f402f24952c595c82f93651c9`.
- Original Atari 2600 NTSC4K SHA256:
  `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.

## Automated observations

[suite.json](suite.json) records all route counts, exact identities, tools,
observed machines/BIOS, hashes of private traces/timing/replays, state replay
hashes and validation source hashes. Raw inputs/states/captures/replays and
cartridges stay local in ignored `outputs/acceptance/`.

The 16 complete-game routes cover both one/two-player selections and all four
independent difficulty combinations on C-BIOS_MSX1/NTSC and C-BIOS_MSX1_EU/PAL.
Each cold-boots, selects mode/switches via actual keyboard devices, resets once,
then plays uninterrupted through stock exhaustion, game over and restart. Two
additional rescue routes require pickup, partial rescue, low-oxygen alarm and
oxygen death. Every source update compares against the independent original
6502 CPU and acquisition oracle. Sampled display VRAM/pixels, original sprites,
ordered real PSG register writes, cadence windows, VBlank commits, VRAM spacing,
RAM guards and stack watermark are checked by the inherited video validator.

All 18 device replays were then loaded **viewonly without the feedback
controller**. Every captured 251-byte canonical state matched the original run.
The package additionally reloads its relative-path replays directly from the
extracted package root against its own copied ROM, comparing the entire state
sequence hash and count. This establishes reproducible automated play, not
manual emulator or real-machine acceptance.

Important limits:

- Natural rescue routes reached partial rescue and oxygen depletion; they did
  **not** reach a six-diver rescue. Full-six bonuses, score boundaries and later
  progression retain their explicitly controlled source/native fixture evidence.
- Exhaustion play is a deterministic device feedback policy, not a skilled human
  game. It deliberately uses the original zero-diver surface penalty.
- Pixels are sampled at boundaries and periodically, not every rendered frame.
- All source updates and ordered audio stores are checked, but oscillator phase,
  analog timbre, host input and visible scanout are outside this measurement.

## Controlled boundaries and regressions

The full prior [video matrix](../video/verification.md) remains applicable by
identical cartridge hash: 449,644 display frames, 514,802 source updates, 60,937
pixel frames, 132,262 audio stores and 210,426 cadence windows. It includes 183
boundary chains, 262 PAL accumulator alignments, dense states, generation rebase,
READY1/token240, cold keyboard/both joystick ports and all difficulty switch bits.
No need to rebuild the entire unchanged baseline merely to relabel its issue.

A fresh [PAL READY1 regression](boundary-regression.json) passes 525 frames,
627 source updates and 72 pixel frames, including one generation rebase and 44
READY1 epoch exposures. Deliberately mutating staged E6 fails at source update 6,
byte E6; the normal READY1 route passes. The new acceptance unit tests reject
boot-only/death-only/incomplete games, missing restart, wrong mode/difficulty,
incomplete player coverage, diagnostic/modified cartridges, stale symbols and
missing/duplicate/mixed routes. Replay relocation preserves BIOS and input events
and rejects a different cartridge.

67 host tests pass in the project environment. Original-free local synthetic CI
passes (the optional independent py65 test is skipped if py65 is absent from its
system interpreter). Public CI assembles diagnostics/synthetic probes; it does
not run the local original-derived full-game matrix.

Independent read-only review found and corrected two validation issues: cold
routes no longer require a historical seeded-game file, and result reuse was
removed to prevent stale oracle/tool evidence. The final complete matrix was run
again after these changes; no new static review blockers remain.

## Delivery and observations still required

[Hardware/emulator instructions](../../docs/hardware-acceptance.md) give exact
hashes, ASCII16 configuration, reproduction commands, controls, scenarios and
machine/cartridge requirements. [Observation template](../../docs/acceptance-observations.md)
separates manual emulator viewing/listening and physical sessions. The ZIP is
local-only and includes the exact candidate, symbols, all verified replay routes,
reports and instructions. Its receipt is `outputs/acceptance/package.json`.

An ignored static VRAM preview was inspected for score/OXYGEN layout and an
eight-second local WAV was captured for owner listening. These do not establish
a completed human playtest or subjective sound acceptance.

**Manual emulator gameplay/listening: pending owner observation. Physical-machine
acceptance, cartridge compatibility and the 20-minute physical soak: pending
actual tests.** Issue #15 prepares acceptance; it does not certify those results.
