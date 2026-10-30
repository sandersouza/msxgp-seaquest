# Issue #11 verification

Local original: verified NTSC/4K Atari2600 revision, SHA-256
`fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
Machine: openMSX21.0/C-BIOS_MSX1, standard3,579,545Hz Z80, NTSC,
64KiB RAM/16KiB VRAM, no expansions. Python3.14.7, py65 1.2.0,
ALE0.12.1/Stella; sjasmplus revision
`d379eeac9ad3857fb48fd3a3929175d0a56038ce`.

| Probe | Result |
|---|---|
| Original F44F→F473 vs Atari raster |768 passing alarm cases |
| Native omitted-HUD alarm |12,288 cases; all256 oxygen bytes and phases |
| Ordered transition fixtures |6,125;0/1/5/6 divers, source ascent/drain boundaries, pickup cap, simultaneous contacts, patrol/death/refill |
| Seeded native chains |6,192 ticks; no game-RAM reloads within each chain |
| Combined alarm/transition/chain contract |24,605 cases; stackF370; IFF disabled, VDP IRQ masked, PSG15 restored, guard intact |
| Full native/input/collision/pixel workload |17,647 cases; max59,311/59,736 cycles |
| CPU margin /32KiB cartridge padding |425 cycles /1,536 bytes |
| Worst-case pacing |240 frames, no skipped VDP frames; max59,204 busy cycles |
| VRAM spacing /visible commit |minimum29 /maximum11,039 cycles |
| Continuous cold-boot actual controls |6,262 updates; no game-RAM reloads; each checked against original TIA occupancy and original CPU |
| Natural measured workload |maximum59,107 cycles; no skipped VDP frames |
| Natural events |12 pickups;1 partial rescue;512 alarm ticks;1 oxygen depletion;6 deaths;7 refills |
| Event→state /completed SAT upload |maximum17.5991 /29.7739ms |
| Native /input /collision regressions |2,707 /5,660 /40,748 cases |
| Graphics oracle /renderer regression |647 scenarios +299 edges /6,526 cases |
| Isolated input/renderer regression |9,598 cases; max58,757 cycles |
| Synthetic host checks /local public CI |36 tests pass /all builds pass, including oxygen adapter |

Timed full workload SHA-256:
`6d60a28ce10d8a01679f8c62719421c14122c96ffd93b8b79950aa2bd1b9bfa6`.
Cold-boot controls cartridge SHA-256:
`e50cec4855f0767e2fde0cc2ba5741b0cc8793ee9dd1fe988bfcfc01bff98dd6`.
Both are32KiB diagnostic cartridges, not a full-game/hardware release.

## Reproduce

See [commands and phase contract](../../docs/oxygen-rescue.md). `make oxygen-natural`
builds and runs the real-input contract first to create the current cold-boot
device replay seed. Its first segment retains Reset/Select, both difficulty
switches, keyboard and joystick pulses. After17 emulated seconds, device-only
feedback collects a partial rescue, holds the safe original Y20 depth until
oxygen depletion, then attempts further collections. It never writes game RAM.
Required natural events are checked so an inert controller cannot pass.

The natural session did **not** complete a full six-diver rescue. Full rescue,
bonus, scoring-phase transitions, byte wrap and refill are covered by separately
identified seeded chains with continuous BIOS controls. Chained initial states
are not described as naturally reached. Each tick acquires actual raster masks
and the omitted source HUD state before the unchanged native source update.
Low-reserve/early-death patrol carry remains covered by the collision regression.

The independent alarm oracle executes F44F→F473 from the original ROM; it does
not copy native F9 into the expected result. A separate768-case ALE check freezes
the subsequent bonus path using an even OLD phase and inactive pickup sound,
so HUD-produced F9 remains observable after the raster. The intentional runtime
alarm corruption fails on the first fixture at byteF9, followed by a normal pass.

The long natural replay exposed two over-budget right-edge frames. The name
renderer now writes the same clipped one/two columns directly. The full pixel
comparison, preceding visible VRAM comparison, unchanged192-byte enemy-pattern /
352-byte commit volumes and two inactive banks verify the optimization. There
is no dropped object or reduced update frequency. These bounds cover the named
workloads, not every reachable state.

Public CI assembles the new adapter with synthetic data and contains no originals.
Hashes/settings/results are public metadata; art, original-derived assembly,
tables, ROMs and replay/state/VRAM dumps stay ignored locally. Latency excludes
host OS, physical inputs and visible scanout. HUD/background composition remains
synthetic; PSG audio, full-game, PAL and physical MSX acceptance remain later work.
