# Issue13 delivery checkpoint

Dedicated ISSUE13 chat, sole implementer. Branch
`codex/feat/13-original-hud-psg`, base main9a08956. PR29 initially pushed7abb28f
was held draft because real attract transitions exceeded123,000cycles. That
implementation is superseded by the final128KiB backend below.

## Current acceptance

- Timed cartridge131072bytesASCII16:
  0942a040aa4bc4cb72df7db39445c2f96f237719bf8e63d1ed962ca13eca0910.
- Cold controls/playtest131072bytesASCII16:
  f6b8e010db183e31f76533763fd195c452dc7933aff9c0ff51bb0b2a51b169c3.
- `make presentation-check` completed successfully on these final artifacts.
  Full39328source/native/pixel cases,240paced frames, focused1129,
  three183-chain attract modes(total111264source updates/10980RGBframes),
  audio7982ticks/34692stores and cold6422updates/15807stores allpass.
- Normalmax59110cycles(626free); continuousattractmax59583(153free), maxcommit10324;
  zero skipped/visible commits. Native2963/input5660/collision40748/oxygen24605/
  progression55243 regressions and48host tests pass. Original-free localCI passes
  (systemPython skips one optionalpy65check). ExactJSONs and settings are in
  references/presentation/verification.md. Do not relabel these as PAL/physical/
  full-game release acceptance; #14/#15 retain those gates.
- Read-only reviewer found/fixed pattern63 oxygen-border collision, wrong
  palette_player_memo player selection, stale-slot mapping ownership, C296RAM
  overlap and READY1pending-token epoch hazard. Final focused review reports
  no remaining material correctness issue. Four new native folds each passed
  16384independent originalCPU cases with ordered stores/finalA/X/Y/carry.
- Delivery pending at this checkpoint: stage/commit/push, immutable-head review,
  remoteCI, PRready/merge, issue13closed/Done and dependency-ready ISSUE14 chat.
  Do not start issue14 implementation in this chat; use docs/handoffs/issue-14.md.

## Binding implementation invariants

- StandardMSX1Z80,64KiBRAM/16KiBVRAM, noexpansions. Atari2600 NTSC4K authority;
  Atari800 disassembly addresses can differ. Mandatory192enemy-pattern and352
  display/name bytes/frame, allsource actors/updates retained. No runtime6502.
- Fixedbank0 mapper helpers; native core/source and constant writers runbank1.
  Temporary mappings restore1. All bank assertions/exact131072-byte host check
  pass. Fixedbankpadding117; source-data gap0before9B00(windowtablesat9900/9A00). Use current symbols.
- Compact138-byte palette records expand303logicalbytes in bounded prefetch.
  Seven enemy slots: private0 plus6global foreground-only slots. Never prewarm0;
  validate mappingownership before invalidation/protection. Water usescolour0/R7,
  black1opaque; externalMSXborder follows water. Source86/92 versus90contrastfixed.
-47resident +16scratch patterns reservepattern63foroxygenedge3FE0/SAT252.
  Surface-player y13 images take priority; colder explosion10/clipped images use
  inactive scratch. Hidden sprites skip patterns whileall8actorSAT slotsremain.
- Runtime token1 permanently means classdefault; fresh2..240serials neverreuse
  canceled generations. Rebase clears512actual tags, patchescurrentmemos and
  invalidatesfont/forecastidentities. **Earlyrebase onlywhenPAL_READY=0**; READY1
  pendingIDs stayintheirepoch untilactivation/cancel. Translate guard retained.
- Boot HUD_ALL_CURRENT1 is downgraded onlyafter palette_stamp_default_memos
  snapshots8HUD_PTRS+2backgroundptrs and exactdefaultsignatures beforehiddenfont
  writes. Source paletteactivations clearflag. Obsolete markerdrain is removed.
- Forecast sourceRAMread-only, copies32tags/update fromD0 then<=2spans/update
  fromE0; validate snapshots/modulo255A3/16pointers/current+nextUID/counter before
  apply. Oppositefont prewarm2tiles/update and sourceUID/visibleblankchecks remain.
- OnlypacedVBlank usesuniformOUT12/OUTI18, flagclearedaftercommit; activeaccess29.
  General fastcopy1..64bytesonlyafterphysicalR1off, slowdispatchbeforeR1on.
  Sourceblackout requires86/E9/F6/AC0..3zero; noextrablackframe. TIDataManual2.1.5
  p13 and openMSX slot model support4.3ms no-waitwindow; maxcommitfitsit.
- ImmutableHUDD000..EBFF, tagsEC00/ED00, RGBEE00/EF00 endF000; defaultRGBC700.
  Keep source251bytes +hardwareC280/282/284/C296 andRPC C6F0. Forecastbuffers
  C100/C300/C200..27F/C2A0..FF areplatformowned; do not restore1024sourcebytes.
  QueueC510 max81×2+terminator<C600; staticIDsC600/C680, rolesC6B0,stateC6D0..EF.
  DispatchC4C4..C6/C6EB..ED; serialC6EA; displayOffC6EE; blackoutC6EF.

## Owner session and local artifacts

- Original outputs/seaquest-issue13-test.rom SHA3cf7b27000519b3f78cfa84195d8eb131a3dc3a8b2ee7c9b71b218b4e5ddf7b5
  and contrast-test65ed673c5dd28a71c0e010cd19e6a62576a50382912323ae631635b0e21bb3bf
  are unchanged. Neither was replaced.
- After verifying the old openMSX process wasclosed, opened the corrected copy
  outputs/seaquest-issue13-colors-fixed.rom (matchingf6b8...), manifest+symbols
  besideit. GUI confirmed sourceHUD/submarine/water running. Current owner session
  is execsession6851; do not stop/reload it or overwrite its named cartridge.
- outputs/presentation/seaquest-final-bench.rom/.sym preserve matching0942before
  syntheticCI overwritesoutputs/render. The historical audio64.rom/.sym names
  also hold128K snapshots; do not infer64K fromtheirfilename.
- All original ROMs/assets/generatedtables/playablecartridges/rawframes remain
  local/ignored. Public conciseJSONs contain metrics/hashes only. Builders share
  outputs; rerun targetsserially. `make presentation-check` includes natural
  prerequisite and all3attract modes; watchdogscalesfor384-tickchains. Forced
  modes onlyadvance serial, neverrollitback across persistentchain caches.
