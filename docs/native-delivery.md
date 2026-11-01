# Native MSX1 disk and plain 32 KiB delivery

Both alternatives run the complete game on an ordinary **64 KiB RAM / 16 KiB
VRAM MSX1**, with a standard-speed Z80, TMS9918-family VDP and PSG. Compression
is used only during startup. Gameplay does not require a RAM mapper, turbo,
extra sound hardware or a cartridge bank-switching mapper.

## Playing from MSX-DOS

1. Boot your MSX1 with your normal **MSX-DOS 1** system disk and disk interface.
2. Copy `SEAQUEST.COM` to that disk. Keep its eight-character filename.
3. At the `A>` prompt, type `SEAQUEST` and press Return.
4. Use the same keyboard/joystick controls as the cartridge. F1 resets the game.
5. Use the **machine's reset button or power cycle** to leave the program.

The executable takes over the original 64 KiB after DOS finishes loading it.
It does not return to the DOS prompt, and does not access or write the disk
during play. It checks available DOS program space and a payload checksum before
taking over; failures print a message and return to DOS. The archive contains
no MSX-DOS system files, BIOS or bootable system disk. Supply your own system
disk. DOS2/Nextor and MSX2-specific environments are outside this qualification.

## Playing the small cartridge

`SEAQUEST32.ROM` is a complete **32,768-byte ordinary cartridge**, mapped at
`4000..BFFF`. Select **Normal**, not ASCII16 or Konami, in openMSX:

```sh
openmsx -machine C-BIOS_MSX1 -cart SEAQUEST32.ROM -romtype Normal
openmsx -machine C-BIOS_MSX1_EU -cart SEAQUEST32.ROM -romtype Normal
```

Use normal emulator speed. The loader expands the game into the same original
64 KiB RAM as the disk executable. A cartridge programmer/flash cartridge must
support an ordinary 32 KiB image. Physical cartridge programming and hardware
qualification remain separate from the emulator tests.

The original `seaquest.rom` download remains the accepted 128 KiB ASCII16
version, with its original hash and WebMSX link. The new alternatives have
different filenames and their own source/manifest/checksum identities; they do
not replace or retag the old artifact.

## Reproducing the binaries

After the existing [development setup](development.md), supply the documented
original inputs locally and run these commands in order:

```sh
make environment-check
.venv/bin/python -m pip install -r requirements-reference.txt
make reference-check
make disk-build
shasum -a 256 outputs/disk/SEAQUEST.COM outputs/disk/SEAQUEST32.ROM
cat outputs/disk/manifest.json
```

`make plain32-build` is an alias for the same shared build. Both targets emit
`outputs/disk/flat.bin`, runtime symbols, loader symbols and a manifest. All
reference-derived data and binaries remain ignored. The first disk build
fetches the public BSD-licensed ZX0 compressor at pinned commit
`ecde3a2ae05061fe06469ed46df81a33b7de7d86` and compiles it with the local C
compiler. Its backwards Z80 decoder and redistribution notice are versioned
under `src/third_party/zx0/`.

## Runtime and loading contract

| Address range | Ownership after startup |
| --- | --- |
| `0100..BF58` | Native code, compact graphics/palettes, writers and forecasts |
| `C000..CFFF` | Canonical source state and bounded platform workspace |
| `D000..EBFF` | Immutable HUD data |
| `EC00..EFFF` | Physical presentation caches |
| `F000..F2DB` | Cold initialization code |
| `F2DC..F2FF` | Guard before the stack |
| `F300..F37F` | Discarded bootstrap and runtime stack reserve |
| `F380..F3FF` | Video mirrors and bootstrap scratch; no resident DOS/BIOS use |
| `F400..FFF3` | Immutable compact palette records |
| `FFF4..FFFF` | Unused by the game; secondary-slot register is preserved |

The DOS loader reads the BIOS frequency identifier through `RDSLT` before
destroying DOS state. It retains the RAM slot/subslot selections established by
DOS. The cartridge obtains the actual page3 RAM slot, preserves its secondary
identity, maps that RAM into the lower pages and checks for absent/aliased RAM.
Neither loader writes palette data to `FFFF`.

Both loaders explicitly upload the 1,504-byte resident sprite atlas to VRAM
`3800..3DDF`. They stage the low executable bytes temporarily in other VRAM,
expand the high palette block separately, and run the backwards main decoder
from the stack reserve. The 1,024-byte in-place margin exceeds ZX0's measured
three-byte delta. The runtime then initializes its own VDP/PPI/PSG access;
interrupts remain disabled and display pacing polls VBlank.

The compact renderer retains exact per-class color equality. Its palette record
is 17 bytes, rather than storing repeated RGB runs; its enemy source expansion
cache is 8 KiB. Visible enemy patterns are transferred during the paced VBlank
commit. Current HUD fields share the same exact descriptors as forecast fields.
The final link verifies every generated numeric writer address against the
assembled symbols and rejects any remaining mapper access in its include tree.

## Reproducing qualification

For a cartridge, use the exact built binary and its matching runtime symbols:

```sh
.venv/bin/python -B scripts/video_check.py --delivery plain32 --rom outputs/disk/SEAQUEST32.ROM --machine C-BIOS_MSX1 --scenario dense --quick
.venv/bin/python -B scripts/video_check.py --delivery plain32 --rom outputs/disk/SEAQUEST32.ROM --machine C-BIOS_MSX1 --generation wrap
.venv/bin/python -B scripts/video_check.py --delivery plain32 --rom outputs/disk/SEAQUEST32.ROM --machine C-BIOS_MSX1_EU --generation wrap
.venv/bin/python -B scripts/full_game_check.py --delivery plain32 --rom outputs/disk/SEAQUEST32.ROM --output-root outputs/native-acceptance/plain32
.venv/bin/python -B scripts/native_replay_check.py outputs/native-acceptance/plain32
```

For disk qualification, prepare a **private** bootable DOS1 image containing
the exact `SEAQUEST.COM` plus `AUTOEXEC.BAT` containing `SEAQUEST`. Supply a
64 KiB MSX1 disk-machine configuration and select its actual PAL/NTSC region:

```sh
.venv/bin/python -B scripts/video_check.py --delivery dos --rom outputs/disk/SEAQUEST.COM --disk /path/to/private-test.dsk --machine YOUR_MSX1 --region pal --scenario dense --quick
.venv/bin/python -B scripts/full_game_check.py --delivery dos --rom outputs/disk/SEAQUEST.COM --disk /path/to/private-test.dsk --ntsc-machine YOUR_NTSC_MSX1 --pal-machine YOUR_PAL_MSX1 --output-root outputs/native-acceptance/dos
.venv/bin/python -B scripts/native_replay_check.py outputs/native-acceptance/dos
```

The harness checks the file inside the disk's FAT12 chain against the supplied
COM, boots from that disk without a cartridge, and compares every immutable
loaded segment and the resident atlas with the independent build. Write
watchpoints reject even transient writes to immutable runtime data. Natural
routes use device controls, with no canonical RAM reloads after boot. Independent
OMR playback loads no feedback controller and compares final canonical state,
pixels and PSG state. Cold device-playback tests additionally exercise keyboard
and both standard joystick ports.

The disk fixture uses the real DOS1 system files distributed in Konamiman's
Nextor 2.1.0 tools disk with zerobas/C-BIOS system firmware and a WD2793 disk
interface, 64 KiB physical RAM in an expanded slot and 16 KiB VRAM. NTSC and PAL
fixtures differ only in the VDP and documented BIOS frequency flag. System
firmware, DOS files, private images and OMR snapshots are not release assets.

Automated original-state/pixel/PSG equivalence and emulator timing are distinct
from subjective listening, human playtesting and physical-machine evidence.
Those manual/physical observations remain pending, as for the original release.
