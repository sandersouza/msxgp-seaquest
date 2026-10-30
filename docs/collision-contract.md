# Original raster contacts and lane integration — issue #10

`make controls-run` now acquires original raster contacts before each native
F5B8→F00E update, including after Reset and Select. The original translated lane
motion, fractional accumulators, seed advancement, spawns and ordered resolution
remain the gameplay authority. No new lane, random or hit-resolution algorithm
replaces the source instructions.

## Acquisition contract

The local manifest-verified NTSC 4K Atari2600 ROM is the authority. Its display
preparation and kernel at F00E–F3B3 determine occupancy; acquisition changes only
B0..B6 and F8. Canonical player coordinates remain X21..134/Y13..108. MSX scaling,
clipped sprite variants, palette and the TMS sprite-collision flag do not feed
back into collision or movement state.

The source CXCLR windows, GRP/reflection masks, doubled P0 width, eight-pixel M0,
per-row ball motion/width and repeated P1 copies are retained. The four lanes
overwrite shared B4/B5/B6 latches in descending3→0 order; B0 retains one result
per lane. F8 records the separate surface window. Its unused low bits read as7
on the source bus; bit7 carries the patrol contact. Source resolution subsequently
handles pickup/hostile ball, missile/enemy, enemy/ball and player/enemy in its
original order, including contact points and simultaneous-hit priority.

Two source details are particularly easy to lose:

- A zero clipped repeat mask still positions one P1 copy at X0. The HMOVE bar
  hides X0..7 in video, but those pixels still participate in collision latches.
  Right-edge object pixels wrap in the TIA's160-pixel domain; repeat coordinates
  first preserve the source byte wrap. X0/inactive balls and missiles also remain
  source hardware geometry; the original resolution applies its own guards.
- With no death, CPY #2 in the lives kernel supplies carry: zero/one reserve
  selects patrol rows11..4. Death counters1..9 also clear carry, while10..23
  replace it with set carry. Set carry selects rows12..5 at raw lines45..52. Collision
  and display both preserve this early-death variant. It uses an existing inactive
  scratch slot; resident/scratch VRAM allocation is unchanged.

## Independent checks

`scripts/collision_reference.py` computes source-coordinate pixel-set intersections.
`scripts/collision_contract.py` compares those results to latches collected by the
unmodified original ROM in ALE/Stella. It freezes raster inputs through the original
bonus early exit. The Z80 then acquires contacts from the same state with poisoned
latch outputs; every other canonical byte must remain unchanged. A second pass
executes normal native resolution and compares all251 shadow bytes with a separate
py65 original 6502 execution.

Fixtures include all 256 base coordinates and eight repeat masks, all reachable
enemy selections and shark offsets, both reflections, every legal player Y,
early-death/surface windows, clipping and circular edges, source seeds/waves,
zero/one-reserve patrols with no death and the reserve/death carry override,
explicit simultaneous contacts, six-diver pickup suppression and patrol contact
in normal/refill/bonus states. Unused source animation pointers3/7 are excluded
from collision authority. The earlier graphics-only probes still exercise their
explicit artificial15-row rectangle; the collision timing sweep substitutes
reachable frames while retaining those fixtures' positions and density.

The continuous cold-boot replay uses actual openMSX keyboard/joystick events and
does not reload game RAM. It captures state before acquisition and before the
native update, compares acquired latches with both occupancy and Atari TIA,
then compares the complete native update with the original CPU. Isolated input
RPC tests continue to supply neutral contacts so the input adapter can be tested
independently.

## Cost and reproduction

The32 KiB cartridge retains BIOS page0,64 KiB RAM/16 KiB VRAM and standard-speed
MSX1 operation. Local generated tables share identical projection rows and store
enemy/ball overlap bitsets. The renderer's collision build caches expanded source
rows FDA4..FDF8 by parity/phase/reflection in32 pages. Stack stores gather those
rows into the same48-byte lane buffer with interrupts disabled and restore SP
before returning. Short fixed VRAM transfers retain29-cycle data spacing and the
same192 pattern bytes/352-byte visible commit. Visible pattern banks are never
overwritten during preparation. Frame-specific verified zero tails avoid processing
empty source player rows. None of these changes reduces objects or tick frequency.

| Current check | Result |
|---|---|
| Atari TIA acquisition / native acquisition+resolution |20,374 /40,748 cases |
| Full-density collision/input/graphics |10,622 cases;59,370/59,736 cycles |
| Paced worst fixture |240 frames without skips;59,263 busy cycles |
| Visible commit / minimum port spacing |11,039 /29 cycles |
| Remaining CPU /32 KiB cartridge padding |366 cycles /1,536 bytes |
| Cold boot, actual controls and Atari/CPU comparison |659 updates, no RAM reloads or skipped VDP frames |
| Natural maximum busy work |55,284 cycles |
| Event→state / completed SAT upload |17.5734 /29.7795 ms maximum |
| Input / native CPU / graphics regressions |5,660 /2,707 /6,526 cases |
| Isolated neutral-contact input/renderer regression |9,598 cases;58,757 cycles |
| Synthetic host checks |36 tests and local public CI pass |

The timed collision probe SHA-256 is
`0990365dec54574eb3a17ead3838dd8d064a1d4049052e5c957211bb55ab14f2`.
The continuous controls/collision cartridge SHA-256 is
`c6fd8c4271d160527ed6e0e3f5459f4eda1fbaa56e66a55d8eb28989da411dee`.
Both use openMSX21.0/C-BIOS_MSX1, NTSC,64 KiB RAM and 16 KiB VRAM.
The paced minimum stack is F370 and the RAM guard is intact. These measurements
bound the named fixtures, not every reachable state; CPU margin remains tight.
Latency measures device replay events to state/SAT completion, excluding host OS,
physical input hardware and visible scanout.

```
make collision-contract
make render-collision-bench
make input-natural
make native-contract
make graphics-reference-check
make render-graphics-bench
bash scripts/ci.sh
```

Negative control (must fail, then rerun the normal contract):

```
SEAQUEST_COLLISION_CORRUPT=1 make collision-contract
```

It changes the acquired B6 lane in the running Z80 backend. Exact hashes,
versions, measured results and independent review belong in
`references/collision/`. Original-derived tables, art, ROMs, listings and replay
snapshots remain ignored under outputs/. Public CI assembles synthetic collision
data and needs no originals; its artifacts contain only the existing synthetic
diagnostic. HUD/background composition remains synthetic. Audio, full-game,
PAL and physical MSX acceptance remain separate work.
