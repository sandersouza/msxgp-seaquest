# Issue13 verification

This records the initial delivery baseline at5a797b6. The current owner-authorized
MSX font refinement and its acceptance are recorded [separately](fonts/verification.md).
Check out5a797b6 to reproduce the old hashes below; the current default build
includes the refined fonts.

Local automated acceptance is complete for the frozen128KiBASCII16 candidate.
Independent read-only review found no remaining material issue after corrections.
Remote CI/integration is tracked in [PR29](https://github.com/sandersouza/msxgp-seaquest/pull/29).
This is presentation/native-contract acceptance, not a full-game release or
physical/PAL validation; #14 and #15 retain those boundaries.

Environment: openMSX21.0/C-BIOS_MSX1, NTSC standard3579545Hz Z80,
64KiB RAM/16KiB VRAM. Python3.14.7, sjasmplus1.24.0 revision
`d379eeac9ad3857fb48fd3a3929175d0a56038ce`.
Atari2600 NTSC4K reference SHA256:
`fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.

| Check | Reproduced result |
|---|---|
| Full native/input/collision/oxygen/progression/pixels |39,328cases; max59,110/59,736cycles,626free |
| Paced dense normal case |240frames, zero skips; max57,190busy/1,732commitcycles |
| Focused HUD/font/palette/ripple/all8sprites |1,129cases,24-byte triple-glyph upload forced; R1/R7 and visible VRAM unchanged before commit |
| Real continuous attract boundaries/exits |183×112=20,496source updates;2,745RGB/all8spriteframes; zero skips/visible commits |
| Forced cache generation rebase |183×112=20,496updates;180actual rebases;2,745RGB/spriteframes; zero skips |
| Prepared token240 across activation/next epoch |183×384=70,272updates;139rebases;9,723READY1/token240 prefetch entries;5,490RGB/spriteframes; zero skips |
| All continuous attract modes |max59,583/59,736busycycles,153free; max10,324commitcycles |
| Ordered source/PSG |7,982ticks/34,692stores/44observed source sites;2,400persistent chain ticks |
| Cold device-only original CPU/TIA/HUD/PSG |6,422updates;15,807sound stores; noRAMreload/skip; max49,007busycycles |
| Native clear/RNG/core |2,963cases, including all256initial zero-clear X values |
| Actual keyboard/joystick/held fire |5,660cases, bothplayers/ports and16/26-tick firing |
| Collision |40,748cases/20,374original TIA contacts |
| Oxygen/rescue |24,605cases/6,192chained ticks/768source raster alarm cases |
| Score/progression |55,243cases/8,800chained ticks/25,072score register/flag checks |
| Omitted display dependency audit |264source executions; onlyB0..B6/F8/F9 read before overwrite |
| Host checks |48pass in reference environment; public synthetic CI runs48 with one optional py65 skip |
| Public synthetic CI locally |all original-free ROM/input/collision/audio assemblies pass |

Timed cartridge SHA256:
`0942a040aa4bc4cb72df7db39445c2f96f237719bf8e63d1ed962ca13eca0910`.
Cold controls/playtest cartridge SHA256:
`f6b8e010db183e31f76533763fd195c452dc7933aff9c0ff51bb0b2a51b169c3`.
Both are131,072bytesASCII16 and differ by bootstrap/build variant. No original
ROM, generated art/table or playable cartridge is published. Named local artifacts
remain ignored; concise JSON summaries beside this document identify each run.
The renderer summary drops the obsolete64KiB rom_padding field and derives the
source-bank gap from matching saved symbols:0bytes before9B00 helpers.
The9900/9A00 pages contain live window-pointer tables, not padding.
Fixedbank0 has117padding bytes. Stack minimumF370 and memory/VRAM guards pass.

## Continuous transition evidence

The former64KiB version's true attract boundary reached123,526total/57,781commit
cycles despite passing normal steady-palette checks. The final backend prepares
exact palettes/hidden fonts/colour spans over prior updates; every source update
and all192enemy-pattern/352display-name bytes remain. Its timing proof includes
all129A2counter boundaries, B/W, multiple A3/player windows, and keyboard/Reset/
Select at oldphaseFE/FF/00. Attract priming only supplies the initial display;
each112/384-update chain then runs without RAM reloads from one real cold-replay
game-over seed. Rebase tests only advance the serial and explicitly exercise a
READY1palette containing token240 before the next epoch. No target cache supplies
the RGB/native oracle. Isolated synchronous projection fixtures are not the
paced-transition timing workload; their maximum65,105cycles is reported in the
focused JSON rather than mislabeled as a paced-frame pass.

Active-picture VRAM data accesses retain at least29cycles; display-disabled
copies use18cycles. VBlank uses12cycle uniformOUT/18cycleOUTI and its maximum
commit remains inside the documented4.3ms no-wait refresh window. See primary
sources and the exact adaptation in [HUD/audio contract](../../docs/hud-audio.md).
The external MSX border follows R7water. Opaque black stays1; source86divers/
hostile shots and92surface ripple retain visible contrast against90water.

Independent read-only review also compared16,384original-CPU cases for each new
F644/F875/F8DE/F992 native fold, including ordered stores and final A/X/Y/carry.
It caught/fixed the patrol/oxygen pattern63 collision, wrong font-memo player
selection and READY1pending-token rebase hazard. Every incoming entry into a
folded body is guarded. These review arithmetic checks supplement the executed
Z80/native regressions; they do not replace them.

## Audio and cold replay limits

Sound negative control from the first implementation changed PSG8 after a hook
and was rejected immediately; clean ordered contracts are reproduced again on
the final hash. Hooks preserve registers/stack/IFF, PSG7 peripheral directions
and PSG15 on every store. Source frame epochs and event order match; analog
amplitude, oscillator phase, TIA polynomial/noise and timbre remain approximate.

Cold replay observed16deaths,14death-driven switches,13attract swaps,2gameovers,
1restart and all4difficulty settings. Maximum event-to-state18.1523ms and completed
SAT30.8844ms exclude host/physical input and visible scanout. Initial37,509cycle
cache preparation runs with R1disabled; subsequent visible frames are timed.
Natural six-diver collection/full-game completion are not claimed: full bonuses
and other late transitions use continuous seeded source chains. PAL/source-cadence
policy and physical-machine release acceptance remain #14/#15.

## Reproduce

With the documented local original inputs and pinned tools:

```sh
make presentation-check
make native-contract input-contract collision-contract oxygen-contract progression-contract
.venv/bin/python -B -m unittest discover -s tests
bash scripts/ci.sh
```

Run serially: builders share ignored outputs. `presentation-check` first builds
and records the cold controls replay, then runs the39,328/240paced suite, focused
sweep, all three continuous attract modes and ordered audio. Save named matching
ROM/symbol pairs before portable CI overwrites renderer build outputs.
`make presentation-run` opens the controls cartridge; arrows move, Space fires,
F1Reset/start and F2Select. The owner playtest copies are preserved separately.
