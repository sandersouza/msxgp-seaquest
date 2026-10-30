# SCREEN 2 renderer feasibility — issue #7

Decision: proceed with a 240-pixel hybrid SCREEN 2 backend on standard MSX1.
The feasibility gate passes on C-BIOS_MSX1/openMSX 21.0. This is a renderer probe,
not a playable game or full-game/physical-machine acceptance.

## Measured configuration and result

Target: 3,579,545 Hz Z80, standard MSX M1 waits, TMS9918A, 64 KiB RAM,
16 KiB VRAM, NTSC, plain 32 KiB cartridge. sjasmplus v1.24.0 commit
`d379eeac9ad3857fb48fd3a3929175d0a56038ce`; Python 3.14.7; ALE 0.12.1.
Reference SHA-256: `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
Exact generated ROM hashes and settings are in [the evidence snapshots](../references/renderer/).
Original-derived native ROMs and dumps remain ignored local outputs.

| Probe | Cases | Worst CPU cost | Verdict |
|---|---:|---:|---|
| Synthetic, all canonical X positions, reflection and crossings | 256 | 43,072 cycles | pixel/SAT comparisons pass |
| Native core plus original enemy rows, existing fixtures and dense mask sweep | 4,238 | 54,179 cycles | canonical RAM and background pixels match |
| Paced native worst case, repeated deterministic fixture | 240 consecutive frames | 54,072 busy cycles/frame | no skipped VDP frames |

The native cases contain 2,190 original tick fixtures plus 2,048 position/mask
stress inputs. There are actual post-core states with all twelve enemies visible.
This gate preserves the original simulation tick; it neither drops enemies nor
throttles the simulation. It does not replace the independent continuous replay
in `make native-contract` (2,707 cases, maximum core-only cost 16,838 cycles).

A VDP frame provides 59,736 CPU cycles. The measured maximum joint case leaves
5,557 cycles (9.3%) for later integration work. This is measured coverage, not
a proof over every reachable full-game state. Collision extraction, real HUD
construction, input and audio must fit and be remeasured in their own issues.

The paced test observes 240 consecutive increments of `VDP_frame_count`.
Commit-start polling jitter gives periods 59,724–59,752 cycles; visible commits
cost 11,501 cycles, begin at display Y192 and finish at Y−20, before the next
active picture. Inactive pattern preparation leaves the previous visible VRAM
signature unchanged for every case. No fifth-sprite status is observed by actual
status-port reads during the paced run. The test reloads a worst-case fixture
each tick to maintain stress; it is not a natural gameplay replay.

## Representation and limits

Canonical coordinates remain original 160-pixel game coordinates. Display X is
`8 + floor(3*x/2)`; canonical repeat spacing 16 becomes 24 display pixels, so
the three copies share phase/parity and six cached 8×8 patterns. Four lanes use
24 generated patterns/192 bytes per tick. Their display rectangle tops are
Y48/72/96/120. The last lane crosses the SCREEN 2 bank boundary at Y128;
the probe checks the split against actual VRAM pixels.

Repeat masks use the original `$A4 & $FEEB[index]` preparation. Copy coordinates
wrap at 256 and clip at canonical 160. The host oracle independently draws
canonical source bits and scales them, instead of using the Z80 expansion LUT.
Original enemy animation pointers and reflection come from the verified ROM;
the synthetic build uses an explicitly synthetic 15-row fixture.

Hardware-only enemies are rejected: three repeated enemies, a lane ball,
two player sprites and the torpedo can require seven hardware slots on one line.
The hybrid uses two player sprites, one torpedo, four lane balls and one patrol.
The patrol's 8-row rectangle goes into pattern rows8–15 of a box at Y22–37;
its visible source pixels map to Y31–37. That box ends before the first ball's
box at Y49–64. Thus player/torpedo plus either patrol or one lane ball require
at most four slots. This corrects the earlier handoff's assumption that the
patrol must be background-rendered.

`scripts/render_reference_probe.py` independently freezes the original through
ALE and measures patrol pixels at raw X64–71/Y46–52 for all three normal player
animation selections. Display translation is raw Y−15. This measurement is
stored in `references/renderer/patrol-geometry.json`; full asset extraction is #8.

The current hardware sprite masks and HUD contents are synthetic fixtures.
Their SAT positions, pattern numbers, nonzero colors, terminator and occupancy
are checked in every VRAM snapshot. The actual pattern table is preloaded once,
and all 64 HUD name bytes plus all eight SAT entries are transferred every tick,
including when unchanged, so their transfer cost is included. Original sprite
silhouettes, animation banks, palette, clipped edge variants and real HUD content
remain #8/#13 work. These must preserve the tested slot/transfer contract or
trigger a new budget measurement. The probe does not establish their pixel fidelity.

## VRAM, RAM and synchronization contract

SCREEN 2 pattern/color/name/SAT/sprite-pattern areas remain at BIOS defaults
`0000/2000/1800/1B00/3800`. Alternate enemy cache tile IDs are 32–55 and 96–119.
Prepare uploads only the inactive cache. Commit uploads four 64-byte name strips,
two 32-byte HUD rows and the 32-byte SAT: 352 bytes. Total steady transfer is
544 data bytes/frame (192 patterns plus 352 visible commit bytes).

`OUTI; JP NZ` gives 29 cycles between data writes on the standard MSX Z80.
The harness measures that minimum across 2,305,472 native data writes. It uses
the [openMSX debugger interface](https://openmsx.org/manual/commands.html),
rather than treating correct final VRAM alone as proof of safe access spacing.
openMSX itself notes that its access tester does not replace physical testing.

The backend requires interrupts disabled during preparation/commit; its fast
clear temporarily points SP into the name buffer. BIOS input/audio integration
must respect this contract. The ROM maps its second cartridge page explicitly
through BIOS ENASLT, including expanded-slot bits.

| RAM range | Purpose |
|---|---|
| C000–C3FF | native canonical/hardware shadow, 1,024 bytes |
| C402–C412 | renderer scratch (holes allowed) |
| C500–C507 | four source-row pointers |
| C6F0–C6FF | benchmark call parameters |
| C7FD | benchmark boot signature |
| C800–CAFF | 768-byte name staging buffer |
| CC00–CCBF | 192-byte enemy pattern buffer |
| CE00–CE7F | 128-byte SAT initialization buffer; 33 bytes live |
| CF00–CF3F | two 32-byte HUD staging rows |
| F374–F37F | observed native stack footprint; initial SP F380 |

Allocated state fits within C000–CF3F (3,904 bytes including holes), plus stack.
The paced test poisons D000–F37F after boot, requires D000–F2FF to remain intact,
and records the stack high-water mark. BIOS workspace at F380 and above is not
used for game buffers. Real interrupt/input routines need their own stack test.

## Reproduce and failure controls

```
make render-bench
make render-native-bench
.venv/bin/python -B scripts/render_reference_probe.py
make native-contract
bash scripts/ci.sh
```

`outputs/render/{synthetic,native}.rom` and result JSONs are local probe artifacts.
The scripts lock shared output directories, require fresh completion counts,
bound emulator processes, compare all 4,238 native states and decoded images,
check inactive-cache visibility, and enforce the measured frame budget.

`SEAQUEST_RENDER_INJECT_PIXEL=13 make render-bench` intentionally fails at
case13 pixel(0,0): actual1/expected0. This verifies that the comparison detects
an actual VRAM error. Run the normal command again after this negative control.
Public CI assembles only the synthetic renderer probe and original diagnostic;
it cannot establish local reference equivalence or emulator timing.

Independent review checked phase/wrap/bank addressing, the eight-slot layout,
VRAM/cache separation and harness evidence. Its AF-marshalling finding was fixed:
the input accumulator belongs at C6F1, above the flags byte at C6F0.

PAL/50 Hz scheduling, natural controls, full gameplay, real original sprite/HUD
pixels and physical machines remain unverified here and have later issue gates.
