# Issue #9 handoff — original input, movement and firing

Start #9 only in a dedicated `ISSUE #9` chat in this Seaquest project. Reuse it
if present. The #8 chat stops all shared-checkout changes after dispatch.

- Repo: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/9.
- #8 branch: `codex/feat/8-original-graphics`; verify its merged main commit and
  PR/CI integration before creating the scoped #9 branch.
- #8 delivery: https://github.com/sandersouza/msxgp-seaquest/pull/24.
- The owner authorizes routine implementation, review, scoped PRs, integration
  and autonomous succession toward first playable openMSX. Keep one issue per chat.
- Dependencies #3/#6/#7 are integrated; #8 adds original sprite display assets.

Read AGENTS.md, docs/project-workflow.md, the local `.github/issues/09*` copy,
docs/superpowers/plans/2026-10-30-first-playable.md, docs/gameplay-contract.md,
docs/original-graphics.md and relevant personal Obsidian guidelines first.

## Verified interface and corrections from #8

- Native gameplay phase remains F5B8→F00E, canonical RAM at C000+original address.
  No interpreter ships. Source collision masks stay canonical; display scaling
  and clipping must never write movement/collision state.
- Local `make graphics-reference-check` extracts 281 assets/views and validates
  497 shape/lettering/death cases plus260 edge cases against ALE/Stella. Includes
  all ten original digits, life/diver icons and both exact original logos.
- Source ball raster anchor is C7+2 before signed HMOVE motion: normal diver
  bounds0..7 relative to C7. Earlier handoff's -2..5 omitted positioning bias.
- Torpedo original width8, MSX width12; raw Y=E1+40, MSX=E1+24. It is seven
  lines below the player's top, not the synthetic prototype's five-line offset.
- Player raw top E1+33; MSX E1+17. Original raw lines53..56 suppress player
  pixels; display-only surface variants blank MSX lines37..40 at E1=13..23.
  Death counters1..9 use the same bitmap as10; counters10..14 select the table.
- Original legal player X21..134 / Y13..108. Player horizontal edge combinations
  outside that contract are not stored. Enemy animation indices3/7 are unused;
  do not interpret the diagnostic's artificial 15-row cases as natural gameplay.
- Enemy and ball display tops now coincide at48+24*(3-lane), as in source raster.
  Patrol has seven visible rows31..37 in a bottom-aligned16px boxY22..37;
  first lane boxY48..63 does not intersect it. Scanline occupancy remains<=4.
- X mapping remains8+floor(3*x/2), viewport8..247. TIA's X0..7 HMOVE video bar is
  deliberately omitted on MSX. Source edge oracle accounts for it separately;
  validate collision latch/blanking semantics in #10 rather than clipping masks.
- `scripts/graphics_palette.py` maps fixed TMS colors; sprite player/death/diver
  selection honors source state/attract masks. HUD names and background color
  transitions in the diagnostic are still synthetic, for #13 integration.

## Renderer, space and delivery evidence

- `src/original_sprites.asm` plus ignored `outputs/graphics/sprites.inc` select
  source-derived animations/surface and edge variants. Generate before assembling
  WITH_GRAPHICS. `make render-graphics-bench` includes native gameplay.
- Sprite catalog:213 patterns /6,816 ROM bytes.47 resident plus two eight-slot
  scratch banks consume2,016 of2,048 sprite-pattern VRAM bytes. Upload variants
  only to the bank not referenced by the current SAT, then switch at VBlank.
- `src/render.asm` now reuses one48-byte lane atCC00..CC2F and uploads it to
  inactive VRAM immediately. Direct stores recover2,881 measured cycles in the
  synthetic/native baseline. Old docs'192-byte RAM staging is historical;
  steady background VRAM traffic is still192 bytes per frame.
- Public exact evidence belongs in `references/graphics/`. Read its final
  graphics-result.json for the accepted ROM hash, cases, CPU margin and settings.
  The measured CPU and 32KiB ROM margins are tight: remeasure every added routine,
  asset, input/audio operation or VRAM transfer. Do not assume room for full game.
- Original inputs, code-generated art/listings/data and native ROMs remain local
  ignored research outputs. Public CI builds only synthetic diagnostics.
- Natural input/audio, full collision acquisition, full gameplay, PAL scheduling
  and physical MSX are unverified; a benchmark ROM is not a playable acceptance.

## Next actions

1. Verify #8 merged, CI passed, checkout clean, and advance only Seaquest #9.
2. Implement original input/movement/firing integration using #6 state semantics;
   preserve exact sampling phase, byte arithmetic and player switching contracts.
3. Measure real input cost and ROM growth against #8 limits before broadening.
   Keep renderer interrupts-disabled/SP-clearing contract and original slot setup.
4. Validate with source/native cases, natural-control openMSX scenarios, independent
   review and CI. Close only on #9's own DoD. Start #10 in its own project chat.
