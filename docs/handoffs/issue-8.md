# Issue #8 handoff — original graphics and display mapping

Start/continue #8 only in the dedicated `ISSUE #8` chat in this same Seaquest
project. This issue #7 chat stops checkout mutations after handoff. Do not run
two implementations in the shared checkout.

- Repo: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Project id: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/8.
- #7 delivery branch: `codex/feat/7-msx1-renderer`; delivery PR will be linked
  in its issue. Verify the merged main commit before branching for #8.
- User authorizes routine implementation, scoped PRs/review/integration and
  continuation toward first playable openMSX without repeated permission.
- #1–#6 are delivered. #7 passed feasibility; successor starts after its PR/CI
  integration is verified. #8 depends on #7. #9 also depends on #3/#6/#7.

Read `AGENTS.md`, `docs/project-workflow.md`, `.github/issues/08*`,
`docs/renderer-feasibility.md` and the first-playable plan before implementation.

## Accepted feasibility interface

- Standard MSX1 64 KiB RAM/16 KiB VRAM, TMS9918A, plain 32 KiB ROM, SCREEN 2.
- Canonical original state remains at C000+original address. Never change
  collision coordinates to fit display. Original 160px field ->240px display,
  X=`8+floor(3*x/2)`, clip original coordinate160 and wrap repeat coordinates256.
- Enemy rectangle tops Y48/72/96/120; source15rows, 12displaypixels wide.
  Repeated copies spaced24px share6tiles/lane. Original mask uses A4&FEEB.
- Backend `src/render.asm`: `LANE_SHAPES` C500 has four last-row pointers;
  rendering reads fifteen bytes backwards, reflects with D9 bit3, builds192
  pattern bytes and uploads inactive cache IDs32–55/96–119. Commit switches
  names only at VBlank. Lane0 bottom tile row uses VRAM bank2.
- Player uses2sprites for24×12, torpedo1, each of4balls/divers1, patrol1.
  **Patrol is hardware, not background:** actual original pixels at raw46–52
  become31–37 with Y−15. Place its8-row rectangle in rows8–15 of a boxY22–37.
  Firstball boxY49–64 cannot overlap. Exhaustive legal playerY model needs<=4
  slots; actual VDP status polling passed without fifth-sprite overflow.
- `scripts/render_reference_probe.py` reproduces patrol bounds for player
  animations0/1/2 with ALE; do not repeat the stale incoming handoff's Y39 guess.
- Initialization maps cartridge page2 with primary/expanded slot bits. IRQs
  must remain disabled while the backend temporarily uses SP to clear names.

## Evidence and limits

- `make render-native-bench`: 4,238 independent reference/native states and
  original-enemy VRAM pixel comparisons; max54,179cycles of59,736 (5,557 spare).
  240 paced worst-case frames: maxbusy54,072, commit11,501cycles in VBlank,
  no skipped frames. `references/renderer/native-result.json` records ROM hash.
- Synthetic256cases max43,072cycles. VRAM minimum spacing29 cycles. Public CI
  assembles synthetic-only probe; original/native ROMs remain ignored outputs.
- `make native-contract` separately passes2,707cases including480 chainedticks,
  maxcore16,838cycles. #7 renderer stress reloads fixtures; it is not gameplay.
- Fresh read-only review found AF input marshalling in the renderer harness;
  fixed F=C6F0/A=C6F1 and reran. No remaining actionable findings.
- Sprite bitmap patterns and HUD payloads are **synthetic**, though SAT positions,
  colors, numbers, terminator/occupancy and full transfer costs are measured.
  Replace with original-derived assets. Handle clipping near canonical159 and
  preload/cache variants within2KiB sprite-pattern VRAM; any extra per-frame
  pattern/color uploads must be included in a fresh budget run. The approximately
  9.3% margin is not full-game timing acceptance. Palette fidelity, natural
  controls, audio, PAL scheduling and physical hardware remain unverified.

## Original asset research pointers (local data only)

- Source ROM SHA fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43.
- Player rows at FD00+ROM[FCFB+E0], backwards11→0. Original TIA doubles each bit
  to16×12; MSX triples each bit to24×12. Display topY=`player_Y+17`.
- Enemy rows at FD00+ROM[FFA2+(D9&7)] plus DD for indices<4, backwards14→0;
  reflection is D9 bit3. Native benchmark already selects these pointers locally.
- Ball/diver masks: rows14→0, movement at FD00+ROM[FF7E+index]+row, accumulate
  x-=signed high nibble. Control at FD00+ROM[FF92+index]+row, enabled bit1,
  width1<<((control>>4)&3). Normal human x−2..5; normalize with+2 toC7.
  Reviewer independently decoded all16 selections: width6–8canonicalpx,
  each fits one16px hardware sprite after×1.5. Verify pixels against ALE crops.
- Ball rectangle topY49+24*(3-lane), playerY+17. Enemy top48+24*(3-lane).
- Freeze ALE fractional accumulatorsCF..D1=0 and lane timersF1..F4=255;
  setRAM uses indices0..127. A3=255 makes ALE terminal; avoid it in probes.
- Preserve original lettering and silhouettes; original inputs and generated
  original-derived blobs/listings remain under ignored outputs, never public CI.

## Next actions

1. Verify #7 merged main, clean checkout, status and artifacts. Create #8 branch
   `codex/feat/8-original-graphics`; mark only its Seaquest project item In progress.
2. Implement reproducible original asset extraction and original-mask/display
   pixel comparisons, with palette/geometry/VRAM layout documented.
3. Integrate assets into the measured backend, preserve all objects and repeat
   native/pixel/scanline/timing evidence; fresh review and CI before closing #8.
4. Start the next ready issue in a new dedicated chat in this same project,
   transferring branch/commit/limits and stopping shared-checkout edits here.
