# CI and Tracking Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete #5 with a public synthetic build/test workflow and scoped delivery conventions.
**Architecture:** Pinned GitHub actions and sjasmplus compile the diagnostic on
Ubuntu without original inputs; issue/PR templates document acceptance and tracking.
**Tech Stack:** GitHub Actions, Bash, Python 3.12, sjasmplus 1.24.0.
**Spec:** ../specs/2026-10-30-seaquest-msx1-design.md

## Constraints and review focus

64 KiB RAM / 16 KiB VRAM target; no original ROM/source published; read-only job
permissions; explicit diagnostic artifact; correct dependency/status/priority
tracking; local checks do not substitute for a real green GitHub run.

## Tasks and ledger

- [x] Add portable synthetic checks, original-input tracking guard and pinned workflow.
- [x] Add task/PR templates and status/acceptance conventions.
- [x] Run shellcheck and local synthetic build/test path (ten tests, identical ROM hash).
- [ ] Fresh review, green GitHub run, focused PR and project update.

Started after #4 delivered in PR #18; #3 remains Ready for the original-mechanics
contract. Do not alter unrelated project items or shared fields.
