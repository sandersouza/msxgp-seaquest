# Issue #13 handoff — original HUD, attract/start presentation and PSG

Continue only in a dedicated `ISSUE #13` chat in the Seaquest project. Reuse an
existing dedicated chat if present. The #12 chat stops all shared-checkout changes
after dispatch; only one implementer owns this checkout.

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/13.
- Dependencies: #8 and #12; delivery PR https://github.com/sandersouza/msxgp-seaquest/pull/28.
- #12 implementation head: `53ea3d3e79d41ad477b2a850e9db2afc45ecbc68`.
  Later commits contain review/delivery metadata. Verify final checks, squash
  merge/main, closed/Done #12 and a clean checkout before the #13 branch.
- Project: `PVT_kwHOAJR8nM4Bn8x0`; #13 item `PVTI_lAHOAJR8nM4Bn8x0zhEz1BI`.
  Status field `PVTSSF_lAHOAJR8nM4Bn8x0zhmfCzE`: Ready=`61e4505c`,
  In progress=`47fc9ee4`, In review=`df73e18b`, Done=`98236657`.
  Change only Seaquest items and verify that status mutations persist.
- The owner authorizes routine implementation, scoped PRs, independent read-only
  review/integration and autonomous succession toward first playable MSX1/openMSX.
  Do not repeat routine permissions. Review permission does not authorize
  implementation delegation. Start a scoped `codex/` branch in the clean checkout.

Read AGENTS.md, docs/project-workflow.md, `.github/issues/13*`, the first-playable
plan, docs/gameplay-contract.md, docs/native-core.md, docs/scoring-progression.md,
docs/oxygen-rescue.md, docs/collision-contract.md, docs/input-controls.md and
docs/original-graphics.md. Use only Obsidian skills unless explicitly requested
otherwise. Through Obsidian CLI read personal/codex-instructions all0- notes and
relevant GitHub/Python guidelines; open Obsidian if CLI cannot connect.

## Supplied gameplay and arithmetic

The original Atari2600 NTSC/4K source remains gameplay authority on unexpanded
MSX1/64KiB RAM/16KiB VRAM. F5B8→F00E is statically translated Z80, not a runtime
interpreter or new game-state machine. Collision/oxygen/input/native contracts
from #9–#11 remain binding; see their handoffs for detailed geometry and BIOS rules.

#12 specializes the sole-entry FB9D→FBCA score block to recover late-bonus CPU.
Native ADD/ADC/DAA retain low/middle/high additions, source carry and returned
A/X/Y/C/N/Z. Middle no-carry implies nonzero B9 and an identity high store; terminal
999999 increments A3 once per scoring call. Dead/identity stores can be omitted
under DI without any observer; individual scoring calls are not batched. Source
event order is retained. Incoming external branches into the folded body are
rejected. Generic carry/NZ call/return barriers remain conservative.

NMOS return79+01→80 has N=1; restoring binary7A's N was incorrect. The score's
no-carry return derives source N/Z from adjusted A. Other paths redefine NZ
before consumption. Enemy/oxygen value is `10*min((groups+2)&255,9)`; groups254/255
pay0/10. Diver payouts cap at20 repeated50-point additions. Saturation can wrap
A3; reserve cap6 and simultaneous missile/body points/death/life checks remain
original. All seven B8..BE/BF..C5 bytes and independent difficulty switches persist.

`acquire_frame_state` supplies original raster contacts plus F44F→F473 logical F9
before each integrated tick, including after Reset/Select. F9=15 for old Y≠13,
oxygen1..16 and death0; otherwise0. Old phase bit4 changes HUD color only. Subsequent
pickup/audio/bonus/death/refill may clear it in source order. A264-case original
display/core read-before-write audit, including real contacts, found only
B0..B6/F8/F9 as omitted logical inputs. This is dynamic dependency evidence; do
not use native RAM as an oracle for a newly omitted source display computation.

## Verified #12 workloads and tight budget

- 55,243 progression records:25,266 direct cases,21,177 integrated transitions,
  8,800 ticks across eight seeded chains.25,072 score register/flag checks.
- All valid low-byte BCD pairs/both carries; upper limits;2,048 terminal cases
  covering every amount byte, both carries, reserves0/6 and A3=0/255.
- Actual contacts, double scoring, death/extra-life/overflow/bonus overlaps,
  all256 group/wave values, patrol unlock/cadence, seven distinct saved fields,
  player exhaustion/game over/Reset/Select, full bonuses and byte wrap.
- 39,328 full native/input/collision/oxygen/progression/pixel cases. Maximum
  59,311/59,736 cycles leaves only425.240 paced frames without skips;59,204 busy
  max,11,039 visible commit max,29-cycle port spacing, stackF370, intact guard.
- 32KiB timed ROM,1,536 padding bytes; SHA-256
  `4c6f9d1f152708c9971fcfdf2d890824b096bdec16736953f3257f8022f4c8fe`.
- Expanded density originally exposed64,981-cycle capped payouts; the same case
  is now58,291. Ordinary60,991-cycle payouts now take57,977. No enemies, visibility,
  pixels, transfer volumes or simulation frequency were reduced.
- 6,262 cold-boot device-only updates; no game-RAM reloads, original CPU/occupancy/
  Atari TIA checked each tick;16 deaths,14 death-driven switches,13 attract swaps,
  two game overs and one restart after controller start. All4 difficulty settings.
  Natural maximum54,771 busy cycles; no skips; event→state17.5991ms /completed
  SAT29.7739ms maxima, excluding OS/physical input/visible scanout.
- Controls SHA-256:
  `1cfd70275c6fd22ea4f169f2864c2054836b86394a415abe6f9de918769bc61f`.
- Regressions:2,707 native,5,660 actual input,40,748 collision/20,374 TIA,
  24,605 oxygen/768 source alarm scenarios,647 graphics scenarios+299 edges,
  39 host checks and local public CI. Final remote CI/review must pass before merge.

Exact public evidence/review is in references/progression/. Local named ROMs,
symbols and raw data are in outputs/progression/final-render and final-natural.
Other outputs may reflect later synthetic CI. Originals, generated art/data,
assembly/listings, ROMs and replay/VRAM/state dumps remain local and ignored.
Natural late-game/full-rescue progression is not claimed: late caps/full bonuses
are explicitly seeded continuous chains. #11's separate natural rescue evidence
remains in references/oxygen/ and must not be relabeled.

## #13 acceptance focus

Integrate original HUD/lettering/score/life/diver/oxygen displays, attract/start
flow and TIA→PSG sound event timing. Original fonts/logos/assets and their source
rows already exist in the local graphics extractor/catalog; do not replace them
with invented lettering. Source audio shadows already run in the native core;
PSG playback/onset/duration/priority/timbre still need independent evidence.

First measure the combined CPU/ROM/VRAM cost. The425-cycle margin does not cover
arbitrary new work. Never reduce enemies, visible objects, graphics quality,
transfers or simulation frequency to fit. Preserve source collision/display
geometry,192 enemy pattern bytes,352-byte visible commits, two inactive banks,
2,016/2,048 sprite VRAM (47 resident patterns plus two8-slot banks),32 source-row
cache pages and DI/SP restoration. BIOS input can EI; keep VDP IRQ generation
masked and the sampler returning DI. Preserve BIOS/slot, PSG15, register/stack
and VBlank contracts while adding actual PSG audio output.

HUD/background are currently synthetic. PSG sound/timbre, full-game, PAL and
physical MSX acceptance remain open. Complete #13 DoD, independent review, CI and
integration before closure, then hand off its dependency-ready successor to a
separate dedicated Seaquest chat and stop checkout mutations here after dispatch.
