# Oxygen, rescue and refill — issue #11

The controls diagnostic runs the original oxygen, pickup, surface, death, refill
and bonus instructions in the translated F5B8→F00E core. The omitted raster block
F44F→F473 now supplies F9 before every integrated update, including the first
update after Reset/Select. It uses the preceding update's Y, oxygen and death
state: F9=15 when Y≠13, oxygen is1..16 and death is zero; otherwise F9=0.
The old frame's bit4 affects HUD color, not the logical alarm. Pickup sound,
bonus, death and refill may subsequently clear F9 in their original order.
PSG playback/timbre and the oxygen bar's visual composition remain #13.

## Ordering and boundaries

- Surfacing is checked before movement. Up from Y14 first arrives at Y13;
  surfacing consequences occur on the following update. Oxygen64 bypasses the
  rescue/penalty check even with divers aboard.
- At oxygen below64 and Y13, zero divers starts death23. One..five divers use
  the original even-phase refill, block movement until completion, remove one
  diver and increment the wave byte. Completion can then admit held controls.
- Six divers sets E8=6; the next tick takes the bonus branch. Oxygen units score
  on even new phases; divers score on phases divisible by16. No normal movement
  runs during bonus. Completion advances groups, conditionally increments the
  wave once, clears lanes and enters refill. Byte wrap is preserved.
- Oxygen drain follows player movement/firing: Y≥20 and new frame divisible by32.
  Thus Down19→20 can drain immediately and Up20→19 avoids that tick's drain.
  Decrement to zero starts death23. F9 uses the earlier raster state, not the
  post-movement/decrement values.
- Real raster contacts still resolve in the source order, including pickup
  limits, hostile shots, simultaneous enemy/player/ball/missile contacts and
  patrol contacts during refill. No collision or transition state machine was
  substituted for the source instructions.

## Verification

```
make oxygen-contract
make render-oxygen-bench
make oxygen-natural
make collision-contract
make native-contract
make graphics-reference-check
make render-graphics-bench
make render-input-bench
bash scripts/ci.sh
```

The oxygen contract executes the omitted original HUD instructions on py65 and
checks them separately against Atari/Stella raster execution. It poisons F9,
covers every oxygen byte, all256 phases, Y13/14/19/20/108, death,0/1/5/6 divers,
simultaneous real contacts, capped pickups and ascent followed by the next tick.
Seeded chains retain native game RAM and use BIOS-sampled controls throughout
depletion/death, partial/full rescue, bonus, wave wrap and refill completion.
They are distinguished from the cold-boot natural replay, which never seeds or
reloads game RAM. The latter retains Reset/Select/difficulty/joystick tests, then
uses keyboard device input to pursue rescues and oxygen depletion.

The complete renderer probe includes low-oxygen and rescue states alongside
full-density clipped graphics, original collisions and actual keyboard input.
Right-edge name writes use direct one/two-column paths for the same tile indices
and pixels; objects, update frequency, transfer volumes and inactive banks are
preserved. This addresses a frame overrun exposed by the longer natural replay.

Exact results, hashes, machine/settings and review evidence belong in
`references/oxygen/`. Original-derived data, assets, ROMs and replay dumps remain
ignored under outputs/. Public CI assembles the alarm adapter with synthetic data.
Synthetic HUD/background, audio, full-game, PAL and physical MSX acceptance remain
explicitly outside this diagnostic's evidence.

Negative control (must fail; rerun normally afterwards):

```
SEAQUEST_OXYGEN_CORRUPT=1 make oxygen-contract
```

This changes the running Z80's F9 output. Expected state comes from original
instructions and cannot be supplied by the corrupted native alarm.
