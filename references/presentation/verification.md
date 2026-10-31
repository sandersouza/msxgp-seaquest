# Issue13 verification — delivery checks in progress

Environment: openMSX21.0/C-BIOS_MSX1, NTSC standard3579545Hz Z80,
64KiB RAM/16KiB VRAM,64KiB ASCII16 cartridge. Python3.14.7,
sjasmplusv1.24.0/d379eeac9ad3857fb48fd3a3929175d0a56038ce.
Reference NTSC4K SHA256:
`fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
Physical machines/PAL/source-cadence acceptance remain open in #14/#15.

The final broad renderer rerun, immutable review and remote CI/integration are
pending. The results below are reproduced checks, not issue closure.

| Check | Evidence |
|---|---|
| Original HUD model versus TIA |321 states/1,284 fields, including every logo counter |
| Focused native HUD/font/palette/ripple |1,000 source-pixel cases;24-byte triple-glyph update verified |
| Ordered source/PSG contract |7,982 ticks/34,692 stores/45 source sites; controls0/4/8/12/15;2,400 continuous chain ticks |
| Cold device-only original CPU/TIA replay |6,420 updates, zero game-RAM reloads, zero missed visible frames; max53,405busy cycles |
| Cold ordered audio |15,807 stores, every captured source update from cold startup |
| Native clear/RNG/core regression |2,963 cases, including all256 initial zero-clear X values |
| Actual input/cadence regression |5,660 cases, both players/ports and16/26-tick held-fire |
| Collision regression |40,748 cases/20,374 original TIA contacts |
| Oxygen regression |24,605 cases/6,192 chained ticks/768 source raster alarm cases |
| Score/progression regression |55,243 cases/8,800 chained ticks/25,072 source score-register/flag checks |
| Omitted display dependency audit |264 source executions; onlyB0..B6/F8/F9 read before overwrite |
| Public synthetic CI locally |46 tests, one optional py65 check skipped in systemPython; all synthetic assemblies pass |
| Host reference environment |46 tests pass, including synthetic6502 ordered-store/frame-boundary trace |

The focused target is
`9782ddd79e58f26cb688d81d7d0132e8723f9f5025af1c0cfa9942227fa44b73`;
the cold controls target is
`3cf7b27000519b3f78cfa84195d8eb131a3dc3a8b2ee7c9b71b218b4e5ddf7b5`.
They differ only by the controls bootstrap/build variant. Local cartridge/raw
artifacts stay in ignored outputs/presentation and outputs/render.

Sound negative control: setting PSG8 to15 after the first hook was rejected at
tick0:FFC3 (`actual...3f0f0000`, expected`...3f000000`). The complete clean contract
was rerun successfully. Hooks preserve AF/BC/DE/HL/IX/IY/SP/IFF, PSG7 peripheral
direction bits and PSG15 after every store. Source instruction-start cycles are
trace metadata; source frame epochs and event order are checked exactly. The
PSG timbre/phase/shared-noise differences are explicit in [the contract](../../docs/hud-audio.md).

Cold replay observed16 deaths,14 death-driven switches,13 attract swaps, two
game overs, one restart and all four difficulty settings. Maximum event-to-state
18.6163ms; completed SAT commit30.8129ms. Those exclude host input/scanout/physical
latency. Initial cache preparation48,071cycles runs with display disabled;
subsequent visible frames are timed. Natural six-diver collection/full bonuses
are not claimed: those events use continuous seeded source chains.

Reproduce with documented local original inputs:

```sh
make presentation-check
make presentation-natural
make native-contract input-contract collision-contract oxygen-contract progression-contract
bash scripts/ci.sh
```

Run targets serially because builders share ignored outputs. Public CI never
acquires or uploads original ROMs/art. See JSON files here for concise records;
RAM/event/VRAM dumps, replay snapshots and extracted assets remain local.
