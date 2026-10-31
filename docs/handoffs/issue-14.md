# Issue #14 handoff — video cadence, compatibility and input latency

Start only after [PR29](https://github.com/sandersouza/msxgp-seaquest/pull/29)
has passed final review/CI and merged. This document prepares the dependency
handoff; it does not authorize concurrent implementation in the shared checkout.
Use the dedicated `ISSUE #14` chat in the existing Seaquest Codex project; reuse
one if present. The ISSUE13 chat stops checkout mutations after dispatch.

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/14.
- Dependencies: #12 and #13. Verify closed/Done and PR29 merged before starting.
- Base: `main` after PR29 merge; resolve its actual merge commit from GitHub.
- Prior implementation branch: `codex/feat/13-original-hud-psg`.
- Read AGENTS.md, docs/project-workflow.md, `.github/issues/14-*`,
  docs/hud-audio.md and references/presentation/verification.md. The working
  history in issue-13-progress.md includes rejected experiments; final evidence
  and the integrated source take precedence over those historical prototypes.
- The owner authorizes routine scoped implementation, independent read-only
  review, GitHub lifecycle/integration and autonomous succession toward first
  playable. Do not repeat routine permissions or delegate implementation.
- Use only Obsidian skills unless explicitly requested otherwise; read the
  personal vault's0- guidelines and applicable GitHub/Python instructions via CLI.

## Inherited implementation and contracts

Original Atari2600 NTSC4K is gameplay authority; Atari800 disassembly supports
investigation but some addresses differ. Target remains standard Z80 MSX1 with
64KiB RAM/16KiB VRAM and standard PSG, no expansions. The128KiB ASCII16 cartridge
is justified by measured palette/colour-queue needs. No runtime6502 interpreter
ships. Source simulation, actor count, original assets and mandatory192enemy
pattern +352display/name bytes per rendered frame are retained.

The source core/data execute in bank1; mapper-changing helpers stay in fixedbank0
and restorebank1 before return. Bank5 contains sprite catalog/metadata and packed
HUD; banks2/3 enemy patterns,4 collectors,6/7/5/3 palette records; bank7 contains
forecast code. Check all bank assertions and exact131072-byte output. Fixedbank
padding is small; use current symbols, not historical free-space estimates.

Water uses colour0+R7; opaque black remains1. The external MSX border follows
water. Source86 divers/hostile shots and92surface ripple keep contrast with90water.
Six global enemy foreground slots plus private0 support palette changes without
water-keyed cache churn.47resident sprite patterns +16scratch reserve pattern63
for the oxygen-border overlay. Preserve all eight actor SAT slots and the ninth
border entry, maximum four visible sprites on each scanline.

Predictable palette/font/colour-queue work is spread over prior idle updates and
validated against actual canonical state/UIDs/pointers before activation. Cache
runtime token1 permanently identifies a class's default vector; other tokens
never reuse an epoch. Rebase clears physical tags and refreshes memos before
reuse. **Early rebase requires PAL_READY=0**: READY1 IDs must remain in the epoch
that produced them until activation/cancel. The translate-side guard remains.
Boot ALL_CURRENT1 is downgraded only after exact visible field memos are stamped
before hidden font writes. Do not reintroduce obsolete deferred cache markers.

Fast uniformOUT12/OUTI18 is selected only inside paced VBlank commit. TI original
DataManual2.1.5 p13 gives a4.3ms vertical-refresh window without slot waits. Active
picture writes keep29cycles. General fast short-copy dispatch only accepts1..64
bytes and only runs after physicalR1off; restore slow dispatch before R1on.
The blackout guard requires source86/E9/F6/AC0..3 allzero. Do not add black frames
or extrapolate this timing policy to turbo CPUs or different VDP modes.

Immutable HUDD000..EBFF, cacheEC00/ED00, RGBEE00/EF00 endF000; defaultRGBC700.
Preserve source251canonicalbytes, hardwareC280/282/284/C296, RPC C6F0, all stack/
VRAM guards. Forecast uses C100/C300/C200..27F/C2A0..FF; do not overwrite those
platform buffers by restoring1024bytes of canonical source RAM. Source zero-page
indexed arithmetic wraps at256 and must not address these platform buffers.

Native folds F619,FFDA,F644,F875,F8DE,F992 retain original ordered stores and
observed register/carry contracts, with incoming-entry guards. Preserve source
instruction phase boundaries and every ordered audio event hook; use original
CPU/ALE as oracle, not target caches. Reference cadence/PAL policy and full-game/
physical-hardware acceptance are still open, specifically #14 and #15.

## Evidence and next actions

The final verification document records exact cartridge hashes, all39328native/
pixel cases,240paced frames, focused1129images/font updates, continuous palette
boundaries/exits/rebase/ready-epoch chains,7982audio ticks,6422cold updates, all
native/input/collision/oxygen/progression regressions and CI. Reproduce serially
with `make presentation-check`; builders share ignored outputs. Human PSG timbre,
full-game route, real machines and PAL are not established by those diagnostics.

Read #14's acceptance before coding. Identify original source cadence and machine
video rates, then implement and measure the50/60Hz policy without reducing source
simulation speed or changing source phase semantics. Record worst load, input
sampling/state/SAT latencies and RAM/VRAM high-water marks for each supported
machine/rate. Existing NTSC source tests do not establish50Hz behavior. Preserve
all original UI/gameplay/sound and remeasure every ROM/input/renderer change.

Owner playtest artifacts remain local and ignored. Preserve
outputs/seaquest-issue13-test.rom and outputs/seaquest-contrast-test.rom if present;
never replace an owner's running openMSX session without their request. Original
ROMs/extracted art/generated tables/cartridges/VRAM dumps stay local; publish only
concise evidence, source/tooling and documentation. #15 owns the full-game
regression route and physical acceptance release after #14.
