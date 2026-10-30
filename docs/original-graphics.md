# Original graphics and SCREEN 2 mapping — issue #8

The measurements below record issue #8's delivery baseline. See
[issue #9 controls](input-controls.md) and references/input/ for the later
translator/renderer optimizations and the current complete input workload.
The current [collision integration](collision-contract.md) also preserves the
source carry-dependent patrol variant during death1..9 or with zero/one reserve
and no death, and records newer timings.

The local extractor preserves the verified NTSC Atari 2600 revision's silhouettes,
animations and lettering. The MSX adaptation has a separate display mapping;
canonical RAM, movement and collision masks remain in original coordinates.
No substitute fonts or branding are introduced.

## Reproduce and provenance

```
make graphics-reference-check
make render-graphics-bench
make render-native-bench
make native-contract
bash scripts/ci.sh
```

The input is the manifest-verified local 4 KiB ROM, SHA-256
`fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
`scripts/original_graphics.py` refuses another revision. Each asset records its
source addresses, row mask and bounds in ignored `outputs/graphics/canonical.json`.
The output manifest records deterministic hashes. Public evidence under
`references/graphics/` contains metadata and results only; original-derived art,
tables, listings, ROMs and dumps stay ignored. Public CI uses synthetic inputs.

| Element | Original source / interpretation |
|---|---|
| Player | FD00 + ROM[FCFB+E0], rows11..0, each bit spans two canonical pixels; D6 bit3 reflects |
| Explosions | FD00 + ROM[FDF0+max(E9,10)] for E9=1..14; a different mask applies only below15 |
| Patrol | Player source rows11..5, reflected, single-width; the final GRP1 write never becomes visible |
| Enemy lanes | FD00 + ROM[FFA2+(D9&7)] plus DD for shark indices below4, rows14..0; D9 bit3 reflects |
| Diver/hostile shot | FF7E motion pointer and FF92 control pointer, rows14..0; signed HMOVE nibble, ENABL bit1, width `1 << ((control>>4)&3)` |
| Player torpedo | FE58 enables one line; NUSIZ0=$35 selects width8, rather than width1 |
| Score | FE00 + digit*8, rows7..0; blank at FE50 |
| Life / rescued diver | FF5D rows8..0 / FFF2 rows8..0 |
| Original logos | Six 16-byte columns at FE5B..FEAB; indices15..8 for Activision and7..0 for Seaquest |

There are 105 base assets and 176 surface display variants. The extractor includes
all 16 ball-control selections. Enemy animation indices3/7 are omitted: original
animation uses0..2 and4..6, and those unused pointers can leave a nonzero GRP1
latch beyond the 15-row rectangle. The diagnostic's artificial enemy-type sweep
still checks its explicit 15-row backend contract; it does not make those unused
selections original gameplay states. Every reachable shark DD offset0..7 is
extracted and checked; the renderer reads the same source pointer directly.

## Pixel authority and clipping

`scripts/graphics_reference.py` compares all 281 assets, including every surface
variant, against ALE/Stella output from the original ROM, plus 260 ball/patrol/
torpedo edge cases and 216 early-death aliases (497 shape/lettering scenarios
plus260 edge cases). It freezes raster inputs using the original bonus early-exit
path, avoiding animation/movement changes before capture. ALE's sticky terminal
state is reset after terminal logo selection. The comparison checks surrounding
rows as well as the shape rectangle, so trailing pixels cannot silently pass.
Early death counters1..9 share frame10; the source attract XOR makes their
otherwise water-colored pixels visible for the mask comparison.

The ball's raster anchor is C7+2 before signed per-row movement, because its
positioning table starts at LFC2C, not LFC29. This yields bounds0..7 relative to
C7 for the normal diver, not the incoming handoff's -2..5. Canonical masks are
stored relative to C7 with that source positioning offset included. They must
not be replaced by the MSX sprite rectangle for collision work.

The original video HMOVE bar hides X0..7. The ALE edge oracle explicitly accounts
for this hardware artifact, including right-edge wraps into that bar. The MSX
display uses the full canonical 0..159 viewport without painting a TIA HMOVE bar.
Canonical shape masks retain those pixels; collision-latch windows and hardware
blanking semantics remain the #10 acceptance gate.

Player surface clipping is independently verified at every canonical Y13..23:
raw video lines53..56 suppress GRP0. The corresponding MSX player lines37..40
are blanked in generated **display variants**. The uncut source mask remains
available separately. Original legal horizontal player bounds are21..134; the
runtime selector uses that contract rather than storing unreachable player
edge combinations. Balls, patrol and torpedo support every active X1..159;
zero and X>=160 select hidden SAT entries. Display clipping never writes RAM.

## Coordinates and palette

The horizontal display mapping is `8 + floor(3*x/2)`, clipped to X8..247.
Apply it to absolute canonical pixels, preserving odd/even phase. A doubled
player bit becomes three MSX pixels, giving a24x12 player in two hardware sprites.
Ball and patrol shapes fit one16x16 sprite. The torpedo becomes12x1.

| Object | Measured original raw top | MSX display top |
|---|---|---|
| Player | E1+33 | E1+17 |
| Torpedo | E1+40 | E1+24 |
| Lane enemy / ball | 65+24*(3-lane) | 48+24*(3-lane) |
| Patrol 8-row rectangle | 45, with nonzero rows46..52 | 30, with nonzero rows31..37 |
| Score / life / rescued diver / logos | 9 / 22 / 178 / 190 | Extracted for subsequent HUD composition (#13) |

The lane ball and enemy now share the same display top, matching the source
raster. The patrol's hardware box is Y22..37, with its rectangle in rows8..15;
the first lane box is Y48..63. Full legal player Y13..108 keeps the eight-slot
strategy at four or fewer hardware sprites per line, including the torpedo's
correct seven-line offset from the player.

`scripts/graphics_palette.py` documents the fixed TMS hue/luminance policy;
`outputs/graphics/palette.json` lists mapped source main, horizon, enemy and
explosion colors. Typical mappings: original gold player18→TMS10, player2 AA→7,
water90→4, logo/diver86→4, patrol08→14, oxygen0C→14. Opaque black uses1;
sprite transparency0 is reserved. This is a fixed-palette visual approximation,
not RGB identity. Sprite player/death/diver colors follow source state and its
attract XOR/mask. HUD composition and background color transitions remain later
integration work; the benchmark still uses synthetic HUD names/background colors.

## VRAM and timing contract

The ROM sprite catalog contains 213 deduplicated16x16 patterns (6,816 bytes).
Only47 patterns are resident: interior animations plus every torpedo edge variant.
Sixteen scratch patterns are two alternating banks of eight object slots.
Total sprite-pattern VRAM is2,016 of2,048 bytes, at3800..3FDF. A clipped/surface
pattern uploads only into the bank not referenced by the currently visible SAT;
the next VBlank commits its pattern number. No active sprite bitmap is overwritten.

The enemy backend now reuses one48-byte staging lane at CC00..CC2F, uploads it
to the inactive VRAM cache immediately, and then prepares the next lane. Direct
stores replace slower indexed stores. Canonical interfaces, tile cache IDs,
192 background pattern bytes and352 VBlank commit bytes remain unchanged. This
recovers measured CPU time for the real surface/edge uploads without dropping
objects, changing game state or reducing simulation frequency.

The integration probe checks canonical RAM against independent original CPU
execution, background pixels, source-derived sprite pixels, palette selection,
the SAT terminator, scanline occupancy, unchanged visible VRAM before commit,
data-port spacing and the whole native+renderer budget. Native fixtures are
supplemented with full-density edge cases, independently varied lane shapes and
positions, and legal player positions/surface states. The paced probe reloads a
worst fixture for240 ticks; it remains a diagnostic, not natural gameplay.

Exact ROM hashes, versions, machine/settings and measured results are in
`references/graphics/`. Remaining CPU/ROM space is a constraint for successors;
any additional per-frame work must be measured again. Natural input/audio,
PAL, full gameplay and physical MSX acceptance are not claimed.

| Probe | Verified cases | Maximum measured cycles |
|---|---:|---:|
| Optimized synthetic renderer | 256 | 40,191 |
| Optimized native core + original enemy lanes | 4,238 | 51,298 |
| Native core + original sprite integration | 6,526 | 59,211 |
| Paced original sprite integration | 240 consecutive frames | 59,104 busy; 11,501 commit |

The integration leaves525 of59,736 cycles (0.88%) in the measured worst case,
with29-cycle minimum data-port spacing, stack minimumF374, intact RAM guard and
no skipped paced frames. This is fixture coverage, not a proof over every
reachable game state. The32KiB diagnostic has256 padding bytes after the linked
source ROM. Successors must reduce cost/space or demonstrate that their work fits;
the earlier #7 margin no longer applies.30 synthetic host tests,2,707 native
continuous-contract cases and the local public-CI script pass. Both deliberate
source-mask and VRAM-pixel corruptions are detected.

[Independent read-only review](../references/graphics/review.md) found no
actionable issues and independently replayed all6,525 saved VRAM preparations,
confirming that previous visible SAT/pattern data stay intact.

Negative controls:

```
SEAQUEST_GRAPHICS_INJECT_ASSET=player-0-0 .venv/bin/python -B scripts/graphics_reference.py
SEAQUEST_RENDER_INJECT_PIXEL=13 make render-graphics-bench
```

Both must fail. Rerun the normal targets afterwards to restore positive evidence.
