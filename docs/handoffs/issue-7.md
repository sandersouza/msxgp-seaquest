# Issue #7 handoff — MSX1 renderer feasibility

The owner now requires **one new chat per new issue, inside the same Seaquest
Codex project**. Continue this issue in its dedicated chat; create the next issue's
chat when dependencies are satisfied. This planning chat stops implementation.
See `AGENTS.md` and `docs/project-workflow.md`.

## Objective and state

- User authorized autonomous work to a first playable Seaquest ROM on openMSX,
  keeping original mechanics faithful and GitHub updated. No approval is needed
  for routine reversible work or the next issue chat.
- Repo: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/7
- Codex project: Seaquest, id `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- GitHub project #7 MSX Game Ports: `PVT_kwHOAJR8nM4Bn8x0`.
- Branch: `codex/feat/7-msx1-renderer`, based on main `1ff1616` (PR #22 merged).
- #1–#6 Done; #7 In progress. #8 depends on #7. #9 depends on #3/#6/#7.
- #7 project item: `PVTI_lAHOAJR8nM4Bn8x0zhEz0gU`.
- Shared Status field: `PVTSSF_lAHOAJR8nM4Bn8x0zhmfCzE`;
  In progress `47fc9ee4`, In review `df73e18b`, Done `98236657`.
- Unfinished local files: `scripts/render_tables.py`, `src/render.asm`,
  `tests/test_render_tables.py`. These were begun just before the user's new-chat
  instruction. They must be preserved and tested, not considered delivered.
- Local issue #6 copy was synchronized to its completed native contract and
  is pending inclusion with the next commit. No original ROM/source is tracked.

## Delivered logical core (#6)

`scripts/core_codegen.py` translates the original gameplay CFG into native Z80
at build time; no interpreter ships. 885 blocks cover gameplay, reset, PRNG,
BCD score, lives, enemies, rescue/oxygen and alternating-player logic.
`outputs/native/core.inc` and `original.rom` are generated/ignored local assets.
Core state shadows original address N at MSX `$C000+N`. A/X/Y→A/B/C, carry→E,
Z/N native flags; original phase `$F5B8`→`$F00E`, with timer shadow zero.

`make native-contract` passed **2,707** independent py65/native openMSX cases,
including reset plus **480 chained updates without reloading native game RAM**,
rollover, sampled controls, Select/Reset and death/player switching. Injected X
corruption at chain tick 13 was detected. Max measured core cost: **16,838 cycles**,
max original instructions 566. Fresh review's continuity gap was fixed and verified.
PR #22 merged as `1ff1616a5490118543109d573b3fe75534afbf59`; CI passed.
Physical raster/refresh/full-game acceptance remain later gates.

Native harness notes: C-BIOS has not mapped the cartridge at emulated second 2;
wait 5 and require boot signature/header. Breakpoint RPC uses `debug break; after
break compare_case`. Generated assembly instructions need indentation (an earlier
unindented RET became a label and was caught). The harness has a file lock,
per-case watchdog and verifies process status plus completed count. Do not run
multiple harnesses against the same `outputs/native` directory.

## Renderer candidate to benchmark

- SCREEN 2, plain 32 KiB target, standard CPU, TMS9918A 16 KiB VRAM.
- Canonical field is 160 pixels wide. Candidate MSX viewport is **240 px centered
  at X=8**, scale 3/2. Original repeat spacing 16 becomes 24, so all three copies
  in a lane share the same tile phase/cache. This avoids tripling pattern uploads.
- Enemies are software background tiles: six 8×8 patterns per lane (3 columns ×
  2 rows), 24 patterns / 192 bytes total per frame, shared by up to three copies.
- Player uses two 16×16 sprites for its 24×12 stretched bitmap; torpedo one;
  four lane balls/divers one each, separated vertically by 24. Peak is four sprites
  per scanline. **Patrol must use background tiles**, since making it a hardware
  sprite can raise peak to five where it overlaps the first lane's bounding box.
- Dirty name-table spans per row avoid a 768-byte upload every frame. Previous
  enemy cells are tracked/cleared in RAM; upload only the union of old/new spans.
- Active-display writes use `OUTI; JR NZ` spacing rather than unsafe tight OTIR.
  Validate actual VRAM bytes and frame costs on the chosen MSX1 machine.
- A universal 12,288-byte phase/parity LUT expands each original 8-bit row to
  12 pixels, shifted across three bytes. `render_tables.py` generates it without
  original ROM inputs; also generates a 256-byte bit reverse table.
- `tests/test_render_tables.py` passed: full-row width/phase/parity and sprite
  budget tests. Full synthetic suite currently **19 tests passes**. The Z80
  renderer has **not been assembled, run or benchmarked** yet.

## Known unfinished points in src/render.asm

- The phase/parity calculation currently rotates parity right four times, yielding
  bit 4; it needs parity in **bit 3** for the 16 LUT states (e.g. five right rotates
  or three left rotates). Fix before assembly/VRAM comparison.
- `benchmark_shape`, aligned `expand_lut` and aligned `reverse_bits` labels need
  a benchmark wrapper. There is no benchmark ROM/tool yet.
- `render_enemies` currently draws all three copies unconditionally for synthetic
  max-density stress. Production must honor original repeat/visible masks and
  canonical wrap: `$A4 & LFEEB[index]` from original display preparation, and
  copy coordinates `(base+0/16/32)&255`, clipped to canonical 0..159.
- Validate tile-bank handling: lane3 top y48 is bank0, lanes2/1 bank1, lane0 top
  y120 crosses bank1/bank2; upload split was written but is untested.
- Check dirty tracking, stack balance and all index/pattern addresses in actual
  emulator output. Do not trust source inspection in place of the benchmark.
- Colors, patrol background, hardware sprite patterns/SAT and production shape
  selection are not integrated. Current generic cache reads `benchmark_shape`.

## Original geometry research (not yet #8 asset delivery)

An ignored `outputs/gfx_probe.py` uses the original ROM in ALE and freezes canonical
state. `setRAM` takes RAM index 0..127, not CPU address. Do not set `$A3=255` for
these probes: ALE then considers the game terminal and later act calls stop.
Freeze fractional accumulators `$CF..$D1=0` and lane timers `$F1..$F4=255` to
avoid one-pixel motion while measuring. Screenshot: `outputs/reference/gfx-probe.png`.

Observed raw Atari geometry, after removing motion:

- Player canonical X maps directly to left X. Bitmap is **16×12** (each original
  8-bit row doubles horizontally through TIA NUSIZ). Its rectangle starts at
  raw Y=`player_Y+32`; nonzero row 1 starts at player_Y+33.
- Enemy lane i rectangle starts raw Y=`63+24*(3-i)`, width8, height15. Shark
  nonzero top rows start at Y65 for lane3 with the measured phase.
- Ball/diver lane i starts raw Y=`64+24*(3-i)`, width8, height15. Human masks
  come from HMBL movement and ENABL/CTRLPF tables, not a simple bitmap.
- Candidate MSX translation is raw Y−15: player top `Y+17`, enemies
  `48+24*(3-i)` (tile aligned), balls `49+24*(3-i)`. HUD can be placed separately
  to retain all original text within 192 rows; do not change collision coordinates.
- Ball mask decoding: for rows14→0, read movement at FD00+ROM[FF7E+index]+row,
  accumulate `x -= signed_high_nibble(movement)`; read control at
  FD00+ROM[FF92+index]+row; enabled if bit1, width `1 << ((control>>4)&3)`.
  Normal human masks span relative X−2..5, so add2 to normalize to canonical C7.
  Validate decoded mask pixels against the frozen ALE crop before claiming fidelity.
- Player rows are FD00+ROM[FCFB+E0], reversed 11→0; expand each bit twice for
  canonical collisions or three times for the MSX 24-pixel display bitmap.
- Enemy rows are FD00+ROM[FFA2+(D9&7)] plus DD for sharks (index<4), reversed
  14→0. Reflect when D9 bit3 is set. Do not substitute unrelated graphics.

## Next actions

1. Read issue #7 and the first-playable plan. Build a stress wrapper around the
   candidate renderer; compare VRAM pixels/names against a host oracle and measure
   cycles with maximum enemies, sprites, crossings, HUD/patrol and native core.
2. Fix/optimize until the measured budget and sprite visibility contract are
   satisfied. Record ROM/machine/settings and evidence; obtain fresh review and CI.
3. Complete #7 and hand off **#8 in a new chat in the same Seaquest project**.
   Then follow the remaining dependencies toward the playable loop. Keep unverified
   graphics/collision/clock/gameplay/hardware claims explicit.
