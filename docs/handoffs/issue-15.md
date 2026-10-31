# Issue #15 handoff — full-game regression and hardware acceptance preparation

## Delivery record

Issue #15 delivery: [PR #32](https://github.com/sandersouza/msxgp-seaquest/pull/32).
Runtime remains the exact #14 cartridge. See
[acceptance evidence](../../references/acceptance/verification.md),
[independent review](../../references/acceptance/review.md) and
[hardware instructions](../hardware-acceptance.md).
The local-only ZIP is `outputs/acceptance/seaquest-issue15-41ec3b92e7a5.zip`,
SHA256 `c1ad0b986638e3b1ad7b59538dd4c1fcb3c9adeb7971f0e8ef4c80c3ec72d68a`.
It contains the exact candidate, symbols, reports, instructions and 18 replays;
59 members match its manifest. Complete-game/rescue matrix and all controller-free
replays pass 105,359 source updates. Independent final read-only review reports
no blockers. Manual emulator gameplay/listening, natural full-six rescue and
physical-machine acceptance remain unobserved; do not promote those to passed.
No original-derived artifacts were published. Owner visible openMSX sessions and
the protected cartridge paths below were not operated or overwritten.

The original start-of-issue handoff follows for historical reproducibility.

Start after [PR #31](https://github.com/sandersouza/msxgp-seaquest/pull/31) is
merged and issue #14 is Closed/Done. Resolve the actual merge revision from
GitHub; do not assume the runtime source hash below is the merge commit.
Use a new/reused dedicated `ISSUE #15` chat in the Seaquest project. The issue #14
chat stops checkout mutations after dispatch. There is one implementer.

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/15.
- Dependencies: #6 (already Closed) and #14 (verify delivered/integrated).
- Base: clean `main` after PR #31. Create a scoped `codex/` branch for #15.
- Read AGENTS.md, docs/project-workflow.md, `.github/issues/15-*`, this handoff,
  docs/video-frequency.md, references/video/verification.md and inherited
  docs/handoffs/issue-14.md. Use current source/evidence over historical prototypes.
- Use only Obsidian skills as requested. Read the personal vault's `0-` and
  applicable Python/GitHub guidelines through the CLI. Do not delegate
  implementation; independent read-only review remains authorized.

## Delivered basis

Runtime source is `87dceabbceb0a25e1d9cea6277d840818d358425`, combining issue #14
with approved score/OXYGEN lettering from PR #30. Later delivery edits record
verification and handoff. Original Atari 2600 NTSC4K remains gameplay authority;
Atari 800 addresses/mechanics are not interchangeable.

The target is standard-speed MSX1, 64 KiB RAM/16 KiB VRAM, standard PSG, no
expansion. The measured palette/pattern catalog justifies 128 KiB ASCII16 ROM.
There is no runtime 6502 interpreter. Original gameplay instructions, actors,
input samples and ordered audio stores are retained. The score/OXYGEN ink is
an explicit owner-approved MSX adaptation; do not revert it as a fidelity repair.

Original source cadence is 262 raster lines/update, 59,736 nominal Z80 cycles.
NTSC uses one source update per display. PAL adds 51/262 updates per display,
giving 313 source updates per 262 steady physical intervals. An extra update
acquires contacts after the prior complete preparation, executes after the next
commit, and omits only presentation. Every rendered frame still transfers all
192 enemy-pattern plus 352 name/display bytes. PAL sampling/presentation is
different; do not claim identical wall-clock onset or latency.

`VIDEO_PAL/ACCUM/PENDING` occupy C428..C42B; bit 0 is the one-time bootstrap flag.
Source Reset does not reset the pacing accumulator. Normal palette iterations
use `paced_wait`/`wait_vblank_next` to avoid discarding a newly arrived edge.
`paced_start` clears stale initial status; non-palette diagnostics keep their
earlier startup path. Timing hooks must include preparation, extra acquisition
and loop dispatch through `paced_wait`, not stop early at `paced_prepared`.

## Evidence and local candidates

[Verification](../../references/video/verification.md) and adjacent JSONs record
exact tools, settings, seeds/hashes, scenarios and endpoints. Fresh video checks
pass 449,644 display frames/514,802 source updates/60,937 pixel frames/132,262 audio
stores, with zero skips or visible commits. They cover 183 boundary/exit/B&W/UI
chains, all 262 accumulator alignments at Select255, dense states, rebase,
READY1/token240 and cold keyboard/joystick replay. All 210,426 steady clock
windows pass; the empty initial pipeline has a bounded phase offset.

Worst continuous NTSC busy load is 58,800/59,736 cycles (936 free); PAL is
67,300/71,364 (4,064 free). Full 39,328-case native/pixel probes reach 59,110.
Full presentation checks, 55 host tests and original-free local CI pass. Review
and remote integration state are on PR #31. Cold event-to-state/SAT maxima are
18.1615/30.8782 ms NTSC and 21.5883/37.5968 ms PAL, excluding host input/scanout.

Preserve these ignored frozen baselines and matching symbols/manifest:

- `outputs/video/seaquest-issue14-final.rom/.sym`: ROM SHA256
  `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
- `outputs/video/seaquest-issue14-bench.rom/.sym`: ROM SHA256
  `23f21dbc42bdbc190e8499257e5bfec9bd39148f54c7bdd9c52d0252fea1c7c9`.
- `outputs/video/issue14-manifest.json` records both symbol hashes.

Both cartridges are 131,072 bytes ASCII16; addresses differ between variants.
`make build` still produces the separate generic diagnostic; it is not the
source-derived playable candidate to package for issue #15.
Reproduce serially with `make video-check`, then `bash scripts/ci.sh`. Builders
share outputs. Use fresh private headless process names and matching ROM/symbols.
Negative controls deliberately disable extra updates or corrupt staged E6 and
are rejected before they can masquerade as source-equivalent clock behavior.

## Invariants and remaining work

Keep bank-1 source/data and fixed helpers that restore mapper 1. Fixed-bank
padding is now 267 bytes; source data still ends at 9B00 with zero padding and
live 9900/9A00 pointer tables. Immutable HUD D000..EBFF/cache EC00..EFFF end F000.
C280/282/284/C296 are reserved hardware mirrors; C100/C200/C300 contain platform
buffers. Restore only 251 canonical bytes plus explicit hardware fields in
seeded tests, never a blanket 1,024-byte canonical snapshot. Preserve SP/DI/PSG15.
Cold stack watermark F35E includes BIOS startup; seeded watermark is F370.

Preserve permanent default token 1, no reused cancelled IDs, early rebase only
when PAL_READY=0, READY1 epoch through activation/cancel, and exact boot memos
before hidden warming downgrades ALL_CURRENT. Preserve source UID/pointer/A3
snapshot checks. Keep 47 resident +16 scratch sprite patterns and pattern 63 for
the oxygen border, all eight actor slots plus overlay and four sprites/scanline.
Water uses colour 0/R7; opaque black is 1; divers/hostile shots/ripple retain
contrast. The external MSX border follows water.

Fast I/O remains inside measured VBlank or physical R1-off; restore slow dispatch
before R1-on. The TI manual covers TMS9918A/9928A/9929A standard clocks. No turbo,
MSX2 refresh-register override or physical-machine compatibility is established.

Issue #15 owns natural full games, controlled mode/difficulty boundary routes,
exact candidate packaging and hardware acceptance instructions. Keep automated,
manual emulator and physical evidence distinct; actual physical acceptance and
subjective timbre remain pending until observed. A boot is not a completed game.
Publish only code/docs/concise evidence. Original ROMs, generated art/tables,
states/replays/captures and original-derived cartridges stay local/ignored unless
the owner explicitly authorizes publication.

The owner has separate visible openMSX playtests. Do not stop/reload/send keys,
change settings or overwrite their cartridges. Preserve in particular
`outputs/seaquest-issue13-colors-fixed.rom` (f6b8e010...),
`outputs/seaquest-issue13-test.rom`, `outputs/seaquest-contrast-test.rom`, and
`outputs/presentation/seaquest-final-bench.rom/.sym` (0942a040...). Do not interact
with any other chat's font worktree/session. Continue #15 autonomously within its
acceptance, maintaining issue/project/PR status, with review and CI before close.
