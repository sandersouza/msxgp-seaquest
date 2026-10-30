# Seaquest MSX1 — proposed design and delivery roadmap

Status: implementation underway; consult the GitHub project and linked delivery
plans for current issue status and verified evidence.
Date: 2026-10-30. Owner: sandersouza. Repository: sandersouza/msxgp-seaquest.
Project: https://github.com/users/sandersouza/projects/7 (MSX Game Ports).

## Intent and acceptance

Port Atari 2600 Seaquest to an unexpanded MSX1. Preserve the original rules,
movement, firing cadence, event order, collisions, spawning, difficulty, scoring,
oxygen, rescue cycle and game modes. Visual and sound adaptations must not change
those rules. A visually convincing demo is not acceptance of gameplay fidelity.

Use the supplied Atari 2600 binary as the behavioral authority. Use the Atari 800
source and executable to accelerate investigation, with every relevant difference
checked against the 2600. Use SeaQuestJs as a visual reference only; its gameplay
is not an oracle. Preserve original graphic shapes and lettering where the target
allows them; do not substitute branding.

Acceptance requires both deterministic state comparisons and emulator integration
evidence. Record ROM hash, reference region, difficulty switches, mode, input
sequence, emulator version, machine, video frequency, scenario and verdict.
Real-hardware acceptance remains explicitly pending until it has actually occurred.

## Verified starting point

- Local branch main has two initial commits; tracked files are README.md,
  LICENSE and .gitignore. README.md is empty. References and .DS_Store are untracked.
- Supplied 2600 image: 4096 bytes; SHA-256
  fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43.
- Supplied Atari 800 XEX: 4393 bytes; SHA-256
  e97cee62f9a99003d78df122eacdd99a24d8e14bd3d0e7d6a497275e4aed86a1.
- Atari 800 source: references/dissasm/seaquest-atari800.s, 48182 bytes. Its header
  identifies a DiStella-derived Seaquest disassembly. It includes Atari 800 hardware
  access and macros, not merely an untouched 2600 dump. It contains self-modifying
  rendering code; that code cannot be copied directly into MSX ROM.
- Useful annotated variables include frame $81, seed $82, score $B8-$BA,
  lives $BB, wave $BD, divers $BE, player X $C6, player Y $E1, oxygen $E6,
  missile $E7 and rescue/refill/bonus flags $E8. These are investigation leads,
  not yet a verified mapping of the supplied 2600 binary.
- The Atari 800 lane renderer draws repeated enemies through playfield data;
  collision behavior depends on platform graphics hardware and requires analysis.
- GitHub repository exists and has no issues or milestones. Project #7 has
  Backlog, Ready, In progress, In review, Done; Priority P0/P1/P2;
  Size XS/S/M/L/XL and Estimate fields. Preserve this shared configuration.
- Homebrew, Python and openMSX are on PATH. The initial PATH check did not find
  sjasmplus, Stella, Atari800 or da65. This does not establish that they are absent
  from other locations. No dependencies were installed in this planning pass.
- New Rally-X provides useful make environment/environment-check/build/run/test
  conventions, a macOS setup dispatcher, a pinned local assembler approach and
  evidence scripts. Reuse those patterns selectively, not its MSX2 rendering stack.

## Approaches and recommendation

1. Recommended: reconstruct and port the original logic to native Z80 assembly,
   with independent video, input and sound backends. This makes timing, flag
   semantics and event order explicit and keeps a small CPU/RAM footprint.
2. Alternative: implement an equivalent state machine in C with SDCC or z88dk,
   optimizing hot paths in assembly. Easier high-level development, but introduces
   a larger semantic rewrite and requires measurement of generated code.
3. Rejected for this scope: adapting the JavaScript game's mechanics. It cannot
   establish original fidelity. A runtime 6502 interpreter is also not the default:
   hardware-dependent raster logic and CPU cost would add risk without solving
   the MSX1 presentation constraints.

The owner authorized publication of these roadmap issues and confirmed the
64 KiB RAM target. Rendering and toolchain choices remain subject to the planned
reference analysis and feasibility measurements.

## Proposed target architecture

- Z80 at standard MSX1 speed; TMS9918-family Graphics II / SCREEN 2, 16 KiB VRAM,
  standard AY-compatible PSG, keyboard and joystick. No MSX2 features, expanded
  RAM, turbo, sound cartridge or disk required to play.
- Target MSX1 with 64 KiB RAM and 16 KiB VRAM, without expansions, as confirmed
  by the owner. Aim initially for a plain 32 KiB cartridge, adjusting ROM size to
  measured requirements. Confirm BIOS/slot handling, stack and buffer use in the
  boot prototype. The ROM budget is a proposed target, not a proven size.
- Separate canonical game coordinates from display coordinates. Measure the
  source's actual active region; do not assume nominal console resolution defines
  gameplay bounds. Rendering transformations must not redefine collisions.
- Reproduce collision masks and ordering from source hardware behavior, including
  clipped/repeated objects and boundary cases. A convenient bounding box is not
  automatically equivalent to the original pixel collisions.
- Benchmark hardware-sprite rendering against a hybrid sprite/tile approach.
  Stress repeated enemies, diver/projectile lanes, player crossings, surface patrol
  and HUD. Respect the four-sprites-per-scanline limit and VRAM access spacing.
  Do not reduce object counts, slow simulation or hide collidable objects to pass.
  Do not assume scanline interrupts or MSX2 sprite features exist.
- Determine source region and actual frame cadence first. Establish a baseline
  against that exact version. Treat 50 Hz/60 Hz scheduling, input sampling and
  presentation as a separate compatibility contract. A fractional scheduler can
  preserve average time but does not itself prove identical input latency or
  frame-by-frame visuals across different refresh rates. Record unavoidable
  presentation differences; never silently slow gameplay on PAL.
- Translate TIA audio events into PSG effects, preserving event timing and
  priorities. Sound timbre cannot be assumed identical across these chips.

## Toolbox and developer workflow

Proposed tools: pinned sjasmplus for Z80; Python in a local virtual environment
for binary manifests, asset extraction and trace comparison; Stella debugger for
2600 disassembly/state capture; Atari800 and an assembler compatible with the
supplied source syntax (investigate MADS) for the secondary reference; DASM for a
reassemblable 2600 listing if required; openMSX for target debugging and timing.

The macOS setup script should support --check and --dry-run, Apple Silicon and
Intel, verify tools and versions, preserve existing environments, and install
project-local tools where appropriate. Pin revisions and verify downloaded sources.
Do not assume an emulator's debug interface is remotely scriptable: validate a
minimal capture experiment before committing to the automation backend.

Proposed layout: src/{core,platform,video,audio}, assets, scripts, tests,
docs, references/{roms,dissasm,traces}, outputs, .github/{workflows,issues}.
Generated outputs and local ROM inputs must not enter public commits by accident.
Keep original inputs untouched and record provenance/hash manifests. Public CI
should build from committed project inputs and use synthetic fixtures when original
ROMs are unavailable; distinguish this from local reference-ROM fidelity checks.

Proposed commands: make environment, environment-check, reference-check,
disassemble, extract-assets, build, run, test, compare, profile, clean.
They are planned interfaces, not commands available in this checkout today.

## Delivery sequence and proposed issue titles

Estimates below are initial implementation-plus-validation planning ranges, not
deadlines. Split L items if investigation reveals multiple independent deliverables.
No milestones exist; phase names below are planning groups, not created milestones.
Published issues use this same order (#1–#15); complete local copies are stored in
.github/issues/ with dependency links and their published URLs.

| ID | Phase | Proposed English issue title | Dependencies | Size | Hours |
|---|---|---|---|---|---|
| SQ-01 | Foundations | Inventory reference binaries and verify Atari 2600 revision and region | — | S | 2–4 |
| SQ-02 | Foundations | Reconstruct Atari 2600 disassembly and map differences in the Atari 800 port | SQ-01 | L | 12–24 |
| SQ-03 | Foundations | Specify original gameplay rules, state transitions and edge cases | SQ-02 | L | 8–16 |
| SQ-04 | Foundations | Bootstrap reproducible macOS toolchain and MSX1 ROM scaffold | SQ-01 | M | 6–12 |
| SQ-05 | Foundations | Configure CI, issue templates and MSX Game Ports project tracking | SQ-04 | S | 3–6 |
| SQ-06 | Feasibility | Capture deterministic Atari 2600 traces and define state comparison contracts | SQ-02, SQ-03, SQ-04 | L | 12–24 |
| SQ-07 | Feasibility | Benchmark worst-case SCREEN 2 rendering and approve sprite strategy | SQ-02, SQ-04 | L | 10–20 |
| SQ-08 | Playable slice | Extract original graphics and map MSX1 coordinates and palette | SQ-07 | M | 6–12 |
| SQ-09 | Playable slice | Port player movement, input sampling and original firing cadence | SQ-03, SQ-06, SQ-07 | M | 8–16 |
| SQ-10 | Playable slice | Port enemy lanes, spawning, random state and collision semantics | SQ-09 | L | 12–24 |
| SQ-11 | Full game | Port oxygen, diver rescue, surfacing and refill transitions | SQ-10 | M | 8–16 |
| SQ-12 | Full game | Port scoring, difficulty progression, lives and alternating-player modes | SQ-11 | L | 10–20 |
| SQ-13 | Full game | Reproduce original HUD, attract flow and PSG sound event timing | SQ-08, SQ-12 | L | 10–20 |
| SQ-14 | Acceptance | Validate video-frequency compatibility, input latency and worst-case frame budget | SQ-12, SQ-13 | L | 10–20 |
| SQ-15 | Acceptance | Run full-game differential regression and prepare hardware acceptance release | SQ-06, SQ-14 | L | 12–24 |

Issue publication: write each full draft to .github/issues/<slug>.md first, then
publish in English and attach to project #7. Include type, relevant category label,
exactly one priority label consistent with project Priority, Size, Estimate,
dependencies, Definition of Ready and Definition of Done. Start with P2 unless a
specific blocker justifies P1. Put unavailable issue types in the body rather than
changing shared configuration. Follow New Rally-X's current use of no milestone
unless the owner selects a milestone scheme. Do not create milestones implicitly.

## Gates and evidence

1. Reference gate: establish region/revision, code-vs-data map and correspondence
   of supplied source/XEX. Reassemble and compare complete load segments where
   practical; explain header, run-address or assembler differences explicitly.
2. Rules gate: extract exact constants and update ordering, not just manual prose.
   Cover diagonal input, facing reversal, held fire and both difficulty positions,
   oxygen alarm/depletion, surfacing with 0/1/5/6 divers, refill controls, patrol,
   bonus oxygen, enemy/diver point caps, extra lives, score limits, death, reset,
   attract and both player modes. Unknowns remain marked unverified.
3. Harness gate: reset and seed alignment, tick boundary and input sampling must be
   demonstrated using a short known sequence. Compare canonical positions, state,
   oxygen, timers, score, lives, enemies, divers, projectiles and RNG; stop at the
   first mismatch. Offline tests of supplied snapshots alone do not validate capture.
4. Hardware gate: demonstrate the highest-density source scenes on standard MSX1
   with measured cycles/VRAM writes, frame pacing, input latency and RAM high-water
   marks. Resolve feasibility before full-game implementation.
5. Delivery gate: replay natural full games plus controlled boundary tests, compare
   sound-event timing and inspect visuals. Separate automated checks, manual emulator
   verdicts and physical-machine verdicts. Package the exact tested ROM and manifest.

## Autonomy and reporting

After roadmap approval, routine implementation and project maintenance should
proceed without repeated supervision: one scoped branch/PR per issue, project status
updates at meaningful transitions, linked evidence, and no closure before the DoD.
Escalate measured conflicts with fidelity, target hardware or scope; offer concrete
alternatives with evidence. Do not substitute a new mechanic to overcome a renderer
limitation. Backlog publication does not install tools, scaffold the game, push
commits, or claim gameplay/hardware validation.

## Sources

- Original Activision manual, reproduced at AtariAge:
  https://atariage.com/manual_html_page.php?SoftwareLabelID=424
- Supplied binaries and references/dissasm/seaquest-atari800.s.
- SeaQuestJs source/reference: https://github.com/kortkamp/SeaQuestJs
- Stella debugger: https://stella-emu.github.io/docs/debugger.html
- sjasmplus: https://github.com/z00m128/sjasmplus
- DASM: https://github.com/dasm-assembler/dasm
- Atari800: https://github.com/atari800/atari800
- New Rally-X local Makefile, scripts/setup.sh, scripts/environment/macos.sh,
  evidence-script inventory, and current GitHub issue conventions.
