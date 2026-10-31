# Issue #14 verification

Local automated cadence, PAL/NTSC, source, pixel, audio and timing acceptance
passes. Delivery is [PR #31](https://github.com/sandersouza/msxgp-seaquest/pull/31).
The candidate includes the owner-approved lettering from PR #30. This evidence
does not certify a full-game release, physical machines or analog PSG timbre.

## Exact inputs and environment

- Atari 2600 NTSC4K SHA256:
  `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
- Frozen controls/video candidate: `outputs/video/seaquest-issue14-final.rom`, 131,072 bytes,
  ASCII16, SHA256
  `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
- Matching symbols SHA256:
  `b8678e849d6169e8efb9e0626c243ef6d5fc8b6f402f24952c595c82f93651c9`.
- Frozen unpaced/presentation benchmark: `outputs/video/seaquest-issue14-bench.rom`,
  131,072 bytes, SHA256
  `23f21dbc42bdbc190e8499257e5bfec9bd39148f54c7bdd9c52d0252fea1c7c9`.
  Matching `.sym` is saved beside it; benchmark and controls addresses differ.
- Runtime source: merge head `87dceabbceb0a25e1d9cea6277d840818d358425`, including
  upstream lettering commit `b2b9792d773fb7f08498c5b466270a3b2a2f3297`.
  Subsequent delivery edits concern verification/documentation only.
- openMSX 21.0, Python 3.14.7, ALE 0.12.1, py65 1.2.0, sjasmplus 1.24.0
  revision `d379eeac9ad3857fb48fd3a3929175d0a56038ce`.
- Standard 3,579,545 Hz Z80, 64 KiB RAM, 16 KiB physical VRAM, SCREEN 2.
  Private processes lock CPU frequency and assert the effective frequency,
  VDP version, physical RAM/VRAM sizes and BIOS identity after replay loading.
  Reports preserve those observed values rather than relying on launch labels.
- NTSC: C-BIOS_MSX1, TMS9918A, BIOS SHA1
  `2f997e8a57528518c82ab3693fdae243dbbcc508`.
- PAL: C-BIOS_MSX1_EU, TMS9929A, BIOS SHA1
  `baf2e9c69252fd9b350b488d89c71887b9d05eec`.

## Source clock and steady pacing

The original's 6,000 idle/fire/directional ALE frames each contain 262 full
raster lines and one source `$81` increment, with frame skip 1 and no sticky
actions. The probe reads the inspected ALE/Stella raster field, not cropped
image height. This is 19,912 source CPU cycles or 59,736 nominal Z80 cycles per
update, approximately 59.9227 Hz.

MSX NTSC uses one update per 262-line frame. MSX PAL uses 313-line frames of
71,364 Z80 cycles, approximately 50.159 Hz. Adding 51/262 extra updates per PAL
frame preserves the original mean simulation speed. Every source update runs
its own logical raster acquisition, input phase and ordered audio stores; the
extra update omits only intermediate presentation. All actors and the mandatory
192 enemy-pattern plus 352 display/name bytes remain in each rendered frame.

The initial empty pipeline has a bounded one-update phase offset. Sliding
262-display-interval audits start after the first displayed interval of each
chain. All 210,426 audited steady windows advance exactly 313 source updates in
PAL or 262 in NTSC. This establishes the mean clock, not uniform input/audio
onset spacing; PAL sometimes groups updates closely together.

## Fresh candidate matrix

All rows compare every update against the original CPU, including updates with
no presentation. All 251 pre-core bytes must match the independent acquisition
from its saved raster state; intervening target mutations cannot become oracle
inputs. Continuous chains reload game state only at the documented seed boundary.
Graphics checks use original assets plus the approved PR #30 score/OXYGEN masks.

| Scenario | Display frames | Source updates | Pixel frames | Max busy cycles |
|---|---:|---:|---:|---:|
| PAL, 183 boundary/exit/B&W/player/logo chains |96,075|114,741|13,176|63,083|
| PAL, Select at phase 255, all 262 initial accumulators |29,344|35,005|5,312|66,842|
| PAL, 32 dense states |16,800|20,064|2,035|67,300|
| PAL, forced token rebase |96,075|114,741|13,176|63,983|
| PAL, READY1/token 240 through activation/rebase |96,075|114,741|13,176|63,083|
| PAL, cold device replay |1,200|1,434|151|59,811|
| NTSC, 183 boundary/exit/B&W/player/logo chains |96,075|96,075|11,712|58,687|
| NTSC, 32 dense states |16,800|16,800|2,050|58,716|
| NTSC, cold device replay |1,200|1,201|149|51,238|

The video matrix totals 449,644 displays, 514,802 source updates, 60,937 pixel
frames and 132,262 ordered audio stores. There are zero missed display frames or
visible commits. PAL rebase mode performs 180 rebases; READY mode performs 148
rebases and observes 8,007 READY1/token-240 prefetch entries. JSON files here record
each seed hash, actual settings, source counts and verdict.

Busy time includes commit, simulation, presentation preparation, anticipatory
contacts and loop dispatch, ending at `paced_wait`. The worst PAL load is
67,300/71,364 cycles, leaving 4,064. The separate full presentation regression's
worst continuous NTSC load is 58,800/59,736 cycles, leaving 936. Its conservative
commit endpoint includes the empty extra-update dispatcher; max 9,703 cycles
still fits TI's documented 4.3 ms refresh window. PAL's measured render commit
max is 9,635 cycles. Actual active-picture I/O spacing is at least 29 cycles;
12-cycle uniform writes and 18-cycle copies remain inside VBlank/display-off.

## Input latency and memory

Sixteen separate directional pulses exercise keyboard and joystick in the cold
replay. Times start at emulated device events: sample means input-adapter return,
state means original update completion, and display means SAT upload completion.
The display measurement follows the first visible directional response; an
intermediate PAL coordinate may intentionally never be presented. These are
measured scenarios, not universal worst-case physical input guarantees.

| Maximum among these pulses | NTSC | PAL |
|---|---:|---:|
| Device to input-adapter return |16.3565 ms|19.8699 ms|
| Device to source-state completion |18.1615 ms|21.5883 ms|
| Device to SAT commit |30.8782 ms|37.5968 ms|

Host OS/device latency, visible scanout and physical displays are not included.
Game RAM is not reloaded after cold cartridge boot. Replays reject debugger
writes, so cold stack measurement uses C-BIOS `init_ram`'s C9 reserve and includes
startup; seeded tests use an A5 marker after BIOS initialization.

Application RAM reserves C000..EFFF (12,288 bytes), F000..F2FF is an unchanged
768-byte guard, F300..F37F reserves 128 stack bytes, and BIOS begins at F380.
The lowest observed cold stack address is F35E (34 bytes below F380); seeded
chains reach F370 (16 bytes). All source/cache/guard boundaries remain intact.
VRAM remains 16 KiB; resident/scratch/border sprite patterns end at 3FFF.
The fixed code bank has 267 padding bytes. Source-bank data still ends at 9B00,
with live 9900/9A00 tables and zero pre-helper padding; this is not free space.

## Presentation regressions, review and reproduction

`make presentation-check` passes 39,328 source/pixel cases (max 59,110 cycles),
240 paced dense frames, 1,129 focused projection cases, 111,264 continuous source
updates across three 183-chain modes, 7,982 ordered-audio cases/34,692 stores,
and 6,421 cold CPU/TIA updates/15,812 audio stores. Isolated display-only projection
fixtures reach 64,469 cycles; they have no preceding paced pipeline and are not
advertised as runtime frame-budget passes. Full source-update fixtures and the
continuous paced scenarios above supply that timing acceptance.

All 55 host tests pass. Original-free local CI passes (55 tests, one optional
py65 skip, plus diagnostic/input/collision/audio/video assemblies). Independent
read-only review checked scheduler, source phases, mapper/stack and test oracles;
reported harness and boundary-coverage gaps were corrected. Deliberately disabling
extra updates fails the clock audit; mutating staged source E6 fails before it can
feed the CPU oracle. Remote checks must pass on the final PR head before merge.

Run these serially from the repository with the documented local reference inputs:

```sh
make environment-check
make test
make video-check
bash scripts/ci.sh
```

`make video-check` runs presentation checks, builds the private matching video
ROM/symbol pair, measures the reference, then runs every row and generation mode
above in separate headless processes. Concise reports are written under
`outputs/video/<machine>/<scenario>-<generation>/result.json`. Raw original-derived
states/art, captures, replay files and cartridges remain ignored. No owner's
visible openMSX session or protected issue #13 cartridge is stopped or replaced.

Physical acceptance and natural full-game release regression remain issue #15.
