# Original gameplay to native Z80

The original gameplay control-flow graph is translated **at build time**, not
interpreted on the MSX. 885 reachable 6502 instruction blocks become direct Z80
instructions/branches/calls. No runtime 6502 interpreter ships in the cartridge.

`scripts/core_codegen.py` reads the manifest-verified local original and writes
ignored `outputs/native/core.inc` plus a local original-data lookup image. Generated
original-derived sources/data remain local. The public repository contains the
generator, the public 6502 ISA facts, test harness and new MSX platform code.
Unsupported instructions/addressing modes fail closed rather than silently changing
behavior. This is a domain-specific gameplay translator, not a general 6502 emulator.

6502 A/X/Y map to Z80 A/B/C. Carry is preserved independently in E; Z/N remain
in the Z80 status register. Loads, stores, compares and carry branches preserve
the original flag effects. The source score routine has a specialized native
block with the same low/middle/high decimal additions, ordered observable stores,
reserve checks and A/X/Y/C/N/Z returns. Its no-carry return gets NMOS N/Z from
adjusted A (e.g.79+01→80/N=1); other paths redefine N/Z before use. Identity high
stores and terminal dead stores at999999 are omitted under DI, without batching
calls or changing any A3 increment. Overflow flag consumers and
unsupported stack/indirect operations are rejected by CFG validation.

Canonical memory lives at MSX `$C000 + original_address`: zero-page state is
`$C080..$C0FA`. Hardware input/audio shadows occupy their original logical
addresses in the same block. Core input/output is at original PC `$F5B8` (after
raster collision collection) to `$F00E` (before next display preparation). This
preserves old/new frame phases and original event order. RIOT waits are bypassed
by a zero timer shadow; the MSX scheduler supplies physical frame pacing.

## Reproduce the independent comparison

```sh
.venv/bin/python -m pip install -r requirements-reference.txt
make native-contract
```

The oracle executes original binary instructions on **py65 1.2.0**. The target
executes generated native Z80 in **openMSX 21.0 / C-BIOS_MSX1**, with 64 KiB RAM,
16 KiB VRAM and no expansions. Both receive identical canonical RAM, sampled
controls and collision-latch results at the named original phase. The harness
compares all shadow memory bytes `$00..$FA`, excluding stack/return bytes.

On 2026-10-30, **2,707 cases passed**: all 256 PRNG seeds, 256 BCD cases, captured
baseline states plus five control variants, reset/frame rollover, alternate-player
and independent switch/reset/select cases, full/partial/zero-diver surfacing,
oxygen/refill/bonus phase combinations and each lane's hit categories/types.
The last 481 cases form a reset plus **480 continuously chained updates** through
frame rollover, held controls, Select/Reset and death/player switching. Only named
hardware input/latch bytes are supplied after the first reset; native game RAM is
not reloaded between ticks. Changing native X at chained tick 13 was detected at
the first divergent byte `$C6` (expected 76, actual 77).
The maximum original instruction count was 566. Maximum native cost was 16,838
Z80 cycles, derived from emulated elapsed time × 3,579,545 Hz, including the RPC
wrapper. This bounds these cases; it is not a full-game performance acceptance.

Two harness defects were caught before acceptance: C-BIOS had not mapped the
cartridge at the earlier two-second probe, and an unindented generated RET was
interpreted as an assembler label. The final harness requires the cartridge boot
signature/header, waits for a safe boot window, times out per case, checks its
process result and completed case count, and serializes runs with a file lock.

## Acceptance boundary

This establishes the **logical CPU phase/state contract** needed by #9–#11.
ALE's initial post-frame baseline is still recorded separately (ROM frame 67,
seed 204 after warm resets); it is not relabeled cold boot. Input sampling is
explicit at the gameplay entry and tested through original SWCHA/SWCHB/trigger
instructions. Hardware collision latches are injected, so these tests do not
certify the new renderer's geometry: #7/#8/#10 must verify that separately.
Physical source clock/scanline measurement, broader natural-game traces and
cross-refresh pacing remain #14/#15 acceptance work. A passing CPU differential
does not certify video, sound, full gameplay or real hardware.
