# Independent read-only review — issue #9

Implementation head: `c21dc72086b36bc403bae404840c95268d16b804`.
Base: `3115e50c7994835ffc1e3b95592a9267be95247b`.
Date: 2026-10-30. Independent read-only subagent review; no build execution,
checkout changes or shared-output writes.

No actionable findings remain. Review covered keyboard/joystick mapping, active
player union, independent switch bits, original sample phase, BIOS/PSG/IRQ and
register contracts, carry/NZ liveness, BCD exclusions, native branch predecessors,
renderer row/column/copy reuse, sprite-bank addresses and acceptance coverage.

The reviewer independently verified all6,144 combinations of unsigned position,
mask and copy admission/columns, plus all64 physical sprite addresses. The CFG
has no overlapping decoded instructions; calls/returns/unknown exits remain
conservative flag barriers.

Independent replay of existing evidence at the immutable head verified9,598
VRAM preparations and9,597 transitions preserve previously visible names, colors,
SAT and patterns. The659 natural updates preserve continuity and match the
original6502 CPU. ROM hashes match the published metadata.

During review the instrumentation was strengthened to capture the actual paced
core return, reset neutral collision inputs every tick, poison input mirrors,
cover continuous held fire for both players/settings and stress active controls
with normal running/shot creation. Final positive and deliberate negative runs
passed their respective expected verdicts. Final CI is checked separately at
the PR head before integration.

This is controls-diagnostic acceptance. Remaining limits:367-cycle measured CPU
margin, neutral collision contacts, synthetic HUD/background composition,
unintegrated audio, PAL and physical MSX unverified. Full-game and collision
acceptance are not implied.
