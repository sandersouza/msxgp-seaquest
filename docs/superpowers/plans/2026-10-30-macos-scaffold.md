# macOS Toolchain and MSX1 Scaffold Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete #4 with reproducible local tools and a bootable diagnostic ROM.
**Architecture:** Read-only check/dry-run modes; pinned local assemblers; isolated
Python venv; standard BIOS SCREEN 2 cartridge; emulator smoke evidence distinct from gameplay.
**Tech Stack:** macOS Bash/Python, Homebrew, sjasmplus, DiStella/DASM/MADS, openMSX, Stella.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md

## Global Constraints

- MSX1 with 64 KiB RAM and 16 KiB VRAM, without expansions; initial plain 32 KiB ROM.
- Preserve existing environments and original inputs; no destructive tool resets.
- Synthetic build/tests do not require original ROMs; research rebuilds do.

## Review Focus

Check/dry-run must not install or create files; wrong tool hashes/commits must fail;
unknown platforms must fail clearly; stack/BIOS variables must not overlap; emulator
boot success must not be described as gameplay fidelity or physical-machine acceptance.

## Tasks

- [x] Write ROM format/length/header validation tests and observe failure.
- [x] Implement version/hash checked macOS environment modes and local tool setup.
- [x] Build diagnostic cartridge and verify binary structure.
- [x] Run isolated C-BIOS MSX1 smoke test, record machine/VDP/RAM/signature/VRAM evidence.
- [x] Document workflow, review, publish PR and update project (PR #18; merged 5e41f21; #4 Done).

## Ledger

Started #4 after #1 completed. #3 is Ready after #2 completed; #4 has no dependency
on #3 and can supply the target/tooling needed by later reference capture.
