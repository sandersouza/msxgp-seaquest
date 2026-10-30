# Reference traces — initial #6 delivery

The initial delivery proves a bounded solo capture
and repeatability check; it does not complete native acquisition alignment, the
full rule fixture catalogue, exact source clock measurement or raster collision
verification.

The subsequent [native CPU contract](native-core.md) supplies the required named
logical phase, reset/seed/control replay and 480 chained updates without reloading
native game state. Broader natural-game/raster capture and physical clock/refresh
validation belong to #10/#14/#15; the initial ALE limitations below remain explicit.

## Install and reproduce

```sh
.venv/bin/python -m pip install -r requirements-reference.txt
make reference-trace-check
.venv/bin/python -B scripts/reference_trace.py capture --output outputs/traces/run.json
.venv/bin/python -B scripts/reference_trace.py compare outputs/traces/baseline-b.json outputs/traces/run.json
```

The optional backend is [ALE Python 0.12.1](https://ale.farama.org/python-interface/),
which uses a Stella-based emulator. It loads the **local manifest-verified original
4K ROM**, not a substitute game binary. Captures and raw 128-byte RAM snapshots
remain in ignored `outputs/traces/`; public CI imports only the comparator/parser
and runs synthetic tests without ALE, NumPy or the original ROM.

Capture settings are explicit: ALE random seed 0, frame skip 1, sticky-action
probability 0, no sound/display, solo mode 0, selected left difficulty B/A and
right difficulty B. The current Seaquest backend exposes only solo mode; alternate
player capture and independently selecting the right switch need another adapter
or extension. RESET is not an exposed joystick action in this interface.

The [pinned ALE reset implementation](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/v0.12.1/src/ale/environment/stella_environment.cpp)
advances 60 NOOP frames, soft-resets, applies mode and soft-resets again. Therefore
the first captured RAM is **not cold power-on or ROM frame zero**. With the tested
setup it is frame byte 67, game seed 204, X=76, Y=13 and oxygen=0. The ALE random
seed and the game's PRNG byte are different quantities. Metadata records the
initial RAM fingerprint, reset policy, versions, input scenario and ROM hash.

## Boundary and initial evidence

Each action is applied through `ALEInterface.act`, then RAM is sampled after the
emulator completes one frame. The first snapshot precedes all scenario actions.
This boundary is not an instruction/PC hook. A future native adapter must acquire
equivalent phase/state; equality of supplied snapshots alone cannot prove it.

`references/scenarios/input-baseline.json` waits through refill, moves right then
left, dives to Y=18, holds fire for eight frames, then surfaces. In the tested
macOS ARM environment (ale-py 0.12.1, logged core 8a8fafb, NumPy 2.5.4):

- Two independently initialized B/B runs produced identical **209 snapshots**,
  including all 128 RAM bytes and action/frame metadata.
- The ROM's frame byte advanced by exactly one modulo 256 at every capture,
  including rollover. This is phase-step evidence, not a measured frame duration.
- Refill reached 64; twenty right/left updates moved X from 76→96→76;
  five down/up updates moved Y 13→18→13.
- After turning left, the shot X after eight held-fire updates was 44 in B and
  60 in A, consistent with original -5/-3 displacement from initial X+8=84.
- An intentionally altered X byte at snapshot 170 was detected as the first
  difference: RAM `$C6`, expected 96, actual 97.

The check writes a fresh `outputs/traces/probe-summary.json`; the committed
`references/trace-probe-summary.json` is the evidence snapshot. All three local
original inputs still match their initial immutable hashes.

## Comparison contract and remaining work

The comparator first requires identical identity metadata (ROM, backend/settings,
scenario/reset policy), then frame/action/index alignment and all 128 raw RAM
bytes, returning the first mismatch. It is currently a **reference-replay**
comparator. A native MSX snapshot needs an explicit canonical-field mapping;
pointer bytes, stack and temporary aliases cannot be compared directly across CPUs.

To finish #6: establish exact source clock/scanline evidence; choose phase hooks
for native comparison; support original reset/select and alternate-player/switch
cases; capture the full relevant fixture catalogue including boundary collisions,
oxygen/rescue/score/death and RNG/lane behavior; validate initial/reset policies
beyond this solo sequence. Preserve the initial fixture as a useful regression,
without treating it as full gameplay fidelity or physical-machine acceptance.
