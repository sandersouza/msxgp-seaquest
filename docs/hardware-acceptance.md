# Seaquest issue #15 acceptance candidate

This is a **test candidate**, not a physically accepted release. The package stays
local under `outputs/acceptance/`; original-derived cartridges and replay snapshots
must not be uploaded to GitHub without the owner's authorization. Automated results
are indexed by `references/acceptance/verification.md`. Use
[acceptance-observations.md](acceptance-observations.md) for manual observations.

## Identify the cartridge

- `seaquest.rom`: **131,072 bytes**, **ASCII16 mapper**.
- ROM SHA256: `41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
- Matching `seaquest.sym` SHA256:
  `b8678e849d6169e8efb9e0626c243ef6d5fc8b6f402f24952c595c82f93651c9`.
- Runtime base: `19940e8fb08ac8269990725b88a70e8c56156e16` (PR #31).
- Target: standard MSX1, **64 KiB RAM / 16 KiB VRAM**, standard-speed Z80,
  TMS9918-family VDP and standard PSG; no expansions or turbo required.
- Original Atari 2600 NTSC4K SHA256:
  `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
  MSX score digits and complete OXYGEN lettering are approved adaptations.

`make build` produces the separate 32 KiB diagnostic. Do not substitute it for this
candidate. The ZIP contains ROM, symbols, instructions, reports and device replays.

## Reproduce automated evidence

From the repository root, with the established environment and local original inputs:

```sh
make environment-check
make reference-check
shasum -a 256 outputs/video/seaquest-issue14-final.rom
shasum -a 256 outputs/video/seaquest-issue14-final.sym
make acceptance-check
.venv/bin/python -B scripts/acceptance_replay.py
make test
bash scripts/ci.sh
```

If the ignored frozen files are absent in a fresh checkout, reproduce them from
the documented local originals without substituting the generic diagnostic:

```sh
make video-build
shasum -a 256 outputs/video/seaquest-video.rom outputs/video/seaquest-video.sym
.venv/bin/python -B scripts/full_game_check.py --rom outputs/video/seaquest-video.rom
.venv/bin/python -B scripts/acceptance_replay.py --rom outputs/video/seaquest-video.rom
.venv/bin/python -B scripts/acceptance_report.py --rom outputs/video/seaquest-video.rom
.venv/bin/python -B scripts/acceptance_package.py --rom outputs/video/seaquest-video.rom
```

The two hashes must equal the candidate identities above; stop on a mismatch.

The serial matrix uses private headless processes. Both selections × four difficulty
combinations × NTSC/PAL must complete natural game over and restart. Two rescue
routes cover pickup, partial rescue, alarm and oxygen death. Every source update,
sampled graphics, ordered PSG stores, timing, clock windows, stack and RAM guards
are checked. No game RAM is seeded in the cold routes. The feedback controller uses
keyboard devices and records OMR events. This is automated play, not a human test.

The identical cartridge's controlled boundary/density/generation/phase evidence is
retained under `references/video/`. To rebuild/audit that baseline serially, use
`make video-check`; compare `outputs/video/seaquest-video.rom/.sym` hashes to the
frozen candidate before substituting files. Runtime changes require new timing
evidence. After the delivery commit exists, build the local acceptance ZIP once:

```sh
.venv/bin/python -B scripts/acceptance_package.py
cat outputs/acceptance/package.json
```

The packager checks all 18 route identities, ROM/symbol/replay hashes, baseline
identity and ZIP contents. It refuses to overwrite an existing ZIP. The manifest
lists each member's hash. Original inputs remain local research prerequisites.

## Manual emulator acceptance

Extract the ZIP into a separate empty directory. From that directory:

```sh
shasum -a 256 seaquest.rom seaquest.sym
openmsx -machine C-BIOS_MSX1 -cart seaquest.rom -romtype ASCII16
```

Use normal speed with sound enabled. Close only this new process when finished,
then repeat PAL:

```sh
openmsx -machine C-BIOS_MSX1_EU -cart seaquest.rom -romtype ASCII16
```

Record the observed machine/settings. Do not use turbo or a VDP override. In a new
private instance, a representative OMR can be loaded from the openMSX console with
`reverse loadreplay -goto begin -viewonly PATH`. Snapshots include machine settings;
packaged cartridge paths are relative to `seaquest.rom`. Start openMSX from the
extracted package root when loading its replays. The packager also checks every
replay against the extracted cartridge before producing the ZIP.

| Control | Action |
|---|---|
| Cursor keys / Space | Active player movement / held fire |
| Joystick 1 / button 1 | Player 1 movement / held fire |
| Joystick 2 / button 1 | Player 2 movement / held fire |
| F1 held | Reset/start |
| F2 held | Select one/two players, with original held repeat |
| F3 press / F4 press | Toggle player 1 / player 2 difficulty B/A |

Switches start B/B and persist over Reset/Select. Matrix values are 0=B/B,
64=A/B, 128=B/A, 192=A/A. Cold boot for a known B/B condition.

1. Play from initial refill through movement, held fire and collisions. Read all
   score digits and OXYGEN; inspect water/border, actors, life/rescue icons, oxygen
   edge and dense overlaps for corruption, disappearance or unexpected flicker.
2. Pick up divers, surface with a partial load and refill; then attempt all six.
   Record events actually seen. Stay submerged for alarm and oxygen death/refill.
3. Complete one-player exhaustion to game over, wait in attract and restart.
   Complete two-player exhaustion, checking alternating turns and separate stocks
   and scores. Test each joystick port independently.
4. Try all four switch combinations, held fire, reversal, diagonals, Select repeat,
   Reset and switch persistence.
5. Listen to shots, impacts, rescue/bonus and oxygen alarm; compare event order and
   perceived behavior to the original where available. PSG timbre and oscillator
   phase are approximations; register checks do not prove subjective acceptance.
6. Repeat representative full games on PAL and NTSC. Observe responsiveness and
   stutter. PAL extra updates preserve source speed; input/presentation phase differs.

A boot, screenshot or passing replay cannot replace completed manual games.

## Physical machine acceptance

1. Record real MSX model, RAM, VRAM, VDP/video standard, PSG, display and joysticks.
   Record flash/cartridge model, firmware and loader. Use its documented **ASCII16
   128 KiB** configuration. No specific flash device is physically qualified here.
2. Verify ROM hash/size before transfer and compare readback/checksum if supported.
   Follow device instructions. Do not silently pad, patch or change the mapper.
3. Power off before inserting/removing a physical cartridge. Cold boot at standard
   speed; run the manual sequence above, including game over/restart and both ports.
4. Run at least **20 minutes** of real play with repeated resets, selections,
   rescues and dense encounters. This is a requested soak, not an observed result.
5. Test available PAL/NTSC machines independently. Mark unavailable cases pending.
   An expanded machine alone does not establish the 64 KiB hardware target.
6. On any hang, reset, corruption, control, audio or pacing fault, record the hash,
   scene, steps and setup. Keep photos/video local unless publication is authorized.

Physical acceptance stays **pending** until actual machine observations exist.
Manual emulator viewing/listening is a separate record.
