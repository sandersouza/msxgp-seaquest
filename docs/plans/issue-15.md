# Issue #15 execution plan

Base: `19940e8fb08ac8269990725b88a70e8c56156e16`, clean main after PR #31.
Branch: `codex/chore/15-full-game-acceptance`. One implementer; independent
read-only review before integration. Runtime and owner-approved HUD stay intact.

1. Extend the existing video differential harness with cold, device-only full
   games: both selections, all four independent difficulty combinations, NTSC
   and PAL. Require exhaustion, game over, restart, correct active players and
   uninterrupted source state. Keep deterministic device replays locally.
2. Exercise successful rescue/oxygen play and retain the inherited controlled
   boundary/phase/density/rebase evidence against the identical cartridge hash.
   Verify every source update, sampled pixels, ordered PSG stores, frame budget,
   clock windows, stack and RAM guards. Deliberately reject incomplete games.
3. Freeze the exact tested 128 KiB ASCII16 cartridge and matching symbols into a
   local-only acceptance package with hashes, reproduction inputs and concise
   public evidence. Do not package the generic 32 KiB build diagnostic.
4. Provide command-by-command emulator and physical acceptance instructions plus
   a fill-in observation record. Separate automated checks, manual viewing and
   listening, and real hardware. Do not invent subjective or physical verdicts.
5. Run relevant host checks and local synthetic CI, obtain independent review,
   resolve findings, publish a scoped PR, verify remote CI and integrate when
   issue acceptance is met. Physical acceptance stays pending until observed.

Original inputs, cartridges, snapshots/replays and captures remain ignored.
Never operate or overwrite the owner's existing visible openMSX sessions.
