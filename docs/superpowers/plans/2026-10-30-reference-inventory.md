# Reference Inventory Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete #1 with immutable input identification and reproducible checks.
**Architecture:** A standard-library inspector verifies hashes and binary structure against a checked-in manifest. Research conclusions remain separate from measured runtime evidence.
**Tech Stack:** Python 3, unittest, GitHub CLI, Stella metadata.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md

## Global Constraints

- MSX1 with 64 KiB RAM and 16 KiB VRAM, without expansions.
- Original Atari 2600 is authoritative; original binary inputs stay local and unchanged.
- No runtime, region-revision or provenance conclusions without explicit evidence.

## Review Focus

Missing inputs must fail clearly; truncated XEX segments must fail; inclusive XEX
addresses must be parsed correctly; modified originals must fail manifest checks;
hash recognition must not be presented as measured frame cadence.

## Tasks

- [ ] Add tests for digest verification and malformed/valid XEX structures; observe failure.
- [ ] Add inspector and immutable reference manifest; pass synthetic tests and real-input check.
- [ ] Document reference identity, source provenance, switches and unresolved timing.
- [ ] Review changes, run checks, publish focused PR and update #1/project status.
- [ ] Continue #2 and #4 after the reference inventory delivery conditions are satisfied.

## Execution ledger

- Started #1 on codex/docs/1-reference-inventory; project status In progress.
- Ruling: use a dedicated branch in the current checkout, preserving the owner's
  untracked originals and the already prepared planning/draft files. No extra worktree
  is needed for this documentation and inspection delivery.
- Stella metadata matches MD5 240bfbac5163af4df5ae713985386f92; MiSTer explicitly labels
  that hash NTSC. Actual scanline/frame measurement remains separate evidence.
