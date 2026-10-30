# Issue #10 handoff — lanes, spawning and original collision acquisition

Continue only in the dedicated `ISSUE #10` chat within the Seaquest project;
reuse it if it exists. The #9 chat stops shared-checkout changes after dispatch.

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/10.
- Project item: `PVTI_lAHOAJR8nM4Bn8x0zhEz0xY` in
  `PVT_kwHOAJR8nM4Bn8x0` (project7).
- #9 branch: `codex/feat/9-original-input`; verify its merged PR/main commit,
  CI and clean checkout before starting a scoped #10 branch.
- Owner authorizes routine implementation, review, scoped PRs, integration and
  autonomous issue succession toward first playable openMSX. No repeated routine
  permission requests. No implementation delegation was authorized.

Read AGENTS.md, docs/project-workflow.md, `.github/issues/10*`,
docs/gameplay-contract.md, docs/native-core.md, docs/original-graphics.md,
docs/input-controls.md and the first-playable plan first. Consult personal
Obsidian `codex-instructions` through its CLI: all0- notes and relevant guidance.
Honor the owner's restriction to Obsidian skills unless explicitly requested.

## What #9 supplies

- Native movement/firing remains the original translated F5B8→F00E algorithm.
  Input sampling is hooked at F6A7, after frame increment. Keyboard joins the
  active player's port; physical joystick ports remain separate. Both difficulty
  switches persist outside original reset RAM. F1/F2 map Reset/Select held;
  F3/F4 toggle each player's B/A setting. Cursor/Space provide directions/fire.
- BIOS SNSMAT/RDPSG/WRTPSG read actual device levels; raw directions retain
  opposing combinations. Main BIOS stays visible in page0. VDP IRQ generation
  is masked because BIOS can EI; input returns DI before SP-based rendering.
  Register preservation, IFF1/2 and PSG15 restoration are tested.
- `make controls-run` cold-boots a **controls-only diagnostic**. Its
  `neutral_contacts` writes B0..B6=FF/F8=0 before every update, including after
  Reset/Select. It is not real collision acquisition. Replace that hardware
  phase with original-equivalent raster/mask acquisition in #10.
- Source algorithms for lane motion, PRNG, spawning and collision resolution
  already exist in the native core from #6. Do not replace them with a new
  high-level model. Preserve collision priority, per-lane latch clear/windows,
  repeated/clipped source shapes, sprite/ball offsets and source HMOVE semantics.
- Pixel/collision coordinates remain canonical. The display's 1.5x X mapping,
  surface variants and TMS palette must not write collision/movement state.
  The geometry corrections from docs/handoffs/issue-9.md remain binding.

## CPU/ROM and verification

- CPU margin remains **very small**. Read final references/input/input-result.json
  rather than the historical #7/#8 budgets. The accepted input stress covers
  neutral collisions, normal/refill states, shot birth/edges, all16 directions,
  fire levels and switch combinations. Real acquisition/resolution density must
  be remeasured before acceptance; do not just add collision code to this budget.
- Renderer objects/pixels and inactive-bank contracts remain unchanged. New
  generated column/repeat-mask tables and per-lane name pointers reduce repeated
  work; fixed three-copy name drawing is unrolled. Repeat masks prove every
  admitted canonical X<160, including byte wraps. Sprite address arithmetic is
  independently checked for all64 physical slots. Last SAT byte drains before
  commit completion. Preserve >=29-cycle VRAM data spacing and VBlank commits.
- The translator now omits dead carry/NZ bookkeeping conservatively and uses
  direct Z80 accesses. JSR/RTS/unknown exits are barriers. Fast carry branches
  require a unique immediate predecessor; NMOS BCD ADC is kept distinct. Native,
  input and graphics regressions plus independent review cover this change.
- `make input-natural` runs5,660 real-device/independent-CPU cases, including
  five300-update chains, then a659-update cold-boot replay without game-RAM
  reloads. Four hardware mirrors are poisoned in full fixtures. At X76/Y50,
  right-facing held fire repeats every16 ticks in B /26 in A for either player.
- Latency evidence distinguishes event-to-native-state from completed SAT
  upload. It does not measure host OS event latency, actual scanout or physical
  hardware. Full gameplay/audio/HUD, PAL and physical MSX are still unverified.
- Public metadata/review are under references/input/. Exact hashes/settings and
  final costs are there. Raw ROMs, replay snapshots, listings, source-derived
  data/art and dumps are local ignored research outputs; never publish them in
  CI artifacts. Public CI assembles synthetic renderer/input only.

## Next actions

1. Verify #9 merged/closed/Done, checkout clean and #10 dependency ready. Move
   only Seaquest #10 In progress and create its dedicated branch here.
2. Establish collision acquisition phase and independent original raster oracle;
   cover every source latch/window, ball/enemy/player/missile and patrol case.
3. Integrate acquired latches with existing native resolution, lane/RNG/spawn
   order. Verify seeds, repeated shapes, clipping and simultaneous priorities.
4. Remeasure maximum density, continuous real input, stack/IRQ/VRAM/pacing and
   original/native state. Obtain independent review and passing CI/scoped PR.
5. Close #10 only after its own DoD/integration. Continue #11 in its own chat.
