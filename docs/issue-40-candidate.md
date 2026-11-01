# Issue #40 local test candidate

Owner approval is required before any PR, merge, tag or release. The issue stays
open. Original ROMs, BIOS/DOS, emulator traces and binaries remain local/ignored.

## Changes

- Filled oxygen pixels use player one's submarine palette role. Bar geometry,
  empty pixels, border, low-oxygen blinking and source logic are unchanged.
- A third stable window displays the authored native-grid `retrowork 2026`.
  Activision remains at counters0..95, its original transition at96..159,
  copyright1983 at160..191 and the added credit at192..255. Active gameplay's
  zero counter retains Activision. No canonical counter is changed.
- Initial idle palettes are forecast even when the source logo counter is zero.
  Zero remains zero in the prediction, matching the original CPU.
- Both half-period player changes prewarm the hidden font. The first half uses
  the current palette; the second uses the complete pending palette. A shared
  blank can be warmed visibly only with the unchanged current background.
- Native enemy transfers omit the permanently zero last row. Cold initialization
  clears all private enemy pattern slots; every subsequent producer leaves that
  row untouched. This removes 12 redundant writes from a four-lane commit.
- Flat palette wrappers avoid redundant calls/register loads. A bounded loop
  replaces the unrolled rare token-rebase stamping to keep the native image
  below C000 without moving any RAM ownership boundary.

## Reproduced baseline failures

Base commit: `e315927ff846e9b019c1a68467523e35119decd8`.
Normal ROM SHA256: `bf4bcb22b2303decbb2316cb673f1e979a5ba4c4e5e97591cd06f7560b8d942e`.
COM SHA256: `b3e8051088a911943501b8bf1f1615afe45e1308fa2d944b80c8dbbc0004e79d`.

The initial screen retains three lives, full oxygen and A3=0, unlike the depleted
game-over seed used by the earlier attract tests. The new `idle` scenario obtains
its state from the original reset routine, then selects only the documented
palette/phase fixture. It never replaces source state after a chain starts.

The strict baseline ROM test fails at frame352 with `budget=61259`, exceeding
59,736 NTSC cycles. A separate diagnostic run on both original native formats
records a skipped VDP frame and 18-cycle writes at active line0, where the
required minimum is29. These diagnostic runs deliberately continued past the
time limit to locate the violation; they are failing evidence, never acceptance.
A longer depleted game-over chain also fails at frame1761 with60,467 cycles.
Private captures and the failure workspace are under `outputs/issue40/baseline-*`.

## Qualification status

Implementation tests:91 host tests pass; original-free synthetic CI passes
(its system-Python trace test is skipped; the project-venv suite runs it).
The preliminary native ROM passed4,096 consecutive game-over frames and two
4,096-frame initial-idle chains (colour/monochrome). Worst idle busy work was
58,704/59,736 cycles; maximum commit15,833 cycles. These are preliminary identities,
not substitutes for the final frozen ROM/COM receipts.

The first local credit placement replaced the stable Activision window; visual
inspection caught this before delivery. The revised three-window cycle keeps
both existing presentations. Final qualification and candidate identities are
pending. Human playtesting,
subjective viewing/listening and physical MSX acceptance are not established by
the automated checks.

## Owner test checklist

1. Load `SEAQUEST32.ROM` as **Normal** on an unexpanded64KiB MSX1, with16KiB VRAM.
2. Start/reset with F1, move with arrows and fire with Space (or use a standard
   joystick). Check that filled oxygen matches the yellow submarine and that
   the emptied part retains its prior appearance as oxygen drains.
3. Reach game-over and watch several complete lower-logo cycles. Confirm the
   exact credit `retrowork 2026`, retained Activision presentation and readable
   text through the changing palette. Reset and play again.
4. Test PAL and NTSC, including the initial idle screen after prolonged inactivity.
5. For DOS1, copy `SEAQUEST.COM` to your own system disk and run `SEAQUEST`.
   Machine reset/power cycle exits the program. Firmware/system disks are not
   included with the candidate.
6. Report approval of this exact candidate, or describe any remaining issue.
   Only explicit approval starts the PR/review/integration/release stage.
