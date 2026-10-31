# Issue #15 independent review and delivery checks

Independent read-only agent review covered the validator, coverage predicates,
packager, replay reproduction, tests and acceptance instructions. Implementation
was not delegated. The reviewer did not modify files, run builders or operate
owner openMSX sessions.

Corrected findings:

1. Removed `--reuse`: its identity omitted transitive oracles/tool versions and
   could reuse stale results. Final acceptance always reruns all 18 routes.
2. Cold routes no longer read the old `outputs/input/natural.bin` game-over seed;
   that prerequisite belongs only to seeded boundary routes.
3. Replays are relocated by matching the cartridge SHA1, preserving BIOS paths
   and recorded events. The packager directly runs its relative `game.omr` from
   the extracted root against its copied ROM, without a feedback controller or
   raw reference trace. All 251-byte states/counts match the verified sequence
   hash for all 18 routes. This closes the review's portability check.

67 project-environment host tests and original-free local synthetic CI pass.
The final matrix passes 96,000 display frames /105,359 original source updates,
12,033 pixel frames, 238,674 ordered audio stores and 91,266 cadence windows.
All 18 replays pass both ordinary reproduction and extracted package checks.
The PAL READY1/rebase route passes; staged E6 corruption is rejected at tick 6.
Archive CRC checks and every member SHA256 pass. The local-only ZIP receipt is
[package.json](package.json); no original-derived media is committed.

The runtime cartridge remains identical to issue #14. Manual emulator gameplay,
subjective listening and physical-machine acceptance remain pending actual
observation. No new static review blocker remains after the corrected findings.
