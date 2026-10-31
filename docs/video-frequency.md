# Video cadence and compatibility (issue #14)

The verified Atari 2600 NTSC4K input is the gameplay clock authority. Its SHA256
is `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
`scripts/video_reference.py` measures the actual Stella raster length, rather
than treating ALE's cropped image height or host frame-skip as the source clock.
It requires ALE 0.12.1 because its inspected serialization layout is versioned.

## Timing policy

The original produces 262 scanlines and increments source `$81` once per frame in
the 6,000 idle/fire/directional observations. Each scanline takes 76 source CPU
cycles; one source update spans 19,912 source cycles. With the nominal MSX
3,579,545 Hz clock, the matching source period is 59,736 Z80 cycles (59.9227 Hz).

Standard MSX1 BIOS IDBYT1 bit 7 selects the fixed VDP refresh standard. NTSC
TMS9918A/9928A uses one source update per 262-line physical frame. PAL TMS9929A
uses 313-line frames of 71,364 Z80 cycles (50.159 Hz). A fractional accumulator
adds 51 for each rendered PAL frame and schedules an additional source update
when it reaches 262. Every 262 steady PAL display intervals therefore advance 313
source updates, with no accumulating slowdown or fixed 6:5 rounding error.
The initial empty preparation pipeline has a bounded one-update phase offset;
the first display interval is excluded from sliding clock-window checks.

All source instructions, logical raster contacts, input samples and ordered
audio stores run for every update. The additional update omits presentation;
every rendered frame retains all actors, 192 enemy-pattern bytes and 352 name/display
bytes. Its contacts are acquired from the preceding complete source state after
render preparation; its source core executes after the next VBlank commit.
The following ordinary update acquires fresh contacts from that result.

This preserves mean simulation speed and source phase order, with different
presentation and input sampling intervals. PAL groups some updates close
together and shows fewer intermediate states. It does not reproduce an NTSC
event's exact wall-clock onset or identical input latency. No TMS9929 refresh
register, expansion, turbo or alternate simulation is used.

Normal paced iterations have already consumed their previous VBlank status.
They poll the next status directly: a blind preliminary read could discard a
newly arriving edge near the NTSC deadline. The first paced entry still clears
old status. The palette bootstrap clears its stale latch once, after initial
preparation with the physical display off. Earlier non-palette diagnostic
variants retain their original startup path.

## Validation

The private harnesses use separate headless openMSX processes and matching ROM/
symbols under ignored `outputs/video/`. The owner's visible issue #13 session and
its cartridge files must remain untouched. Builders run serially.

The [verification record](../references/video/verification.md) contains exact
ROM/tool/machine identities, all scenarios and command-by-command reproduction.
The fresh video matrix verifies 514,802 source updates and 449,644 display frames;
all 210,426 steady clock windows pass. Worst measured busy loads are 58,800 of
59,736 cycles in NTSC and 67,300 of 71,364 in PAL. All actors, original source
updates and ordered audio stores are retained. Measured cold input-to-SAT maxima
are 30.8782 ms NTSC and 37.5968 ms PAL; host input and visible scanout are excluded.

The initial 128 KiB ASCII16 cartridge remains necessary for the measured original
palette/pattern catalog. RAM remains 64 KiB and VRAM 16 KiB. Physical hardware,
full-game acceptance and subjective PSG timbre remain issue #15 work. The
owner-approved score/OXYGEN lettering from PR #30 is included; source gameplay
and the original alarm/raster model remain unchanged.

## Primary timing sources

- [ALE0.12.1 TIA serialization](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/v0.12.1/src/ale/emucore/TIA.cxx#L293-L307)
  identifies the recorded full-raster scanline field.
- [TI TMS9918A/9928A/9929A Data Manual](https://www.bitsavers.org/components/ti/TMS9900/TMS9918A_TMS9928A_TMS9929A_Video_Display_Processors_Data_Manual_Nov82.pdf),
  section 2.1.5/table 2-2, specifies the common 2 microsecond access window after
  vertical refresh. The existing fast paths remain confined to measured VBlank
  commits or physical display-off; active display retains 29 cycle spacing.
