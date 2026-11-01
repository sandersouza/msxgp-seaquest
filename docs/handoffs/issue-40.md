# Issue #40 — oxygen color, attract credits and cycling HUD repair

Issue: https://github.com/sandersouza/msxgp-seaquest/issues/40
Dedicated chat: `ISSUE #40` in Seaquest project `745758fe-48e5-471b-950b-4a2cee9dea9a`.

## Owner request and authorization gate

Implement in this new issue/chat: filled oxygen bar yellow like the player's submarine, with depleted/empty rendering unchanged; add exact `retrowork 2026` to the lower Activision logo/text cycle outside active gameplay; reproduce and repair lower HUD corruption during non-gameplay color cycling. No cause has been assumed or measured yet.

**Deliver the local ROM/COM candidate for owner testing, then wait for explicit owner approval. Do not create any PR (even draft), merge, tag or publish until that approval.** After approval, perform independent review/PR/merge and publish a new release retaining the base release text and appending these fixes. This explicit user gate overrides earlier autonomous release practices. Keep the issue open while approval/delivery is pending.

## Exclusive checkout transfer

- Repository: `/Users/sandersouza/Developer/msx-gamePorts/seaquest`.
- Current branch: `main`, commit `e315927ff846e9b019c1a68467523e35119decd8` (merged PR #39).
- Existing tracked checkout was clean. Pending files from issue setup: `.github/issues/hud-oxygen-attract-credits-corruption.md` and this handoff, both untracked. Preserve/commit them on a new scoped branch such as `codex/fix/40-hud-attract`.
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

Take exclusive checkout ownership, create the scoped branch, commit setup docs, reproduce/capture baseline attract corruption, implement the three changes, validate and prepare candidate ROM/COM plus concise before/after previews and exact reproducible commands. Deliver to the owner in ISSUE #40 and wait for the required approval before creating a PR or publishing anything. Do not ask for initial architecture/permission already authorized by this handoff.
