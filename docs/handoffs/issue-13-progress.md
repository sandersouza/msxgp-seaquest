# Issue13 implementation ledger — ongoing, not acceptance

Owner: dedicated ISSUE #13 chat, sole implementer. Branch
`codex/feat/13-original-hud-psg`; base main9a08956. Issue13 is verified In progress.
No commits/PR yet. Follow the main issue13 handoff and project workflow.

## Current checkpoint — source frozen, final verification/delivery pending

- Full HUD+PSG39,328/240paced PASS before the final name-page offset saving:
  59,705/59,736 (31free),29-cycle VRAM spacing,1,478commit max, stackF370,
  immutable HUD/stack/RAM guards intact. Hash1ed1352849333d443a876dc9b1939a3a195d87fc604659adcf73de0ffbe97e88.
  Log outputs/presentation/audio-second-full.log. This is superseded target code
  only by the final0/4 name-page representation saving216cycles/frame; the final
  full39,328 run still must be reproduced at the final hash.
- Final private audio64 target hash9782ddd79e58f26cb688d81d7d0132e8723f9f5025af1c0cfa9942227fa44b73.
  Compilepassfixedbank7F20 (224padding), bank1BFFB (5padding),64KiBASCII16.
- Focused1,000 HUD cases PASS, max59,489, including all100 digit pairs/both
  players,512palette combinations,256ripple seeds and32full-suite heavy cases.
  Font priming deliberately uses999999 before the exact target score: all three
  missing middle glyphs upload24bytes and previous display stays valid. Output
  outputs/presentation/sweep/result.json. Last native fullworst changed tocase6468
  before font stress; allscenarios remain source-derived display fixtures.
- Ordered audio contract PASS7,982ticks/34,692stores/45source store sites,
  controls0/4/8/12/15,72..934hookcycles. Includes2,400 continuous native chain
  ticks for six-diver surfacing, depletion and full bonuses; no game-RAM reload
  or PSG reinit after each chain's first tick. Compare rawstore/order/source81,
  canonical251RAM and actualPSG0..10 after every event. All main registers,
  SP/IFF, PSG7peripheral bits andPSG15 preserved. Negativevolume injection was
  detected at tick0:FFC3; clean positive rerun passed. AudioModel uses math;
  no target color/sound tables enter expected values.
- Cold private controls ROM3cf7b27000519b3f78cfa84195d8eb131a3dc3a8b2ee7c9b71b218b4e5ddf7b5
  PASS6,420updates from firstsource update/15,807ordered audio stores, no game-RAM
  reload, no missed visible frames,53,405maxbusy. Startup cacheprepare48,071 with
  display disabled. CPU/TIA acquisition and entire canonicalstate checked each
  update;16deaths/14deathswitches/13attractswaps/2gameovers/1restart/all4difficulty.
  Device-only six-diver collection is NOT claimed; full bonuses have seeded chains.
- Local public CI PASS46tests (one optionalpy65 test skipped in systemPython),
  syntheticboot/render/input/collision/PSG assembly. Venv46hosttests pass with
  py65. Final progression contract PASS55,243 incl25,072score register/flags and
  8,800chain ticks;264original omitted-display audit stillonlyB0..B6/F8/F9.
- Core optimizations: inlineFFAF fourLSRs withfinalcarry capture; deadNZ transfer
  OR elimination; FB56 ascending clear with low-byte wrap; bonus-loop-local IY
  dispatch initializedF794 everyentry, selecting regular after firstcheck or
  exact single-call terminal return after saturation. All20calls/A3increments
  remain. No new source roots/branches into folded clear/bonus bodies allowed.
  Final low/middle score DAA already gives correctS/Z; removed redundantOR.
- Audio: per-store EXAF/EXX hooks, channel-specificperiod lookup, encodedcontrol
  parts, sharednoiseowner withsource0priority, idempotent source masks. DC/noise
  hold prior inaudible periods; changed tonal events write both period bytes.
  Timbre/phase/DC/amplitude/sharednoise differences explicit in docs/hud-audio.md.
- Sourcecolor normal-slot lookup occupies unused streamed PATBUF CC00..CCFF.
  Six resident foregrounds preserve source AC ordering and every pattern/visible
  transfer. Source82 water ripple now matches all256 seeds/attractcolors.
- Independent read-only stream_review checked stream/banks, slotbounds, source
  helper/clear semantics, bonus IY domination and160audio/25mixer policy vectors.
  Need final immutable implementation/evidence review, PR/remoteCI/integration.
- No commits/PR yet. Issue13 open/Inprogress. README/development/HUDaudio docs and
  publicmake presentation targets added; references/presentation public evidence
  and finaldelivery/issue14 handoff still need writing. Do not close issue early.
- Active sequential regression driver (session67801) runs native2963 inclall256
  clearX, input5660, collision40748, oxygen24605; logs outputs/presentation/*-final.log.
  Do not run other outputs/render builders until it completes. Then run final
  --audio --progression, save named artifacts before CI/other builders overwrite
  bench.rom. Full Python pixel checking takes several minutes at100%CPU.
- Public targets: make presentation (outputs/render/presentation-controls.rom),
  make presentation-run, make presentation-check, make presentation-natural.
  Full audio bench copies its ROM/sym to outputs/presentation/audio64 for focused
  checks. Natural --audio makes a fresh replay seed with its current cartridge.

## Earlier prototype notes (superseded where different)

## Latest state (supersedes prototype notes below)

- HUD/background full39,328 source-state/pixel cases now PASS, plus240paced
  frames, max58,698/59,736 (1,038 free),29-cycle spacing, commit1,399 max,
  stackF370 and immutable HUD/RAM guards intact.64KiB ASCII16 hash
  8083a13abc9d563b935d92957d0fc31e336b5bcd390fcfb1d4737235fd55e088.
  Exact named outputs: hud-precolor-full.{rom,sym}, -result.json, -pace.json,
  -worst.bin and -pace-start.tcl in outputs/presentation/.
- All39328 comparisons include current original HUD/scene TMS colors, nine SAT
  slots/last oxygen pixel, visible-before-commit protection with real R2, all251
  canonical bytes, source silhouettes/occupancy and source-ordered AC colors.
  Field/colour compiler tables are nearly8KiB including caches (D000..EF10),
  source data immutable6928 bytes; F000..F2FF guard is preserved.
- Six normal enemy foregrounds {1,6,10,12,13,14} with blue water are precolored
  in VRAM. Black slot0 is the mutable fallback for attract/other backgrounds.
  Per bank pattern layout: top1..72 enemies,73..178 player0 fonts,
  179..244 player1 resident font subset,245..250 two3-slot middle-glyph banks,
  251..255 backgrounds; middle1..180 enemies; bottom1..36 enemies/HUD37+.
- Player1 keeps all outer pair tiles and life icons resident; only a missing
  middle pair bitmap needs an8-byte upload, max3 per score change. Native glyph
  scratch bank flips only when the score changes. Need explicit all100 pair/
  bothplayer/max3missing-glyph stress coverage; current suite writes16 extra
  glyph bytes beyond39328*(old352 + new4SAT bytes + existing192/sprite uploads).
- New benchmark primes two display-only F00E frames per independently seeded
  fixture, restores exact RAM for measured F5B8 core. For input86=0 (synthetic
  cold/reset-derived cases lacking a previous display), presentation init uses
  boot85=0/86=FF only during priming. The exact input RAM is restored before
  timing and independent6502 expectation. This setup must remain explicit;
  it is not a preceding display of that invalid/cold source palette.
- Earlier131k oxygen peaks came from incorrectly priming black86=0 into all
  colors, then repainting an invented preceding scene. Mixed valid-palette
  cases reached64,470 with old per-frame attributes; normal precolored slots
  solved that without dropping pixels,192 pattern bytes or352 visible bytes.
- Direct constant-colour VRAM fill replaces RAM/stack staging and preserves
  exactly29cycles/write (OUT12 + INC HL7 + NOP5 + NOP5). Runtime colour fallback
  is correct in isolated default-color probe; attract palette timing/pixels
  remain to sweep, especially source82-dependent surface glints.
- Bank0 code currently ends7D20 (736 bytes spare); bank1 endsBF00 (256 spare).
  Generated hud_build_colors and hud_enemy_init execute in bank1; all gameplay
  core/mapper transfers remain fixed bank0 and restore bank1 before other calls.
- Cold controls bootstrap now enters paced_frame_start before the first commit;
  display stays disabled until a complete valid name/color/SAT commit.
- Read-only reviewer found no simple5k native flag gain. Useful pending option:
  specialize FB56 zero-clear, preserving ascending stores/wrap, A0/XFB/Y/CNZ.
  It helps Reset/Select; max mixed has no Reset or score calls.
- Audio NOT implemented yet. Next: add per-source AUDC/AUDF/AUDV store hooks,
  preserving main AF/BC/DE/HL/IX/IY/E with EX AF/EXX; output actual PSG changes
  immediately in source event order (not one final frame snapshot). Cache
  idempotent writes; skip tone-period changes for DC/noise-only types.
  A suggested platform cache region is C460..C46C, free after collision C452.
  PSG7 high direction bits and PSG15 must remain intact. Hook source direct
  STA/STX/STY zpg/abs15..1A only; full-reset indexed hardware clearing is startup
  initialization, meaningful F5B8 paths use direct stores. Need independent
  source event traces/onset/duration/priority and timbre document.
- Suggested audio data251bytes fits the last bank1 pageBF00:3*32 tone words
  (pure4 periodround114*n/16; pure12 round342*n/16; noise15 approximation),
  noise32, mixerparts16, init11. Audio hook engine ~500bytes should fit bank0.
  Source original uses controls0,4,8,12,15; verify through traces.
- Public issue13 DoR checked and ongoing progress synchronized. DoD remains
  unchecked/open. Source/graphics/licensed inputs stay local/ignored. No PR yet.

## Evidence already reproduced

- Original #12 baseline:39,328 cases/240paced pass,59,311 cycles/hash4c6f9d1f….
- `--stream`: same cases/pixels/transfers/pacing pass,57,173 cycles,2,563 free;
  local outputs/presentation/stream-only.{rom,sym} and stream-only-result.json.
- `--stream --packed` plus unrolled shape setup: same pass,56,718 cycles;
  hash1098509691bd57dafe655680020dd47741ec10d8bb3e69100f02d9e0c747176a,
  4,608 ROM padding. Named packed-full files in outputs/presentation/.
- `--banked --progression`: same39,328 and240paced pass,55,651 cycles,
  4,085 free, same192 enemy/352 visible bytes,29-cycle spacing, stackF370,
  11,039 commit.64KiB ASCII16, same MSX1/64KiB RAM/16KiB VRAM. Hash
  0d4278b6961b1d0311d120b9b95ea4ee714d21e2feb207b54402e558f2e19e4b.
  Named banked-full files in outputs/presentation/.
- Independent read-only stream_review verified18,176 direct-stream address
  cases; then all608 banked image/pointer vectors,19 source-window mappings,
  FC00..FFFF and7/2 aliases, all core code in fixed bank0 and bank1 restoration.
- `hud_reference.py`:321 original ALE states/1,284 field comparisons pass:
  BCD score/leading blanks, all reserve/diver counts, all256 A3 logo values,
  six-diver flashes, both players and attract palettes. Model takes source RAM.
-42 synthetic host tests pass. Runtime audio/HUD integration is NOT accepted.

## Working code and open constraints

- core_codegen maps F7ED to7 bytes and FB52 to2; rejects other reads belowFC00.
  Source bounds: F7B4 Y2..6; FB28 X0/1 from latched facing. Packed renderer links
  FC00..FFFF only; original.rom remains full4KiB for independent host oracles.
- Banked layout: fixed code4000..7FFF; source/art data bank1 at8000..BFFF;
  pre-expanded enemy banks2/3 temporarily select page2 through7000 and restore1.
 608 images/29,184 payload bytes preserve48-byte per-lane transfers/split lane0.
- Original HUD in32KiB overflowed1,536 bytes before audio, after packing. Issue13
  explicitly allows initial32KiB ROM target to grow for measured needs.
- hud_tables generates compressed source data/startup LZ into D000..beforeF000;
  original art/derived pixels/tables/ROMs stay ignored. Current immutable blob
  ~7KiB plus1,024 color-cache bytes nearly fills D000..EFFF. Guard tests must
  reserve this declared region and still check F000..F2FF and stackF300..F37F.
- HUD uses64 name bytes scattered over score/life/diver/logo/oxygen, plus one
  4-byte SAT entry. Sprite63 at3FE0 uses the last32 VRAM pattern bytes: it
  restores the exact oxygen border pixel when three colors share a TMS row
  (oxygen1..4, x80, y153..156). Nine SAT slots; no actor scanline conflict.
- Static background includes original sky/water/seabed; top blank gaps compress
  score toY0, life toY8 (8 nonblank source rows), sky17..28; actors unchanged.
  Glyph fields shift+1MSX pixel toX96 for9-tile alignment. Bottom diverY160,
  logoY176, oxygenY152. Source seed-dependent surface ripple still needs audit.
- Two name tables1800/1C00 allow name preparation during active display; R2 flips
  at VBlank. Current benchmark decode/signature/R2 capture and SAT9 acceptance
  have NOT yet been adapted; do not run HUD full harness until those changes.
- hud.asm is prototype. Startup unpacker byte-check passes in hud_probe.py.
  Valid current prototype steady one-case probe is58,933 cycles before audio.
  First arbitrary seeded field-cache fill is93,558; not a passing frame budget.
  Field color caches now use exact mapped color signatures (up to4 role nibbles),
  raw source keys only for two multi-hue sky classes. Header B7 is still dynamic.
- Next planned improvement: preload both player header palettes in spare bank0
  pattern slots. Only tile50..55/114..119 are enemies in SCREEN2 bank0, so the
  current exclusion32..55/96..119 wastes36 slots. Dual header atlas fits243 free
  slots; shrink oxygen blink table to17 entries (normal65 + blink17; currently
  duplicated65+65) to recover912 RAM bytes for the extra font data. No source
  pixels/frequency/transfer reductions. Cache original field bytes to avoid
  recomputing unchanged HUD pointers. Initial all-pattern palette prewarm can
  skip color checks until actual palette changes; later changes must be timed.
- Initial cold-control path currently commits uninitialized HUD pointers;
  must bootstrap through paced_frame_start, keep display disabled during init,
  then enable after the first valid SAT/name/color commit. No acceptance yet.
- Scene tile0 water and source enemy/background color transitions remain to
  integrate/verify. Audio playback is not implemented yet. Need original audio
  event/epoch traces and PSG onset/duration/priority checks plus timbre document.
- Native no-HUD synthetic and historical contracts remain available. Do not
  overwrite named accepted evidence with ongoing prototype builds.

## Development gotchas

- Reject R3 color-address aliasing as a CPU optimization on the target: openMSX
  VDP.cc/updatePatternBase and VDP.hh/TMS99X8A show TMS9918A/9928A coupling R3
  low mask bits into the pattern table. R3=E0 would also alias distinct patterns.
  This was investigated and rejected BEFORE implementation; do not pursue it.
- sjasmplus `MACRO name argument` has no comma after macro name; check assembler
  success before running a probe. Earlier invalid prototype measurements were
  discarded. `DUP` numeric variable does not text-substitute into labels; use
  numeric local labels. Assembler booleans can be-1; use IF for byte counts.
- OUTD decrements fullHL; direct stream needs16-bit+100 between columns.
- `hud_probe.py` uses private hud64 ROM/symbols, verifies startup unpacking, then
  runs one seeded frame three times. It is debugging, not full acceptance.
- Existing full renderer validation takes several minutes in Python. Serial
  shared outputs/render and outputs/native locks; independent private output
  probes are safe. Current full banked baseline run has completed.
- Only Obsidian skills. personal/codex-instructions all0-, GitHub/Python and
  documentation guidance were read through CLI.42 tests at last run.
