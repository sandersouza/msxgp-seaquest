# Reference Trace Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver #6 incrementally without confusing replay equality with acquisition alignment.
**Architecture:** Optional pinned ALE adapter, manifest-verified ROM, explicit action/reset
metadata, post-frame raw RAM captures, first-mismatch comparator and real-ROM probes.
**Tech Stack:** Python/unittest, optional ale-py 0.12.1 and its NumPy dependency.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md and ../../gameplay-contract.md

## Constraints and review focus

Preserve original inputs; capture metadata cannot call ALE's warm reset cold boot;
distinguish ALE RNG from game seed; compare actions/phase/identity as well as RAM;
require repeatability and a detected injected mismatch; do not claim alternate
players, cycle-accurate native alignment or source clock measurement yet.

## Tasks and ledger

- [x] Observe failing comparator/parser tests; implement a standard-library synthetic path.
- [x] Capture local original via optional ALE with frame skip 1 and sticky probability 0.
- [x] Independently repeat 209 snapshots; verify frame-byte stepping and position/refill probes.
- [x] Verify B/A shot displacement and detect an intentionally changed real-trace X byte.
- [x] Fresh review of initial partial delivery: clean; PR #21 uses Refs #6. CI is checked before merge.
- [ ] Finish native phase mapping, exact timing evidence and additional source contract fixtures.

#1–#5 are delivered; #6 is In progress and #7 Ready. Initial ALE source inspection
confirmed 60-frame warmup and soft resets, solo-only exposed mode and difficulty
bit mapping. Initial ROM frame 67/seed 204 are recorded, not treated as reset zero.
