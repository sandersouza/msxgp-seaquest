# Original HUD and ordered PSG sound

Issue [#13](https://github.com/sandersouza/msxgp-seaquest/issues/13) integrates
the original score/font/leading blanks, reserves, rescued divers and flash,
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

The measured implementation uses a64KiB ASCII16 cartridge, unexpanded64KiB RAM,
16KiB VRAM, standard Z80, TMS9918A SCREEN2 and the standard PSG. The initial32KiB
ROM target overflowed1,536bytes before audio even after unused source code was
removed. Expanded enemy bitmaps in two ROM banks recover the required CPU time.
Code remains in fixed bank0; every temporary enemy-bank transfer restores the
source/art data bank before returning. No runtime6502 interpreter is present.

Original glyphs shift one MSX pixel right to align six projected source glyphs
with nine tiles. Score/lives start atY0/8, all colored sky rows are retained with
blank gaps compressed, actor geometry stays unchanged, oxygen starts at152,
divers at160 and logo at176. The original full160-pixel viewport policy removes
the TIA HMOVE strip. TIA hue/luminance maps to fixed TMS indices; analog RGB is
not claimed identical. Seed-dependent water rows are projected independently.

Two name tables at1800/1C00 alternate. Names/patterns prepare into inactive
storage; VBlank flips R2 and commits changed colors/SAT. Six normal enemy colors
are resident, with a mutable fallback for other attract backgrounds. Player1's
font is resident; player2 has resident outer tiles/life icons and two banks of
three middle-glyph slots. A changed score can upload24bytes while the prior font
bank remains visible. The sweep explicitly forces all three uploads.

The established192 enemy-pattern bytes and352 display bytes per frame remain;
one extra4-byte SAT entry restores the oxygen border when three colors share a
TMS row. Nine SAT entries never exceed four active sprites per scanline. Its
last32-byte pattern occupies3FE0..3FFF. Generated HUD data/cache useD000..EF0F;
the streamed renderer's unusedCC00 staging page holds the source-color slot
lookup. F000..F2FF and stack guards remain checked.

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

`make presentation-check` runs39,328 integrated source-state/pixel cases,
240paced frames, the focused font/palette/water sweep and the ordered PSG
contract. `make presentation-natural` builds the cold cartridge and runs a
device-only replay with no game-RAM reloads. The replay compares every update
against original CPU instructions and original TIA contacts. Alerts, firing,
diver sounds, death, refill and full-bonus chains are also checked from seeded
source scenarios; naturally collecting six divers is not claimed.

The display oracle uses original ROM/ALE pixels and canonical source state,
not generated target HUD caches. Every independently seeded renderer case
warms both display caches using two F00E display-only preparations, then restores
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
