# Issue #40 local test candidate

The owner approved the exact candidate on 2026-11-02: “aprovada, pode seguir”.
The approval gate is satisfied; the issue stays open until integration/publication. Original ROMs, BIOS/DOS, emulator traces and binaries remain local/ignored.

## Changes

- Filled oxygen pixels use player one's submarine palette role. Bar geometry,
  empty pixels, border, low-oxygen blinking and source logic are unchanged.
- A third stable window displays the authored native-grid `retrowork 2026`.
  Activision remains at counters 0..95, its original transition at96..159,
  copyright 1983 at160..191 and the added credit at192..255. Active gameplay's
  zero counter retains Activision. No canonical counter is changed.
- Initial idle palettes are forecast even when the source logo counter is zero.
  Zero remains zero in the prediction, matching the original CPU.
- Both half-period player changes prewarm the hidden font. The first half uses
  the current palette; the second uses the complete pending palette. A shared
  blank can be warmed visibly only with the unchanged current background.
- Native enemy transfers omit the permanently zero last row. Cold initialization
  clears all private enemy pattern slots; every subsequent producer leaves that
  row untouched. This removes 12 redundant writes from a four-lane commit.
- Flat palette wrappers avoid redundant calls/register loads. The original fast
  unrolled token-rebase stamping is retained with register-indirect accesses.
  All player swaps mark an atlas-only change when the physical palette is
  unchanged, including console transitions. Every logo, including the credit,
  has an exact precompiled queue. Shared HUD and logo fragments are interned
  separately to fit all 30 variants in RAM. The credit's former generic fallback
  exceeded the NTSC budget during a Select transition; the focused case now
  passes at52,919 cycles, including original-state, pixel and audio checks.
- Native precompiled fixed-field queues collect the current oxygen gauge
  separately. This also covers Fire starting a refill on the palette-change
  tick, rather than falling back to an expensive full HUD scan.
- Forecasted palette commits' contiguous lower-background colour writes share
  one VDP address setup inside VBlank. Other transfers retain the normal
  paced writers. The fused path uses the same immutable colour classes and
  preserves the slow active-display fallback.
- After palette activation, an atlas-only player swap uses its already warmed
  font and collects changed bottom fields once. It does not enqueue the full
  fixed HUD again. A continuous128-palette attract chain exposed the redundant
  work at frame21,601, a combination not covered by the earlier525-frame seeds.
  Native forecast aliases also avoid redundant wrapper/guard instructions.

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
A longer depleted game-over chain also fails at frame1761 with 60,467 cycles.
Private captures and the failure workspace are under `outputs/issue40/baseline-*`.
The captures establish timing and VRAM-write violations; they are not a video
recording of the displayed scanout. Owner testing still needs to confirm that
the originally reported visible corruption is gone.

## Qualification status

Frozen implementation: `a44811c68345d32041d0114c048276e169958430`.

| Local artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `SEAQUEST32.ROM` (Normal) | 32,768 | `5907ee7f9eb50df9ae356fee9bcb5ef931beb388d569a22aa9af043a7d97018a` |
| `SEAQUEST.COM` (DOS1) | 25,599 | `a4f1e4330ceb6ad0dff7769d0c2805e22149241da6c3359b8cf2baa453a03d91` |

Implementation tests: 91 host tests pass; original-free synthetic CI passes
(its system-Python trace test is skipped; the project-venv suite runs it).
The shared banked renderer passed 39,328 palette/progression cases, worst 59,056
of 59,736 NTSC cycles, plus 240 paced frames. The native-only fused writer does
not change that diagnostic ROM: its rebuilt SHA256 remains
`8bd402d131e233f0dbcc857cdfd4c3ad0807de6423d3cee17774f6cc8ec6154f`.
That legacy benchmark is separate from native ROM/COM qualification.

The final frozen artifacts passed 78 instrumented checks: 42 palette/generation/
boot checks plus 36 complete game-over/restart/rescue routes, and 36 independent
original-CPU replays. They covered 2,643,400 display frames,
2,927,052 source updates and 341,048 sampled pixel frames.
Worst busy work: NTSC 59,133/59,736 cycles;
PAL 67,006/71,364. There were no skipped VDP frames
or visible commits; active-display writes retained at least 29 cycles spacing.
Loader bytes, resident atlas, immutable regions, generations, stack/VRAM guards,
source state, presentation and PSG checks passed on both formats.

The local owner archive is `outputs/issue40/seaquest-issue40-5907ee7f.zip`. It includes both binaries, exact
SHA256 sums, a Portuguese test guide, qualification details and actual VRAM
previews. The half-oxygen before/after pair uses byte-identical 251-byte source
states from qualified baseline/candidate routes; the empty red half is identical.
No BIOS, DOS, original ROM or replay image is shipped in this archive.
Compact public metadata is in `references/compact-delivery/issue-40-candidate.json`;
full private receipts and excluded intermediate candidates remain under
`outputs/issue40/`. Discarded identities do not qualify these final files.

Human playtesting, subjective viewing/listening and physical MSX acceptance
are not established by the automated checks.

## Owner test checklist

1. Load `SEAQUEST32.ROM` as **Normal** on an unexpanded 64 KiB MSX1, with 16 KiB VRAM.
2. Start/reset with F1, move with arrows and fire with Space (or use a standard
   joystick). Check that filled oxygen matches the yellow submarine and that
   the emptied part retains its prior appearance as oxygen drains.
3. Reach game-over and leave it running for 10 minutes to cover the prolonged
   colour sequence as well as the short lower-logo cycles. Confirm the
   exact credit `retrowork 2026`, retained Activision presentation and readable
   text through the changing palette. Reset and play again.
4. Test PAL and NTSC, including the initial idle screen after prolonged inactivity.
5. For DOS1, replace any older `SEAQUEST.COM` on your own system disk with the
   supplied file and run `SEAQUEST`.
   Machine reset/power cycle exits the program. Firmware/system disks are not
   included with the candidate.
6. Report approval of this exact candidate, or describe any remaining issue.
   Only explicit approval starts the PR/review/integration/release stage.

## Reproducible build and qualification

Supply the existing local original inputs and use the project virtualenv. The
short `make input-natural` trace has no game-over seed; use the complete
progression trace before seeded qualification:

```sh
make environment-check
make progression-natural
.venv/bin/python -B scripts/render_bench.py --palette --progression
make build
make build FORMAT=com
shasum -a 256 outputs/disk/SEAQUEST32.ROM outputs/disk/SEAQUEST.COM
```

For each of `C-BIOS_MSX1` and `C-BIOS_MSX1_EU`, run the exact ROM and matching
symbols through `scripts/video_check.py` with `--delivery plain32`: scenarios
`attract`, `idle`, `dense` (525 frames each); `attract --generation wrap` and
`attract --generation ready` (525 each); `idle --generation wrap --quick` and
`idle --generation ready --quick` (1024 each); `cold` (1200); and consecutive
`attract --quick` / `idle --quick` chains (32768 each). PAL additionally runs
`burst` (525 frames, all 262 accumulators). Each command has its own output
folder and preserves every timing/state/pixel/audio/immutable-RAM check.

```sh
.venv/bin/python -B scripts/video_check.py --delivery plain32 --rom outputs/disk/SEAQUEST32.ROM --machine C-BIOS_MSX1 --scenario idle --frames 525 --output-root outputs/issue40/reproduce/plain32
.venv/bin/python -B scripts/full_game_check.py --delivery plain32 --rom outputs/disk/SEAQUEST32.ROM --output-root outputs/issue40/reproduce/plain32-acceptance
.venv/bin/python -B scripts/native_replay_check.py outputs/issue40/reproduce/plain32-acceptance
```

Repeat the same matrix with `--delivery dos --rom outputs/disk/SEAQUEST.COM`,
the private verified DOS1 disk and the64 KiB MSX1 machine configurations from
[native delivery](native-delivery.md). Set `--region ntsc`/`pal` explicitly;
the DOS `cold` device replay uses `--input-delay 25`. Run both 18-route natural
acceptance suites and their independent replays. Firmware, DOS and replay
snapshots remain outside the candidate archive.

The complete local matrix can be reproduced with the following Bash commands
after the build above. The DOS disk must contain the exact newly built COM;
delete an older file before importing its replacement, and verify its bytes.
The custom DOS machines and private system disk are local prerequisites.

```bash
set -eu
for delivery in plain32 dos; do
  if [ "$delivery" = plain32 ]; then
    binary=outputs/disk/SEAQUEST32.ROM
    extra=()
    ntsc_machine=C-BIOS_MSX1
    pal_machine=C-BIOS_MSX1_EU
  else
    binary=outputs/disk/SEAQUEST.COM
    extra=(--disk outputs/issue40/testenv/seaquest-dos1.dsk)
    ntsc_machine=seaquest_issue35_dos_ntsc
    pal_machine=seaquest_issue35_dos_pal
  fi
  for region in ntsc pal; do
    machine=$ntsc_machine
    if [ "$region" = pal ]; then machine=$pal_machine; fi
    run_case() {
      .venv/bin/python -B scripts/video_check.py \
        --delivery "$delivery" --rom "$binary" --machine "$machine" \
        --region "$region" --output-root "outputs/issue40/reproduce/$delivery" \
        "${extra[@]}" "$@"
    }
    run_case --scenario idle --frames 525
    run_case --scenario attract --frames 525
    run_case --scenario dense --frames 525
    run_case --scenario attract --generation wrap --frames 525
    run_case --scenario attract --generation ready --frames 525
    run_case --scenario idle --generation wrap --frames 1024 --quick
    run_case --scenario idle --generation ready --frames 1024 --quick
    if [ "$delivery" = dos ]; then
      run_case --scenario cold --frames 1200 --input-delay 25
    else
      run_case --scenario cold --frames 1200
    fi
    if [ "$region" = pal ]; then run_case --scenario burst --frames 525; fi
    run_case --scenario attract --frames 32768 --quick
    run_case --scenario idle --frames 32768 --quick
  done
  acceptance="outputs/issue40/reproduce/$delivery-acceptance"
  .venv/bin/python -B scripts/full_game_check.py \
    --delivery "$delivery" --rom "$binary" "${extra[@]}" \
    --ntsc-machine "$ntsc_machine" --pal-machine "$pal_machine" \
    --output-root "$acceptance"
  .venv/bin/python -B scripts/native_replay_check.py "$acceptance"
done
```

## Approval and independent review

The owner approved this exact candidate on 2026-11-02. Independent review of `e315927..afed3c0` found no actionable or merge-blocking defects and checked all 30 generated queues, binary/source identities and the 78 receipts. The reviewer did not rerun emulator tests. Physical hardware remains unverified; the owner did not specify a test platform or duration. The pre-approval ZIP and its receipt remain immutable snapshots.
