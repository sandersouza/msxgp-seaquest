# Issue #11 handoff — oxygen, rescue, surface and refill transitions

Continue only in the dedicated `ISSUE #11` chat in the Seaquest project. Reuse
that chat if present. The #10 chat stops all shared-checkout changes after dispatch.

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Codex project: `745758fe-48e5-471b-950b-4a2cee9dea9a`.
- Issue: https://github.com/sandersouza/msxgp-seaquest/issues/11.
- Project item: `PVTI_lAHOAJR8nM4Bn8x0zhEz03Y` in `PVT_kwHOAJR8nM4Bn8x0`.
- Dependency #10 delivery: https://github.com/sandersouza/msxgp-seaquest/pull/26.
  Implementation head: `89514e0d5405dff8201b5003b19b819335316e34`. Later delivery
  commits contain review/handoff metadata; verify the final PR head, successful
  CI, squash merge/main and clean checkout before creating a scoped #11 branch.
- Owner authorizes routine implementation, independent review, scoped PRs,
  integration and autonomous succession toward a first playable MSX1/openMSX
  version. Do not repeat routine permission requests. Independent read-only
  review does not authorize implementation delegation.

Read AGENTS.md, docs/project-workflow.md, `.github/issues/11*`, the first-playable
plan, docs/gameplay-contract.md, docs/native-core.md, docs/input-controls.md,
docs/original-graphics.md and docs/collision-contract.md. Consult `personal` /
`codex-instructions` through Obsidian CLI: all 0- notes and relevant GitHub/Python
guidance. Honor the restriction to Obsidian skills unless explicitly requested.

## Supplied by #10

`make controls-run` now cold-boots actual keyboard/joystick input and **original
raster collision acquisition** before each F5B8→F00E update, including after
Reset/Select. The native original already contains lane/RNG/spawn/resolution and
oxygen/rescue/refill/bonus/death algorithms. Preserve their instruction/event
order rather than replacing them with independent high-level state machines.

Acquisition writes only B0..B6/F8. Source clear windows, doubled/reflected P0,
eight-pixel M0, per-row ball motion/width and repeated/clipped P1 geometry are
validated against original TIA latches. A zero repeat mask still leaves an
invisible P1 copy at X0; the HMOVE video bar does not remove collision pixels.
Repeat coordinate arithmetic preserves byte wrap before TIA160-pixel wrap.
F8 low bits read 7; bit 7 carries the separate patrol latch. Shared lane latches
retain the source 3→0 selection and native resolution priority.

With no death, the lives kernel CPY #2 leaves carry clear for zero/one reserve.
Death1..9 also clears carry; death10..23 replaces it with set carry. F1B5 ADC
selects patrol rows11..4 for clear carry, otherwise12..5 at raw lines45..52.
Both collision and display preserve the low-reserve and early-death variants.
It uses the existing inactive scratch slot; sprite VRAM remains2,016/2,048 bytes,
47 resident patterns plus two eight-slot scratch banks. Original graphics catalog
has226 deduplicated patterns. Display scaling/clipping never writes canonical RAM.

The collision renderer caches expanded FDA4..FDF8 rows by parity/phase/reflection
in32 ROM pages. SP gathers the same48-byte lane patterns while DI, then restores
the real stack. Short fixed transfers preserve >=29-cycle VRAM spacing. The
existing192 enemy-pattern bytes and 352-byte visible commit stay unchanged. BIOS
input can EI, so VDP IRQ generation stays masked and the sampler returns DI.

## Evidence and tight limits

Public evidence: `references/collision/`; see review.md for the independent
review and verification.md for commands/settings. Originals, derived tables/art,
ROMs, listings, snapshots and raw evidence remain ignored locally under outputs/.

- 20,374 original TIA cases; 40,748 acquisition/ordered-resolution cases. All 256
  phases/waves/seeds and 96 legal player Y values. Includes all base coordinates /
  repeat masks, simultaneous contacts, pickup limits and patrol normal/refill/bonus.
- 10,622 native/collision/input/graphics cases; **59,370/59,736 cycles**, leaving
  only **366 cycles**. Timed32 KiB probe padding: **1,536 bytes**.
- 240 paced frames without skips; 29-cycle minimum data spacing; 11,039-cycle
  maximum visible commit; minimum stack F370 and intact RAM guard.
- 659 uninterrupted cold-boot actual-control updates, original TIA/occupancy and
  original CPU comparison each tick; no game-RAM reloads or skipped VDP frames.
  Natural maximum busy work55,284 cycles. Event→state <=17.5734 ms and completed
  SAT upload <=29.7795 ms; host OS, physical input and visible scanout excluded.
- 2,707 native, 5,660 input, 6,526 graphics and 9,598 isolated neutral-contact
  input/renderer regressions pass.36 host tests and local public CI pass.
- Runtime B6 corruption fails immediately at the first acquisition; the normal
  contract passes afterwards. Separate input RPC tests intentionally retain
  neutral contacts to isolate input; the paced controls diagnostic acquires real ones.
- Timed probe SHA-256:
  `0990365dec54574eb3a17ead3838dd8d064a1d4049052e5c957211bb55ab14f2`.
  Cold-boot controls/collision SHA-256:
  `c6fd8c4271d160527ed6e0e3f5459f4eda1fbaa56e66a55d8eb28989da411dee`.

Never add work on top of these numbers without measuring it again. Resolve CPU /
ROM cost first if needed; do not reduce enemies, visibility, quality or frequency.

## #11 acceptance focus

1. Verify #10 merged/closed/Done and #11 dependency ready; create the scoped
   branch here and move only #11 In progress. No concurrent checkout implementer.
2. Validate source thresholds and phase ordering for oxygen,0/1/5/6 divers,
   pickup limit, partial/full/no-diver surfacing, refill blocking/completion,
   death and bonus. Use real acquired contacts and uninterrupted device controls.
3. Audit remaining source raster/HUD-derived state, especially F9 alarm logic
   around F43F–F47E. #10 replaces collision latches only; an F5B8 CPU differential
   supplied with native RAM does not certify omitted source HUD computations.
   Preserve source behavior where it feeds #11 transitions; distinguish logical
   alarm state from future PSG timbre/audio delivery in #13.
4. Remeasure the complete workload, actual pacing, stack/IRQ/VRAM and canonical
   state. Keep existing collision/input/graphics regressions and source oracle.
   Obtain independent review, passing CI and a scoped integrated PR.
5. Close #11 only after its own DoD; continue #12 in another dedicated project
   chat with a durable handoff and stop changes here after dispatch.

HUD/background composition remains synthetic; audio, full-game, PAL and physical
MSX acceptance are unverified. A running diagnostic is not acceptance of those items.
