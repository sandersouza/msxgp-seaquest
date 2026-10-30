# Original controls — issue #9

Issue #9's measurements below retain their delivery baseline. The current
`make controls-run` includes [issue #10 collision acquisition](collision-contract.md);
current combined timing and continuous-replay evidence are in references/collision/.

The controls diagnostic connects MSX input to the existing native gameplay code.
It preserves the original F5B8→F00E update, byte arithmetic, facing, opposing-key
order, unnormalized diagonals, boundaries and held-level fire. No replacement
movement or cooldown algorithm is introduced. This is a controls diagnostic;
collision acquisition, HUD composition, audio and full-game acceptance remain
their own issues.

## Controls and phase

| MSX control | Original input |
|---|---|
| Cursor keys | Directions for the currently active player |
| Space | Held fire for the currently active player |
| Joystick port 1 / primary button | Player 1 directions / held fire |
| Joystick port 2 / primary button | Player 2 directions / held fire |
| F1 held | Console Reset; retains frame phase and PRNG as in the original |
| F2 held | Console Select; original 31-update repeat and selection state |
| F3 press | Toggle player 1 B/A difficulty |
| F4 press | Toggle player 2 B/A difficulty |

Both switches start at B and persist across Reset/Select. Difficulty keys toggle
once per press; fire, Reset and Select remain sampled levels. Keyboard directions
join only the active player's joystick nibble. Activity on either joystick still
participates in the original inactivity detection.

The adapter runs at F6A7, after the original frame increment, before console and
joystick consumption. SNSMAT reads the actual keyboard matrix; RDPSG/WRTPSG read
both raw joystick ports once, retaining all 16 direction combinations. GTSTCK's
normalization would discard opposing directions. PSG register15 is restored,
including selection, strobes and other peripheral outputs. BIOS remains mapped
in page0. VDP IRQ generation is masked because BIOS input calls can execute EI;
the adapter returns with CPU interrupts disabled before SP-based name clearing.
Register snapshots, IFF1/2, VDP IRQ masking and PSG15 restoration are checked.

The issue #9 delivery diagnostic substituted neutral hardware collision inputs B0..B6=FF/F8=0
before **every** update, including after Reset/Select. These are the future
collision backend's inputs, not persistent game state. The current cold-boot
diagnostic replaces this phase with original raster acquisition. Isolated input
RPC and `make render-input-bench` retain neutral contacts for adapter regression.

## Reproduce

```
make controls-run             # cold boot, continuous controls diagnostic
make input-natural            # input contract plus uninterrupted boot replay
make render-input-bench       # full native/background/sprite/input density
make native-contract
make render-graphics-bench
bash scripts/ci.sh
```

The local original inputs must pass the manifest. ROMs, source-derived data,
listings, replay snapshots and raw dumps remain ignored under outputs/. Public
metadata is under references/input/. Public CI needs no originals and assembles
the synthetic renderer plus the hardware adapter; it cannot establish original
gameplay or emulator/hardware acceptance.

Input fixtures use real openMSX KeyMatrixState/MSXJoyState device events. Their
four target hardware mirrors are poisoned, so expected values cannot pre-seed a
missing sampler write. Reference results come from the independent original
6502 CPU. Full-RAM fixtures test all direction combinations, fire thresholds,
corners, port separation, keyboard union and both independent switch bits.
Five subsequent 300-update chains preserve native game RAM: four held-fire
chains for both players/settings and one Select/Reset/switch-edge chain.

In the held-fire scenario at X76/Y50 facing right, B produces shots every16
ticks and A every26 ticks, identically for both players. This is a consequence
of the original active-shot lifetime and displacement5/3, not a new cooldown.
Different positions/facing can change the lifetime.

The natural replay cold-boots, traverses refill, held fire, reversal,
Select/Reset and fresh refill, then applies 16 keyboard/joystick pulses at
different frame phases. No game RAM is reloaded. Every captured native update
matches the original CPU. Latency reports distinguish event-to-state completion
and event-to-completed SAT upload, reading actual VRAM after commit. Visible
scanout, host OS input latency and physical MSX have not been measured.

## Cost and remaining limits

| Final probe | Cases / maximum |
|---|---|
| Independent native CPU contract | 2,707 cases; 10,997 cycles |
| Actual-device input contract | 5,660 cases; sampler 1,879 cycles |
| Continuous cold-boot replay | 659 updates; no game-RAM reloads |
| Native graphics regression | 6,526 cases; 52,886 cycles |
| Full-density native graphics/input | 9,598 cases; 59,369 /59,736 cycles |
| Worst input pacing | 240 frames; no skipped VDP frames |
| VRAM data spacing / VBlank commit | 29 cycles minimum /11,529 cycles maximum |
| CPU margin /32 KiB ROM padding | 367 cycles /1,792 bytes |
| Input event→state /completed SAT upload | 18.6709 ms /32.2447 ms maximum |

The controls ROM SHA-256 is
`701e3293951b902ef08d81a75bc63c1f5fc5637ffaec02cf5e5992d40198845a`;
the timed full-density probe is
`f5a3c463bcb8077d38a19611e77710f4e54cfae4dcb9a574d38e5682f0e3d474`.
Both are32 KiB diagnostics for C-BIOS_MSX1/openMSX21.0, NTSC,64 KiB RAM and
16 KiB VRAM. These are different diagnostic entry paths. The pacing stack
minimum is F370 and the RAM guard remains intact. All31 host tests, the local
public-CI script and both synthetic builds pass. The intentional port2 corruption
fails on the first case at C00D; the subsequent normal run passes.

Measured values, exact ROM hashes/settings and review evidence are in
references/input/. The input stress pass adds normal-running cases with oxygen64,
refill disabled, Y13/17/18/20/108, shot inactive/edge-active, both facings,
all16 direction combinations, held/released fire and all switch combinations.
It also retains the original dense edge/surface fixtures. State, pixels, palette,
scanline occupancy, preceding visible VRAM, port spacing and pacing are checked.

To recover CPU/ROM room, the static translator emits direct accesses and omits
only dead carry/NZ bookkeeping. Calls, returns and unknown exits are conservative
flag barriers; fast carry branches require a unique immediate predecessor.
Instruction/event order and original algorithms remain unchanged. Renderer work
uses the same pixels, objects, two scratch banks and transfer volumes; name-row
addresses and X columns are reused, fixed copies are unrolled, and scratch VRAM
address arithmetic avoids a redundant multiplication. A short commit drain lets
the final queued TMS byte reach VRAM before a completion snapshot.

This remains fixture coverage rather than a proof over every reachable state.
The remaining CPU margin is small. Real collisions, HUD/audio additions, PAL
scheduling and physical hardware require new evidence; no playable acceptance
is implied by the controls diagnostic.

Negative control (must fail, then rerun the normal checks):

```
SEAQUEST_INPUT_CORRUPT_PORT2=1 make input-contract
```

It inverts port2's sampled fire bit. The poisoned-input contract must identify
the C00D mismatch immediately. A later normal build restores the valid ROM.
