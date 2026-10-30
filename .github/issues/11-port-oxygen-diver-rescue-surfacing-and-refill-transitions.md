## Goal
Implement oxygen drain/alarm/depletion, diver pickup, full/partial rescue cycles, surfacing penalties, refill controls and bonus transitions.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #10: Port enemy lanes, spawning, random state and collision semantics

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] Match reference state and event timing for 0/1/5/6 divers, simultaneous oxygen/surface events, pickup limits, death and refill. Preserve controls and enemy behavior during transitions.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-11
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: M
- Estimate: 12 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/11

## Implementation and evidence

Delivery PR: https://github.com/sandersouza/msxgp-seaquest/pull/27.

The omitted original F44F→F473 HUD block now supplies the logical oxygen alarm
before every integrated F5B8 update. The translated original oxygen, pickup,
surfacing, refill, death and bonus algorithms and their event order are retained.
Explicit ascent14→13/next-tick surfacing, drain19/20 boundaries,0/1/5/6 divers,
simultaneous contacts, pickup caps, wave/group wrap and continuous controls pass.

24,605 oxygen contract cases,768 Atari alarm scenarios and17,647 integrated
pixel/state cases pass. Maximum59,311/59,736 cycles leaves425; the32KiB cartridge
has1,536 padding bytes. A direct right-edge tile path fixes natural frame overruns
while retaining pixels, objects, transfers and update frequency. 240 paced frames
pass without skips, with29-cycle VRAM spacing, stackF370 and intact guard.

6,262 uninterrupted cold-boot controls updates match Atari contacts and the
original CPU, with no game-RAM reloads or skipped VDP frames. The session contains
12 pickups,1 partial rescue,512 alarm ticks,1 oxygen depletion,6 deaths and7 refills.
Full rescue/bonus/refill passes in seeded continuous chains; this natural session
does not complete a full rescue. Maximum natural work is59,107 cycles.

Regressions:40,748 collisions;2,707 native;5,660 actual input;647 graphics scenarios
plus299 edges;6,526 graphics renderer;9,598 isolated input/renderer;36 host tests
and local public CI. Intentional runtime alarm corruption fails immediately,
followed by a passing normal contract. Independent read-only follow-up at
47f74dc3fba64e2258671bebf77ca678a704c690 found no actionable findings, recomputing
all24,605 expected records,6,129 chain continuations and6,262 natural updates,
and directly checking1,280 clipping cases. Both remote checks passed there;
the final delivery head must also pass before integration.

See [phase and reproduction](https://github.com/sandersouza/msxgp-seaquest/blob/main/docs/oxygen-rescue.md)
and [exact evidence/review](https://github.com/sandersouza/msxgp-seaquest/tree/main/references/oxygen).
Original-derived art, tables, ROMs, listings and replays stay local and ignored.
HUD/background remain synthetic; PSG audio, full-game, PAL and physical MSX
acceptance remain later work. Successor handoff: docs/handoffs/issue-12.md.
