# Add MSX-DOS disk delivery and a plain cartridge no larger than 32 KiB

Type: Task (native issue-type persistence is unavailable in this repository).
Priority: P2. Size: L. Estimate: 16 hours, provisional until memory/compression feasibility is measured.
Project: MSX Game Ports #7. Milestone: none, following repository convention.

## Goal and owner authorization

Add two playable variants to the existing latest release, 1.0.0:
1. A program for the MSX itself, loaded from disk/MSX-DOS without a cartridge. The owner clarified that '.exe' means MSX disk execution, not a Windows emulator wrapper. Use the appropriate MSX-DOS .COM format and supporting files/disk image as required.
2. A complete plain MSX1 cartridge of at most 32,768 bytes, without a bank-switching mapper requirement.

Preserve the standard MSX1 target: 64 KiB RAM, 16 KiB VRAM, base Z80, TMS9918-family VDP and PSG. A disk interface/drive is naturally required for the disk variant; no additional RAM or sound expansion may be silently required.

## Context and dependencies

The existing [1.0.0 release](https://github.com/sandersouza/msxgp-seaquest/releases/tag/1.0.0) contains an unchanged, accepted 131,072-byte ASCII16 ROM, SHA256 `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`. Prerequisites #6 through #15 are delivered. PRs #33 and #34 publish the release/README. Keep the original ROM asset and immutable 1.0.0 tag intact; new binaries need their own reproducible source revision and identities.

Simply changing ASCII16 to Konami does not shrink cartridge capacity. Current banked data includes expanded enemy patterns, palette catalogs and forecast code. Measure reuse, compression, startup expansion and a complete RAM map before choosing an implementation. A plain32 build must preserve current fidelity and performance, rather than relabel or truncate the banked image.

## Scope

- Audit code/data sizes, bank access, spare RAM, BIOS/DOS ownership, stack and VRAM constraints.
- Design a shared compact representation/runtime layout if feasible; preserve original mechanics, presentation, graphics and audio quality.
- Implement reproducible disk and plain32 build/launch/package targets, with safe failure on unsupported machine/load conditions.
- Validate loaded code/data identities, RAM/slot ownership, original-state equivalence, full-density timing and PAL/NTSC behavior for both variants.
- Run complete-game/restart and rescue regressions on actual new binaries in private openMSX instances; test disk boot/loading, not just a memory-injected payload.
- Update README/release notes with exact requirements, distinct filenames, checksums, launch/loading commands and source revision.
- Add verified new assets to release 1.0.0; preserve existing asset/download/WebMSX links. No original Atari ROMs, BIOS or research replay bundles may be uploaded.

## Definition of Ready

- Owner clarified the disk target as native MSX/MSX-DOS.
- Existing runtime and 64 KiB acceptance references are available locally.
- Feasibility and implementation choices remain engineering work in this issue; do not claim plain32 is possible until measured.

## Definition of Done

- [ ] Disk program runs without a cartridge on an unexpanded 64 KiB MSX1 with disk/DOS support, with exact loading instructions.
- [ ] Plain cartridge is <=32,768 bytes and runs without ASCII16/Konami mapper emulation on the standard 64 KiB target.
- [ ] Full gameplay, graphics, audio and original mechanics are retained; measured frame timing and memory guards pass on final artifacts.
- [ ] PAL/NTSC complete-game/restart and rescue validation is recorded for each delivered variant; manual/physical qualification stays explicitly scoped.
- [ ] Independent review and relevant local/remote checks pass; scoped PR is merged.
- [ ] Latest release contains verified downloads, distinct manifests/checksums and correct instructions, linked to actual source revisions.
- [ ] Local issue copy, GitHub status and handoff agree. If a delivery condition is infeasible, document the measured blocker and keep the issue open instead of publishing a degraded build.

## Feasibility checkpoint — 2026-10-31

The unchanged playable rebuild reproduces the accepted 1.0.0 hash. The existing
renderer passes 39,328 original-state/pixel fixtures at a maximum 59,110 cycles.
A corrected 8 KiB enemy-cache diagnostic preserves all 39,328 canonical states,
VRAM images, VDP registers and name pages, but costs 61,243 cycles against the
59,736-cycle NTSC limit. Its paced test costs 60,915 busy cycles and skips frames.
That candidate is rejected and remains a 128 KiB ASCII16 diagnostic.

The current expanded layout cannot simply be loaded into 64 KiB RAM. Whole-image
host XZ compression measures 28,632 bytes but supplies no Z80 decoder or fitting
runtime. Exact role-based palette reconstruction is a promising next reduction;
its CPU, shared memory layout and native load paths are unimplemented.

See `docs/compact-delivery.md` and `references/compact-delivery/` for measured
scope, reproduction and remaining design work. This checkpoint does not prove
that a redesigned port is impossible. All delivery checkboxes remain pending;
keep this issue open/In progress, and publish no degraded or unverified binary.
