# Issue #12 verification

Reference: manifest-verified NTSC/4K Atari2600 ROM, SHA-256
`fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
openMSX21.0/C-BIOS_MSX1, standard3,579,545Hz Z80, NTSC,64KiB RAM/16KiB VRAM,
no expansions. Python3.14.7, py65 1.2.0, ALE0.12.1/Stella; sjasmplus
`d379eeac9ad3857fb48fd3a3929175d0a56038ce`.

| Probe | Passing evidence |
|---|---|
| Direct original/native score and player routines |25,266 records:20,000 low-operand pairs/carries;3,024 upper boundaries;2,048 terminal byte/carry/reserve/A3 cases;194 seven-field swap/selection cases |
| Score return registers/flags |25,072 A/X/Y/C/N/Z comparisons, including79+01→80/N=1 |
| Integrated progression transitions |21,177: real contacts/double scoring/death/life crossings, bonus caps/overflow, all256 groups/waves, patrol phases, death completion and attract |
| Seeded continuous chains |8,800 ticks across8 starts;8,792 continuations without game-RAM reload; four difficulty profiles, player exhaustion/Reset/Select and late full bonuses |
| Total progression contract |55,243 records; stackF370, intact guard, IFF disabled, VDP IRQ masked and PSG15 restored |
| Omitted original display input audit |264 source executions, including48 real contact states; reads before core overwrite are B0..B6/F8/F9 |
| Full native/input/collision/oxygen/progression/pixel sweep |39,328 cases; maximum59,311/59,736 cycles,425 free |
| Pacing /visible commit /VRAM data spacing |240 frames without skips;59,204 busy max;11,039 commit max;29-cycle minimum spacing |
| ROM /padding /sprite VRAM |32KiB /1,536 bytes /2,016 of2,048 bytes |
| Cold-boot device-only progression |6,262 updates; no game-RAM reloads; every update compared with original CPU, occupancy and Atari TIA |
| Natural events after controller start |16 deaths;14 death-driven player switches;13 attract switches;2 game overs;1 restart; both players and all4 independent difficulty combinations |
| Natural frame /latency measurements |54,771 busy max; no skipped VDP frames;17.5991ms event→state,29.7739ms event→completed SAT maximum |
| Native /real input /collision /oxygen regressions |2,707 /5,660 /40,748 /24,605 records;20,374 original TIA collision and768 alarm scenarios |
| Graphics authority /synthetic public checks |647 original shape scenarios plus299 edges /39 host tests and all local CI builds |

Timed integration ROM SHA-256:
`4c6f9d1f152708c9971fcfdf2d890824b096bdec16736953f3257f8022f4c8fe`.
Cold-boot controls ROM SHA-256:
`1cfd70275c6fd22ea4f169f2864c2054836b86394a415abe6f9de918769bc61f`.
Named ROMs/symbols and raw evidence are retained locally in
`outputs/progression/final-render/` and `outputs/progression/final-natural/`.
Other generated outputs may subsequently be overwritten by synthetic CI.

## Cost correction and fidelity

The expanded late-game density sweep exposed90 over-budget cases, maximum64,981
cycles. A terminal-only optimization left23 ordinary diver-payout overruns.
The final source score-block specialization retains each individual call and its
ADD/ADC/DAA event order, low/middle/high observable stores, reserve checks and
returns. It omits identity high stores when middle addition cannot carry, and
dead score stores when already saturated. No intermediate observer exists under
DI and this source block has no calls or I/O. No enemy, pixel, transfer, visibility
or simulation frequency was reduced. The original64,981-cycle fixture now takes
58,291; an ordinary60,991-cycle fixture now takes57,977. The global maximum is
still bounded by the earlier59,311-cycle controls workload.

Returned-status checks exposed the previous binary-N restoration error at79+01.
The no-carry score exit now derives NMOS N/Z from adjusted A; carry paths redefine
N/Z before their source consumers. The specialized block preserves X/Y and source
carry in E. Unsupported external entries into the folded score body are rejected.

The intentional running-Z80 BA corruption fails at the first record: expected0,
actual1. The subsequent normal55,243-record run passes. The display audit is dynamic
dependency evidence, not a hardware geometry proof; collision and natural TIA
checks supply that independent authority. All source-derived records/art/ROMs/
listings/replay snapshots remain ignored. Public JSON contains metadata only.

## Reproduce and limits

See [phase, controls and commands](../../docs/scoring-progression.md).
`make progression-natural` first rebuilds the actual-device input contract and
its cold-boot replay seed, then uses only keyboard/joystick events. Its controller
starts at17 emulated seconds and alternates dives/ascent to exhaust both players,
restarts once, then leaves the subsequent game-over/attract flow running. The28
total player toggles include14 deaths,13 attract swaps and one reset; only the14
death switches are used as alternating-gameplay acceptance.

Natural late-game caps/full bonuses were not reached. Those are separately
identified seeded continuous chains, not relabeled natural gameplay. The named
fixture sweep is not a proof of all reachable frame costs. HUD/background remain
synthetic; PSG playback/timbre, full-game, PAL, physical scanout/input latency and
physical MSX acceptance remain #13–#15. Independent review is recorded separately.
