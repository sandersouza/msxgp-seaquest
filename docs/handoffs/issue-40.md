# Issue #40 — oxygen color, attract credits and cycling HUD repair

Issue: https://github.com/sandersouza/msxgp-seaquest/issues/40
Dedicated chat: `ISSUE #40` in Seaquest project `745758fe-48e5-471b-950b-4a2cee9dea9a`.

## Owner request and authorization gate

Implement in this new issue/chat: filled oxygen bar yellow like the player's submarine, with depleted/empty rendering unchanged; add exact `retrowork 2026` to the lower Activision logo/text cycle outside active gameplay; reproduce and repair lower HUD corruption during non-gameplay color cycling. The original handoff did not assume a cause. Measured failures and the implementation are now documented in `docs/issue-40-candidate.md`.

**Deliver the local ROM/COM candidate for owner testing, then wait for explicit owner approval. Do not create any PR (even draft), merge, tag or publish until that approval.** After approval, perform independent review/PR/merge and publish a new release retaining the base release text and appending these fixes. This explicit user gate overrides earlier autonomous release practices. Keep the issue open while approval/delivery is pending.

## Exclusive checkout transfer

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Handoff base: `main`, commit `e315927ff846e9b019c1a68467523e35119decd8` (merged PR #39). Current issue branch: `codex/fix/40-hud-attract`; frozen implementation commit `a44811c68345d32041d0114c048276e169958430`.
- The initial issue/handoff files were preserved and committed at `0087519`. The implementation is committed locally; owner approval is still pending.
- The old ISSUE #35 chat stops modifying the checkout immediately after dispatching this handoff. The new ISSUE #40 chat has exclusive implementation ownership. Do not run concurrent issue implementations here.
- GitHub project #7 item `PVTI_lAHOAJR8nM4Bn8x0zhFNhjI`: In progress, P2, M, estimate 8 hours (provisional). No milestone. Labels bug/enhancement/priority:p2. Full local issue copy is authoritative for requirements.

## Current formats and source

`make` / `make build` / `make run` build/launch the complete ordinary 32 KiB Normal ROM `outputs/disk/SEAQUEST32.ROM`. `make build FORMAT=com` selects `outputs/disk/SEAQUEST.COM`. Both are emitted by the shared builder. COM run requires `MACHINE=<installed disk-capable 64K MSX1>` and `DOS_DISK=<owner DOS1 image>`; `scripts/play.py` imports current COM/AUTOEXEC into a temporary disk copy. Do not replace defaults with the old diagnostic or ASCII16 game.

Native qualified baselines (unchanged by PR #39):
- SEAQUEST32.ROM 32,768 bytes SHA256 `bf4bcb22b2303decbb2316cb673f1e979a5ba4c4e5e97591cd06f7560b8d942e`.
- SEAQUEST.COM 25,361 bytes SHA256 `b3e8051088a911943501b8bf1f1615afe45e1308fa2d944b80c8dbbc0004e79d`.
- Published binary build revision `0f11ed47d16cd8bda9531cd992db9afec8106f3c`; runtime SHA256 `b6fb79b91276a0d72761aa62423ce6e391fee3197dc6b4d8415318a8d2055c70`.
- Original `seaquest.rom`: 131,072-byte ASCII16, SHA256 `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`, separately retained.
- Current release https://github.com/sandersouza/msxgp-seaquest/releases/tag/1.0.0 ; annotated tag remains `aa93f67d4755067fceda42560f71c4da9d442050`, target `6b741859464f32d20d1007c9b53bd9f474643f92`. Latest base release prose is `docs/releases/1.0.0.md` on main, reflecting Normal default/WebMSX and separate ASCII16 history. Preserve its base narrative when preparing the later release; do not publish now.

## Read first / implementation entry points

Read AGENTS.md, docs/project-workflow.md, the issue copy, docs/native-delivery.md, docs/hud-audio.md and relevant current source. Required Obsidian guidelines are available through `obsidian vault=personal` in codex-instructions (0-defaults,0-tokenomics,github-instructions,python-virtualenv/project-documentation as applicable). Only use Obsidian skills for coding unless the owner explicitly invokes another skill, per user instructions.

Likely source entry points: scripts/hud_tables.py (hud_logo/oxygen tile vectors and role descriptors), scripts/hud_fonts.py, scripts/graphics_palette.py, scripts/disk_palette_tables.py, src/hud.asm, src/palette*.asm and src/disk/*. Shared source may also affect original banked integration. Reproduce before assuming palette/cache/staging failure. Native loader/runtime ownership is tight; do not write into immutable tables or introduce mapper writes.

## Evidence and reproduction

- Public compact receipts: references/compact-delivery/native.json (59 checks, 36 routes/replays) and publication.json. Native reproduction/qualification commands: docs/native-delivery.md. Its current measured worst NTSC busy time is 59,698 / 59,736 cycles, only 38 cycles margin; PAL 67,264 / 71,364. Fresh full-density checks are required for every renderer/font/ROM change.
- Before this handoff: 90 host tests, local synthetic CI, independent review and both remote PR #39 CI jobs pass. New default Make ROM and COM launch paths loaded real native programs (2,422/1,014 paced-loop observations). This is boot/run evidence, not complete new gameplay acceptance.
- Native ignored artifacts: outputs/disk/, final published assets outputs/disk/release/. Original-free CI mutates shared generated outputs/presentation; follow fixture-generation prerequisites documented in native-delivery.md before dense checks.
- Prior full acceptance roots: outputs/issue35/qualified-{dos,plain32}-video and qualified-{dos,plain32}-acceptance. Local private DOS1 test disk outputs/issue35/testenv/seaquest-dos1.dsk; SHA256 `5fb34d8c1664a60e4cc81c1a4f1a8585428dc2420f00bce9f74d85b0e38b928e`. Current COM is present there; a new candidate must be imported/verified. Custom machines seaquest_issue35_dos_pal / seaquest_issue35_dos_ntsc use 64K expanded-slot RAM and private firmware. BIOS/DOS files and replays must stay local.
- Full-state replay comparison uses scripts/native_replay_check.py. Generation safety and real loader immutability checks are in scripts/native_video.py. Build/package source binding in scripts/source_identity.py and package_native.py must remain honest: new binaries require new receipts, not reuse of old identities.
- Historical failure modes already fixed: stale generated absolute writer pointers; transient mapper writes to $7000 (flat RAM data); palette generation rebase during four-chunk token construction; shadowed state hash variable. Treat as investigation leads only, not current proven causes.
- Keep intentional pixel differences confined to this issue's approved presentation changes; never relax gameplay/state/audio/VRAM/timing checks generally. Validate whole palette/logo cycles, generation wrap/READY, PAL/NTSC dense scenes, game-over/restart and complete-game/rescue as appropriate on final native ROM/COM.
- Automated evidence, human emulator viewing/listening, owner approval and physical MSX tests must remain separate. Physical/human acceptance is not established by previous automated tests.

## Next actions

The approved runtime and release 1.0.1 are complete. The publication metadata PR records the verified delivery and closes issue #40; set the project item to Done after that merge. No runtime work remains. Do not reopen the frozen implementation or infer physical acceptance from owner approval.


## Local candidate delivered for owner testing

- Frozen runtime source: `a44811c68345d32041d0114c048276e169958430` on `codex/fix/40-hud-attract`.
  Later documentation commits do not alter the source fingerprint.
- ROM 32,768 bytes, SHA256 `5907ee7f9eb50df9ae356fee9bcb5ef931beb388d569a22aa9af043a7d97018a`.
- COM 25,599 bytes, SHA256 `a4f1e4330ceb6ad0dff7769d0c2805e22149241da6c3359b8cf2baa453a03d91`.
- Owner archive: `outputs/issue40/seaquest-issue40-5907ee7f.zip`; guide `outputs/issue40/candidate/LEIA-ME.md`.
  These binaries and captures stay local/ignored pending approval.
- Final evidence: 78 checks, 36 complete routes plus 36 independent replays,
  2,643,400 frames; NTSC worst 59,133/59,736,
  PAL 67,006/71,364 cycles, no skipped VDP frames/visible commits.
  91 host tests and synthetic CI pass. Shared banked diagnostic remains the
  exact 39,328-case benchmark binary `8bd402d131e233f0dbcc857cdfd4c3ad0807de6423d3cee17774f6cc8ec6154f`.
- Authoritative compact receipt: `references/compact-delivery/issue-40-candidate.json`.
  Full receipt: `outputs/issue40/candidate/qualification.json`.
- Actual fixes and reproducible commands: `docs/issue-40-candidate.md`.
  The measured baseline missed VBlank and performed 18-cycle active writes.
  The repair forecasts initial palettes, warms both font half-periods, fuses
  lower-background transfers and avoids a full HUD queue after an already
  prepared atlas swap. Oxygen/credit changes remain presentation-only.
- Owner human emulator viewing/listening/playtesting and physical MSX evidence
  remain pending. This does not change the existing release 1.0.0 or its prose.
- **No PR/draft, push, merge, tag or publication has been made. Keep issue #40
  open/In progress and wait for explicit approval of these exact binaries.**
  After approval: independent review, PR/checks/integration, then the requested
  release retaining `docs/releases/1.0.0.md`'s base narrative and appending fixes.
  Any runtime change must be requalified and its binary identity rechecked
  against the owner's tested candidate. Do not start another issue in this chat.

## Approval and release preparation — 2026-11-02

Owner message: “aprovada, pode seguir”. Approval and independent review records are `references/compact-delivery/issue-40-approval.json` and `issue-40-review.json`. Release 1.0.1 ships the exact approved hashes; the 1.0.0 assets and narrative source file remain unchanged. Integration/publication is in progress. No platform, duration or physical test evidence was supplied with approval.

## Published and verified — 2026-11-02

- Implementation PR #41 merged as `6df671816fba7b4afbfa57230b0fa435ed444c0d`.
  Both PR checks and the main-branch CI passed. Independent review found no blockers.
- Release: https://github.com/sandersouza/msxgp-seaquest/releases/tag/1.0.1 .
  Annotated tag `ba05f690bc3dc73e7c109228980e8f3f84066ce0` points to the merge.
- Five public assets were downloaded without authentication and byte/hash checked.
  ZIP integrity, member identity and inner/outer checksums passed. ROM/COM are
  exactly the approved 5907ee7f/a4f1e433 files; no rebuild or runtime edit occurred.
- The old 1.0.0 body and all eight assets remain unchanged. Its base prose is
  preserved in the new notes, with current native identities and appended fixes.
- Authoritative publication record: `references/compact-delivery/issue-40-publication.json`.
  Private download copies and verification helpers remain under `outputs/issue40/`.
- Owner approval is recorded; detailed test platform/duration and physical MSX
  evidence remain unspecified/unverified. Release authorization does not certify hardware.
- This final metadata integration completes issue #40. Keep the approved binary
  hashes as the release identity; any future runtime issue belongs in its own chat.
