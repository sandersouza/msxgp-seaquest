## Goal
Add reproducible build checks, useful issue/PR templates, artifact manifests and project conventions. Keep original ROM inputs out of public CI and commits.

## Target and fidelity contract
MSX1 with **64 KiB RAM and 16 KiB VRAM**, standard-speed Z80, TMS9918-family VDP and standard PSG; no expansions required. Atari 2600 is the behavioral authority; the Atari 800 port supports investigation and SeaQuestJs is a visual reference only. Initial ROM target is 32 KiB, subject to measured needs.

## Dependencies
- #4: Bootstrap reproducible macOS toolchain and MSX1 ROM scaffold

## Definition of Ready
- [x] Required dependency evidence is available; unresolved inputs are documented.
- [x] Reference ROM revision/region, relevant source inputs and validation scenarios are identified.
- [x] Scope and acceptance criteria below are understood.

## Definition of Done
- [x] CI builds project inputs and uses synthetic fixtures where original ROMs are unavailable. Record issue type, priority, size, effort, dependencies and acceptance evidence; distinguish public CI from local fidelity checks.
- [x] Relevant checks pass and reproducible evidence is linked (ROM hash, tool versions, machine, settings, scenario and verdict where applicable).
- [x] Documentation and delivery links are updated; unverified emulator/hardware claims remain explicit.

## Tracking
- Roadmap ID: SQ-05
- Type: Task (recorded here: the native issue type field did not persist through the GitHub API for this repository).
- Priority: P2 (normal backlog)
- Size: S
- Estimate: 4.5 hours, including implementation and validation; initial planning estimate, not a deadline.
- Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- Initial status: Backlog
- Milestone: none (existing repository convention).

Original ROMs are local research inputs; do not publish them accidentally. This issue excludes work owned by dependent roadmap items.

Published issue: https://github.com/sandersouza/msxgp-seaquest/issues/5

## Delivery evidence
- Merged in https://github.com/sandersouza/msxgp-seaquest/pull/19.
- GitHub Ubuntu CI passed: https://github.com/sandersouza/msxgp-seaquest/actions/runs/41086215493 (push) and https://github.com/sandersouza/msxgp-seaquest/actions/runs/41086215448 (PR).
- Ten synthetic tests and diagnostic build/check passed without original inputs; shellcheck and fresh independent review clean.
- Pinned workflow, diagnostic artifact/hash, issue/PR templates and scoped delivery conventions are documented in docs/project-workflow.md.
