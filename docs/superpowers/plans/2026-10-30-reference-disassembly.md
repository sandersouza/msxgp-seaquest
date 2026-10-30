# Reference Disassembly Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete #2 with reassemblable local listings and explicit 800 hardware differences.
**Architecture:** Verify original inputs, run pinned DiStella/DASM and MADS, compare
entire binaries, and export address-only maps. Keep generated listings and binaries local.
**Tech Stack:** Python 3/unittest, DiStella 3.02-SNAPSHOT, DASM, MADS 2.1.8.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md

## Global Constraints

- MSX1 with 64 KiB RAM and 16 KiB VRAM, without expansions.
- Atari 2600 is the behavioral authority. Binary reproduction is not runtime equivalence.
- No original ROM, supplied source or generated disassembly enters public commits.

## Review Focus

Code/data boundaries are heuristic; label matches are not semantic identity;
binary identity includes lengths and all XEX headers; upstream short filename
buffers require short relative input; source originals must remain unchanged.

## Tasks and ledger

- [x] Validate original hashes; pin research tools and record versions/checksums.
- [x] Rebuild both complete binaries and compare byte for byte.
- [x] Observe failing tests, implement strict identity and listing map, pass nine tests.
- [x] Export 196 shared labels and code/data reachability ranges; document hardware differences.
- [ ] Fresh review, final checks, focused PR and project update.

Ruling: generated source/listings remain in ignored outputs/reference; only address
metadata and hashes are published. Tools are local and ignored; setup automation is #4.
Found and resolved: DiStella's 50-byte filename buffer traps on the full local ROM
path. Running with a short relative filename from an explicit cwd preserves bytes.
Both regenerated complete binaries matched initial SHA-256 values on 2026-10-30.
