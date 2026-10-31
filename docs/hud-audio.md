# Original HUD and ordered PSG sound

Issue [#13](https://github.com/sandersouza/msxgp-seaquest/issues/13) integrates
the source-owned score/leading blanks, reserves, rescued divers and flash,
oxygen gauge, Seaquest/Activision logo transition, sky/water/seabed, and sound.
The local reference remains the verified NTSC4K Atari2600 ROM. No original
ROM, extracted bitmap, generated font table or playable cartridge is published.

Use `make presentation-run` with the documented local inputs. The cartridge
boots directly into the original start/attract flow, reads the existing keyboard
and two joystick controls, and uses original gameplay/collision/oxygen/scoring
logic. `make run` still opens the portable synthetic hardware diagnostic.
Full-game release acceptance, reference cadence/50Hz policy and physical machines
remain the work of #14 and #15.

## Hardware and presentation

The implementation uses a128KiB ASCII16 cartridge, unexpanded64KiB RAM,
16KiB VRAM, standard Z80, TMS9918A SCREEN2 and the standard PSG. The initial32KiB
ROM target overflowed before audio; a64KiB intermediate version then took over
123,000cycles during real attract colour transitions. The128KiB layout stores
exact prepared palettes and bounded native colour collectors. Enemy bitmaps
retain their two expanded ROM banks. Fixed bank0 owns mapper-changing helpers;
source code/data run in bank1, and every temporary mapping restores bank1 before
returning. No runtime6502 interpreter is present.

Score/lives start atY0/8, all colored sky rows are retained with
blank gaps compressed, actor geometry stays unchanged, oxygen starts at152,
divers at160 and logo at176. The original full160-pixel viewport policy removes
the TIA HMOVE strip. TIA hue/luminance maps to fixed TMS indices; analog RGB is
not claimed identical. Seed-dependent water rows are projected independently.

The owner requested an MSX lettering refinement after the original presentation
delivery. Score digits now use an authored8x8 mask in each existing12x8cell,
with even two-pixel stems, balanced round digits and consistent four-pixel gaps.
This removes the alternating stroke widths from3:2 horizontal enlargement.
OXYGEN uses six complete6x7glyphs in its existing six8x8tiles. Its bottom row
closes O/G/E instead of being cut by the old five-line source sampling window.
Leading-zero blanking, values, player colours, life/diver/logo art and oxygen-bar
geometry remain source-owned. The display oracle applies these two explicit
font adaptations; the original Atari HUD/alarm reference remains unchanged.

The source-font block now has105records instead of106. One reserved player2
padding tile keeps scratchIDs245..250 fixed, and its61-record prewarm bound
includes the padding and all six scratch tiles. Unused uniform colour classes
fill the fixed31-class palette format; RAM/VRAM budgets remain unchanged.

Two name tables at1800/1C00 alternate. Names/patterns prepare into inactive
storage; VBlank flips R2 and commits changed colours/SAT. Seven enemy slots use
six fully warmed foreground colours plus one private fallback. Predictable
attract palettes and hidden glyph colours prepare over preceding updates;
actual canonical state and field pointers validate a prepared result before use.
A default class vector has permanent cache token1, while other exact vectors
receive fresh generations, including canceled prefetches. Token rebasing clears
all physical cache tags before reuse. Forecasting changes presentation only.

Water-coloured pattern nibbles use TMS colour0, with the actual water hue in R7.
This removes the need to recolour every enemy background at a water transition.
Opaque black retains index1. The external MSX border consequently follows the
water colour; active256×192 pixels retain the projected source image. Source86
(divers and hostile shots) and92(surface ripple) retain contrast with90(water).
Only a completely black original scene can disable R1 for preparation; its next
visible image is fully prepared before R1 returns, with no extra black frame.

Player1's font is resident; player2 has resident outer tiles/life icons and two
banks of three middle-glyph slots. A changed score can upload24bytes while its
prior font bank stays visible. The sweep forces all three uploads. Frequent
surface-player images are resident; less frequent and clipped images use two
inactive scratch banks.47 resident patterns plus16scratch reserve hardware
pattern63 at3FE0..3FFF for the oxygen-border overlay. Nine SAT entries never
exceed four active sprites on a scanline.

The established192enemy-pattern bytes and352display/name bytes per frame remain.
Hidden sprite patterns and redundant colour uploads may be skipped; every actor
and original simulation update remains. Generated immutable HUD data occupies
D000..EBFF, colour cachesEC00/ED00, and double RGB buffersEE00/EF00. F000..F2FF,
stack guards, source hardware locations and the RPC area remain protected.

Active-picture VRAM data writes retain at least29Z80cycles between accesses.
Only the paced VBlank commit uses12cycle uniform OUT or18cycle OUTI writes;
fast general copies run only while R1 is physically disabled and accept1..64bytes.
The slow copy dispatch is restored before display enable. TI's original
[Data Manual, section2.1.5, page13](https://peacockmedia.software/tms/TMS9918datasheet.pdf)
specifies2µs accesses during its4.3ms vertical-refresh window; the measured
commits fit that window. The [openMSX original-slot implementation](https://raw.githubusercontent.com/openMSX/openMSX/master/src/video/VDPAccessSlots.cc)
provides the corresponding TMS9918 access-slot model. This is standard-speed
MSX1 operation; turbo CPUs need their own timing policy.

## Sound event policy

The original6502 algorithm still owns counters, onset, duration, priorities and
overlap. Every direct source AUDC/AUDF/AUDV store calls the PSG adapter in the
same order, including an earlier alarm overwritten by a later event in one
update. A single end-of-frame snapshot would lose those transitions.

Hooks preserve AF/BC/DE/HL/IX/IY/SP/IFF, keep PSG7 peripheral directions, never
write PSG15, and return with interrupts disabled. Idempotent masked source
stores do no work. A changed tonal store projects its period immediately; held
inaudible periods survive DC/noise-only modes. The cold indexed hardware clear
is platform initialization; audio starts muted before the original game reset.

For source frequency `n=(AUDF&31)+1`, use the nearest integer AY period:

| Original control | PSG projection | Difference |
|---|---|---|
|0|both tone/noise gates disabled, source volume retained|DC/analog filtering differs|
|4|square, period `round(114*n/16)`|pitch rounded to half a period at most|
|12|square, period `round(342*n/16)`|same rounding, original divide-by-three|
|8|AY noise, period `clamp(round(114*n/32),1,31)`|TIA9-bit versus AY17-bit polynomial; high periods clamp|
|15|square carrier `round(684*n/16)` plus AY noise|explicit POLY5/divide-by-three timbre approximation|

Each source channel maps to PSG A/B with its own volume (`AUDV&15`); C and the
hardware envelope remain disabled. AY has one noise clock: active noisy source0
owns it before source1, while both channels retain their own gates and volumes.
The source event priority is preserved; simultaneous independent TIA noise clocks
and nonlinear amplitude curves cannot be represented exactly. Oscillator phase,
waveform identity and sub-instruction TIA onset are not acceptance claims.

Clock/divider interpretation is supported by the primary implementations and
datasheet: [MAME TIA audio](https://github.com/mamedev/mame/blob/master/src/devices/sound/tiasound.cpp)
and [AY-3-8910 data manual](https://hansotten.file-hunter.com/uploads/files/AY38910.pdf).
The adapter's event delay is measured separately from the source frame epoch.

## Verification and reproducibility

`make presentation-check` first records the cold device replay, then runs39,328 integrated source-state/pixel cases,
240paced frames, the focused font/palette/water sweep,183continuous attract
chains and the ordered PSG contract. A second attract run forces native cache
generation rebasing. `make presentation-natural` builds the cold cartridge and runs a
device-only replay with no game-RAM reloads. The replay compares every update
against original CPU instructions and original TIA contacts. Alerts, firing,
diver sounds, death, refill and full-bonus chains are also checked from seeded
source scenarios; naturally collecting six divers is not claimed.

The display oracle uses original ROM/ALE pixels and canonical source state,
not generated target HUD caches. Every independently seeded renderer case
warms both display caches using F00E display-only preparations (two normally,
48 for isolated attract-boundary fixtures), then restores
the exact input RAM before measured F5B8. Artificial cold inputs with86=0 have
no preceding valid picture: only their presentation preparation uses boot0/FF.
Oxygen fixtures65/255 still compare native canonical bytes exactly, while the
display model clamps them to the reachable0..64 display domain. These fixtures
do not establish original pictures for invalid display states.

Portable CI builds a mathematical audio probe and synthetic graphics/collision
probes without original inputs. The optional synthetic6502 trace test runs when
py65 is installed; reference runtime checks remain local. Evidence, versions,
hashes and remaining acceptance boundaries are in
[presentation verification](../references/presentation/verification.md).
