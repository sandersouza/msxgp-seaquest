# Issue #35 — MSX-DOS and plain 32 KiB delivery

Issue: https://github.com/sandersouza/msxgp-seaquest/issues/35

The owner requests adding two playable alternatives to latest release 1.0.0:
a native MSX disk/MSX-DOS program and a complete plain cartridge <=32,768 bytes.
The owner explicitly clarified that `.exe` means execution on the MSX from
disk/MSX-DOS, not a Windows package. Choose the appropriate `.COM` and supporting
files/disk image. Follow AGENTS.md: implement only in dedicated chat `ISSUE #35`.

## Starting state

- Checkout: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`, branch `main`,
  HEAD `c987420838f116363aee7f1598830c1c22f32857` before this handoff.
- Pending changes: only the new local issue copy
  `.github/issues/msxdos-and-plain32-delivery.md` and this handoff, both untracked.
  Preserve them and commit on the scoped issue branch. No implementation started.
- Release tag `1.0.0` remains at `6b741859464f32d20d1007c9b53bd9f474643f92`.
  Branch `release/release-1.0.0` is at `c987420` (README follow-up).
- Existing `seaquest.rom` is 131,072 bytes ASCII16, SHA256
  `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
  Keep existing assets and tag intact. Distinct new files/manifests must identify
  the actual new source revision, rather than pretending they are the old image.

## Initial findings (read-only; not a feasibility result)

- `src/render_bench.asm` lays out fixed code in bank0, source/data in bank1,
  enemy expansion in bank2 and palette data/code in banks3–7.
- `src/enemy_banked.asm` and `src/palette_fast.asm` switch ASCII16 page2 through
  `$7000`. `palette_forecast.asm` contains code normally resident in bank7.
- `scripts/render_bench.py` assembles the production palette variant and asserts
  exactly 131,072 bytes; `scripts/video_check.py --build-only` builds the playable.
- Existing smaller diagnostic variants are not full-game replacements. Changing
  mapper metadata or truncating the existing image cannot satisfy plain32.
- Compact shared data, startup decompression and RAM ownership need a measured
  design. Do not sacrifice palette, original graphics/audio, fidelity or timing.
- Standard 64 KiB RAM/16 KiB VRAM remains mandatory. Disk hardware/DOS is expected
  only for the disk variant; RAM mapper/turbo/extra audio must not be required.

## Prior verified evidence, not proof for new variants

Release preparation freshly reproduced the exact original 1.0.0 ROM, passed 67
venv tests and all18 independent device replays; local synthetic CI and remote
PR #33/#34 CI passed. A browser opened the public WebMSX link and loaded the game.
`references/acceptance/` and `references/video/` record the unchanged cartridge's
broader validation. New layouts/loaders need their own original-state, full-density,
PAL/NTSC, boot-from-disk, complete-game and rescue evidence. Manual/physical
acceptance and subjective audio remain unrecorded; do not backfill results.

## Next actions

1. Read issue copy, project workflow and relevant runtime/memory contracts.
2. Create `codex/feat/35-msxdos-plain32` from current main and preserve this handoff.
3. Audit bank payloads, code, compressibility and complete RAM/BIOS/DOS map before
   deciding implementation. Consult primary MSX-DOS/BIOS docs for loader behavior.
4. Build and validate both artifacts without regressing the accepted runtime;
   use scoped tests, independent review, local/remote checks and a linked PR.
5. Update GitHub project status and README/release instructions, retain the WebMSX
   link directly below both gameplay images, publish only verified new downloads
   to existing latest release and download-check all added assets.
6. If an acceptance condition is infeasible, record the measured blocker and keep
   the issue open. Do not silently deliver degraded graphics/sound or expanded-RAM
   builds. Continue autonomously within the owner's authorization.

The planning chat stops editing the checkout once the new issue chat starts.
