# Issue #35 execution plan

Spec: `.github/issues/msxdos-and-plain32-delivery.md`. Base `c987420`.
Branch: `codex/feat/35-msxdos-plain32`. The owner explicitly authorized
autonomous feasibility, implementation, review, integration and release work.
Use the current checkout as requested; no concurrent implementation.

1. [x] Preserve the incoming handoff, confirm live issue/release state and
   reproduce the immutable accepted image. Read local and Obsidian guidelines.
2. [x] Measure useful bank payloads, compression and complete RAM ownership.
   Distinguish storage compression from the expanded runtime working set.
   Consult primary DOS specifications for TPA, BIOS calls and system ownership.
3. [x] Build a private compact-enemy spike using the existing exact 8 KiB
   expansion cache instead of 29 KiB of prepared transfers. Retain full original
   graphics/HUD/audio and compare states/pixels and full-density frame costs.
   This spike still uses ASCII16 and is not a disk/plain32 delivery candidate.
4. [x] Choose a shared runtime only when both the 64 KiB DOS memory budget and
   plain32 storage/slot layout fit. If a tested approach misses the acceptance
   gate, retain the measured blocker and required redesign; never infer that
   the game itself is mathematically impossible on this hardware.
5. [x] For viable candidates, implement native disk and plain32 loaders and
   reproducible packages. Verify real loading, RAM/slot/stack guards, original
   state/pixels/PSG, full-density timing and PAL/NTSC full-game/rescue routes.
6. [x] Obtain independent review, run local and remote checks and integrate a
   scoped PR. Publish new assets only after their own gates pass; preserve tag,
   original assets and README image/WebMSX order. Otherwise keep #35 open,
   publish no candidate binaries, and synchronize measured blockers/handoff.

Review focus: DOS1 on a 64 KiB MSX1, expanded RAM slots, BIOS visibility while
using low RAM, page/stack overlap, actual disk boot versus memory injection,
and compression estimates being mistaken for a usable runtime.

Current implementation: PR #37. The flat runtime and both real loading paths
now fit and pass their complete automated qualification; see
`docs/native-delivery.md` and `references/compact-delivery/native.json`.
PR #37 is merged and the five new native assets are published and read-back
verified in release1.0.0; see `references/compact-delivery/publication.json`.
No implementation/delivery step remains. The earlier ledger below records
the initial rejected design, not the final native implementation.

## Decisions and evidence ledger

- Initial baseline: 67 host tests pass. Production rebuild is 131,072 bytes,
  SHA256 `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
- Existing release and project state were inspected live: #35 open/In progress;
  original release asset identity matches. No release mutations performed.
- First measurements: zlib of the whole ROM is 40,925 bytes; LZMA is 28,632
  bytes. These host compression measurements supply no Z80 decoder, RAM layout,
  load path or timing proof.
- Baseline: 39,328 original-state/pixel fixtures pass; 59,110 unpaced cycles,
  58,782 paced busy cycles. This bench ROM is distinct from the playable.
- Corrected compact enemy diagnostic: all 39,328 canonical/VRAM/VDP comparisons
  pass, but 61,243 unpaced and 60,915 paced cycles fail; frame steps include 2.
  The diagnostic remains 128 KiB ASCII16. It is rejected, not a smaller release.
- Independent review corrected the initial prototype's fast-transfer comparison
  and identified palette factorization as further engineering work. Final review
  found no P1/P2 issues; stale-result cleanup, VDP-state comparisons and explicit
  descriptor overhead were added. Host reconstruction proves the 70 RGB fields
  factor through 24 roles, but no Z80 palette implementation is validated.
- Detailed evidence and next design work: `docs/compact-delivery.md` and
  `references/compact-delivery/`. Steps 4–5 remain unfulfilled. #35 stays open and
  In progress. No disk/plain32 candidates or release assets were published.
