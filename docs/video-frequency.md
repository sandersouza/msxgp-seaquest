# Video cadence and compatibility (issue14)

The verified Atari2600 NTSC4K input is the gameplay clock authority. Its SHA256
is `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
`scripts/video_reference.py` measures the actual Stella raster length, rather
than treating ALE's cropped image height or host frame-skip as the source clock.
It requires ALE0.12.1 because its inspected serialization layout is versioned.

## Timing policy

The original produces262 scanlines and increments source81 once per frame in
the6,000 idle/fire/directional observations. Each scanline takes76 source CPU
cycles; one source update spans19,912 source cycles. With the nominal MSX
3,579,545Hz clock, the matching source period is59,736 Z80 cycles (59.9227Hz).

Standard MSX1 BIOS IDBYT1 bit7 selects the fixed VDP refresh standard. NTSC
TMS9918A/9928A uses one source update per262-line physical frame. PAL TMS9929A
uses313-line frames of71,364 Z80 cycles (50.159Hz). A fractional accumulator
adds51 for each rendered PAL frame and schedules an additional source update
when it reaches262. Every262 PAL display frames therefore advance313 source
updates, with no accumulating slowdown or fixed6:5 rounding error.

All source instructions, logical raster contacts, input samples and ordered
audio stores run for every update. The additional update omits presentation;
every rendered frame retains all actors,192enemy-pattern bytes and352name/display
bytes. Its contacts are acquired from the preceding complete source state after
render preparation; its source core executes after the next VBlank commit.
The following ordinary update acquires fresh contacts from that result.

This preserves mean simulation speed and source phase order, with different
presentation and input sampling intervals. PAL groups some updates close
together and shows fewer intermediate states. It does not reproduce an NTSC
event's exact wall-clock onset or identical input latency. No TMS9929 refresh
register, expansion, turbo or alternate simulation is used.

## Validation in progress

The private harnesses use separate headless openMSX processes and matching ROM/
symbols under ignored `outputs/video/`. The owner's visible issue13 session and
its cartridge files must remain untouched. Builders run serially.

- Identify source raster/update cadence with `scripts/video_reference.py`.
- Compare every source update, including updates without presentation, against
  original CPU instructions; compare logical contacts before each update.
- Check continuous attract palette transitions, source clock over262 frames,
  original pixels/all actors, ordered PSG stores, VBlank commits, VRAM access
  spacing and guarded RAM/stack on both refresh standards.
- Exercise dense states and real keyboard/joystick event latency separately.
- Re-run applicable presentation regressions, original-free CI and independent
  read-only review before delivery. Record exact machine/tool/ROM identities.

The initial128KiB ASCII16 cartridge remains necessary for the measured original
palette/pattern catalog. RAM remains64KiB and VRAM16KiB. Physical hardware,
full-game acceptance and subjective PSG timbre remain issue15 work.

## Primary timing sources

- [ALE0.12.1 TIA serialization](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/v0.12.1/src/ale/emucore/TIA.cxx#L293-L307)
  identifies the recorded full-raster scanline field.
- [TI TMS9918A/9928A/9929A Data Manual](https://www.bitsavers.org/components/ti/TMS9900/TMS9918A_TMS9928A_TMS9929A_Video_Display_Processors_Data_Manual_Nov82.pdf),
  section2.1.5/table2-2, specifies the common2microsecond access window after
  vertical refresh. The existing fast paths remain confined to measured VBlank
  commits or physical display-off; active display retains29cycle spacing.
