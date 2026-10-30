# Issue #12 handoff — score, lives, progression and alternating players

Continue only in a dedicated `ISSUE #12` chat inside the Seaquest project. Reuse
that chat if present. The #11 chat stops all shared-checkout changes after dispatch.

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/12.
- Dependency delivery: https://github.com/sandersouza/msxgp-seaquest/pull/27.
- #11 implementation head: `47f74dc3fba64e2258671bebf77ca678a704c690`.
  Later commits contain delivery/review/handoff metadata. Verify final CI, squash
  merge/main, closed/Done #11 and a clean checkout before starting the #12 branch.
- The owner authorizes routine implementation, scoped PRs, independent read-only
  review/integration and autonomous succession toward a first playable MSX1/openMSX
  version. Do not repeat routine permissions. Review authorization does not
  authorize implementation delegation. One implementer owns the shared checkout.

Read AGENTS.md, docs/project-workflow.md, `.github/issues/12*`, the first-playable
plan, docs/gameplay-contract.md, docs/native-core.md, docs/oxygen-rescue.md,
docs/collision-contract.md, docs/input-controls.md and docs/original-graphics.md.
Use only Obsidian skills unless explicitly requested otherwise. Consult `personal`
/`codex-instructions` through Obsidian CLI: all0- notes and relevant GitHub/Python
guidance; try opening Obsidian if the CLI cannot connect.

## Supplied by #11

The existing static F5B8→F00E translation already contains score, lives, progression,
patrol, death and player-switch algorithms. Preserve source arithmetic and event
order; do not substitute independent high-level state machines. Original Atari2600
NTSC/4K gameplay is authoritative on standard MSX1/64KiB RAM/16KiB VRAM.

`acquire_frame_state` computes omitted F44F→F473 HUD F9 before original collision
acquisition and every integrated native update, including after Reset/Select.
F9=15 for Y≠13, oxygen1..16 and no death; otherwise zero. Old frame bit4 changes
source HUD color, not F9. Later original pickup/audio, bonus, death and refill
instructions may clear F9. Isolated input RPC still uses neutral contacts and
does not acquire HUD state; do not mistake it for integrated gameplay evidence.

Oxygen/rescue coverage includes Up14→13 with the next tick's surface check,
Down19→20/Up20→19 at the drain boundary,0/1/5/6 divers, actual pickup limits and
simultaneous contacts, patrol during refill, full bonus, controls blocked until
refill completes, death, wave byte wrap and bonus group wrap. Native core
instructions and translator carry/NZ/call barriers are unchanged.

The longer natural replay exposed over-budget frames near the right edge. The
name renderer now writes the same one/two clipped columns directly at columns30/29.
All original pixels, objects,192 enemy-pattern bytes,352-byte commits, two inactive
scratch banks and update frequency are retained. No canonical state is changed
by display scaling/clipping. The new adapter also assembles in public synthetic CI.

## Final #11 workloads and limits

- 768 original ALE/Stella alarm scenarios;12,288 native alarm cases.
- 6,125 ordered transition cases plus6,192 seeded chained ticks:24,605 total.
  Chains reload only at the start of each scenario and use real BIOS controls.
- 17,647 integrated pixel/state cases; maximum59,311/59,736 cycles, only425 free.
  240 paced frames, no skipped VDP frames,29-cycle minimum data spacing,
  maximum11,039-cycle visible commit, stackF370 and intact RAM guard.
- 32KiB timed ROM;1,536 padding bytes. Timed SHA-256:
  `6d60a28ce10d8a01679f8c62719421c14122c96ffd93b8b79950aa2bd1b9bfa6`.
- 6,262 uninterrupted cold-boot controls updates, no game-RAM reloads, original
  TIA/occupancy and original CPU checked each tick. Maximum59,107 busy cycles,
  no skipped frames, event→state17.5991ms /completed SAT29.7739ms.
  Natural events:12 pickups,1 partial rescue,512 alarm ticks,1 oxygen depletion,
  6 deaths and7 refills. Full rescue was covered by seeded chains; it did not
  complete in this particular natural session. Do not relabel it natural coverage.
- Cold-boot controls SHA-256:
  `e50cec4855f0767e2fde0cc2ba5741b0cc8793ee9dd1fe988bfcfc01bff98dd6`.
- Regressions:40,748 collisions/20,374 original TIA scenarios;2,707 native;
  5,660 real input;647 graphics scenarios +299 edges;6,526 graphics renderer;
  9,598 isolated neutral input/renderer;36 host tests and local public CI.
- Running Z80 F9 corruption fails on the first fixture, then normal checks pass.

Public evidence is in `references/oxygen/`; see verification.md and review.md.
Local raw evidence and named timed/natural ROM snapshots are in outputs/oxygen/.
Other generated outputs are overwritten by the regression/CI commands. Originals,
art, tables, generated assembly, ROMs and replay/VRAM/state dumps stay ignored.

## #12 acceptance focus

1. Verify dependency delivery and project fields; create a scoped #12 branch and
   move only Seaquest #12 In progress. No concurrent implementation in this checkout.
2. Validate original six-digit BCD, saturation,10,000-point crossings and reserve
   cap, enemy/diver value progression and caps, oxygen bonus, group/wave byte wrap,
   patrol unlock/cadence, game over, restart and alternating players. Preserve all
   seven saved fields and independent difficulty settings.
3. Audit any omitted display/raster-derived inputs relevant to #12. A differential
   fed native RAM is not an oracle for omitted source computations. Independently
   execute original binary instructions and retain real contact acquisition.
4. Include late-game values, simultaneous scoring/death/extra-life/bonus events,
   natural controls and continuous chains. Measure complete maximum-density work;
   solve CPU/ROM cost first if needed. Never reduce enemies, visibility, quality
   or simulation frequency to fit. Preserve BIOS/PSG15/IFF/stack/VBlank contracts.
5. Obtain independent review, passing CI and scoped integration before closing #12;
   hand off the dependency-ready successor to another dedicated project chat.

Keep #10 geometry/latch contracts: source CXCLR windows; reflected/doubled P0;
width8 M0; per-row ball HMOVE/width with C7+2 anchor; byte-wrap then TIA160 wrap;
invisible zero-mask P1 atX0; repeated/clipped P1;3→0 shared-latch selection; F8 low
bits7 and bit7 patrol. Death1..9 or no-death reserves0/1 select patrol rows11..4;
death10..23 selects12..5. Both display and collision retain this carry variant.
The HMOVE bar hides display pixels but does not remove collision occupancy.
Sprite VRAM remains2,016/2,048 bytes:47 resident patterns plus two eight-slot banks.
Renderer source-row cache is32 pages; DI/SP gathering restores the real stack.

HUD/background composition remains synthetic. PSG audio/timbre, full-game, PAL,
physical input/scanout latency and physical MSX acceptance remain unverified.
