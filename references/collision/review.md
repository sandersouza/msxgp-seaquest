# Independent read-only review — issue #10

Implementation reviewed against main f869722:
`89514e0d5405dff8201b5003b19b819335316e34`.
No actionable findings remain at that head. Subsequent delivery commits contain
documentation/evidence/handoff metadata only; CI must also pass at the final PR head.

The initial review of136cb88069defe0ff4f983306e46edce8ab1c35e found one P1
fidelity defect: with E9=0, carry into F1B5 comes from the lives kernel CPY #2.
Zero/one reserve selects patrol rows11..4, but the initial implementation and
Python expectations selected rows12..5. This could cause a false patrol death.
The acquisition, display selector and Python models were corrected together,
with low-reserve oracle fixtures and carry-override regressions.

The reviewer independently checked the corrected head without builds or edits:

- All10,622 backgrounds, sprite masks and native outputs using a separate
  original-ROM-byte decoder and pixel intersections plus py65 execution.
- All10,621 prior-visible VRAM transitions: preparation preserves currently
  visible names, attributes, colors and sprite patterns until commit.
- All659 uninterrupted natural updates against separate intersections/original
  CPU execution, preserving canonical acquisition state, strict continuity,
  consecutive VDP frames and the55,284-cycle natural maximum.
- Both final ROM hashes: timed probe0990365dec54574eb3a17ead3838dd8d064a1d4049052e5c957211bb55ab14f2
  and controls/collision c6fd8c4271d160527ed6e0e3f5459f4eda1fbaa56e66a55d8eb28989da411dee.
- All504 reserve/death/frame combinations against original6502 carry and
  ALE pixels. The exact BB=1,E9=0,E0=0,E1=14,C6=76,F6=69 counterexample now
  yields F8=07 in both the original Atari and running Z80 backend.
- The59,370-cycle integrated maximum and240 paced frames without skips.

The366-cycle CPU margin remains tight. PAL, full-game/HUD/audio and physical
hardware are unverified. Review scripts/results remain ignored under
outputs/collision/review-*; source art/data/ROMs and raw replay state stay local.
