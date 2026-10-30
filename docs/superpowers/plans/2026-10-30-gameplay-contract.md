# Original Gameplay Contract Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete #3 with source-grounded rules, ordered states and a trace acceptance catalogue.
**Architecture:** Derive the specification from the byte-identical original listing,
correct reference-map role descriptions, and separate static conclusions from #6 runtime traces.
**Tech Stack:** Original 6502 listing/symbols and Markdown research contract.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md

## Constraints and review focus

Original 2600 is authoritative; MSX1 64 KiB RAM/16 KiB VRAM; preserve byte/BCD/carry
semantics, prior-vs-new frame phase, collision latch aliases and resolution order,
reset-vs-start seed behavior, and seven-field player-state swapping. Static source
extraction is not a captured trace or gameplay acceptance. No production behavior changes.

## Tasks and ledger

- [x] Inspect original loop, input, collision, movement, oxygen, bonus, score, PRNG and player switching.
- [x] Record source addresses, constants and update ordering; enumerate runtime acceptance scenarios.
- [x] Correct LF689 and LFFDA role descriptions in the reference map.
- [x] Fresh domain review against original listing; resolve material discrepancies.
- [ ] Green CI, PR integration and project update; advance #6 after #3 completion.

#1/#2/#4/#5 completed first. #3 started once its reference disassembly dependency
was satisfied. Captured masks/coordinate mapping and actual frame timing remain
explicit #6/#7/#8/#14 acceptance work; the original source algorithm is binding.
Review corrections: patrol lookup starts two bytes before the displayed table
label (groups 2–4 every four ticks, 5+ every two); successful rescue conditionally
increments wave once rather than taking a maximum after byte wrap; held-select
counter 30 yields 31 updates between repeats. Enemy-value source starts at $F633.
