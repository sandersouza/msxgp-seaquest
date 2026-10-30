# Reference inventory — issue #1

Target: unexpanded MSX1, **64 KiB RAM / 16 KiB VRAM**. Original inputs are
local research material and excluded from Git. This repository's license does not
establish redistribution permission for supplied third-party ROMs or source.

## Reproduce

```sh
python3 -B scripts/reference_inventory.py
python3 -B -m unittest discover -s tests -v
stella -rominfo references/roms/seaquest-atari2600.a26
```

`references/manifest.json` records byte sizes, SHA-256/MD5 hashes and structural
metadata. The checker only reads inputs; `--describe` prints current metadata and
does not update the approved manifest. Missing or changed inputs fail the check.
Original files must be supplied locally at the manifest paths after a fresh clone.
Synthetic tests work without these originals.

## Atari 2600 authority

- Input: `references/roms/seaquest-atari2600.a26`, 4096 bytes.
- MD5: `240bfbac5163af4df5ae713985386f92`.
- SHA-256: `fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43`.
- Stella's [property database](https://github.com/stella-emu/stella/blob/289a40f1b63022b8bbe5b722061c660009d5de2c/src/emucore/stella.pro#L3354)
  matches this MD5 to Seaquest (1983), Activision / Steve Cartwright, model AX-022.
- The [MiSTer Atari 2600 core catalogue](https://github.com/MiSTer-devel/Atari2600_MiSTer)
  explicitly identifies the same hash as NTSC. Stella 7.0c (`brew` 7.0c_1) reports
  `Display Format: NTSC*`, `Bankswitch Type: 4K* (4K)` and two joystick ports.
  Asterisk annotations are retained rather than presented as an explicit database override.
- Reset vector is `$F000`; raw vector words at offsets `$FFA/$FFC/$FFE` are
  `$EA02/$F000/$FD00`. Raw words do not imply that all vectors are exercised by
  the Atari 2600 hardware.
- Behavioral baseline: this exact 4K NTSC hash. A separately named commercial
  revision or dump lineage is **unknown**, not inferred from the local filename.
- Actual scanline count, cadence, startup RAM/seed and gameplay behavior are
  **not measured by this inventory**. Reference traces in #6 must measure them;
  do not silently substitute an exact 60 Hz clock for the measured source cadence.

## Atari 800 secondary reference

- Input: `references/roms/seaquest-atari800.xex`, 4393 bytes.
- MD5: `8323cfbc15d5d2f2b5110ae8ec283496`.
- SHA-256: `e97cee62f9a99003d78df122eacdd99a24d8e14bd3d0e7d6a497275e4aed86a1`.
- Parsed load segments: `$2000–$2DA0` (3489 bytes), `$2E00–$2F81` (386),
  `$3000–$31F1` (498), `$02E0–$02E1` (2). RUNAD is `$20C0`.
- The XEX container does not identify its author, region, revision or provenance.
  Those remain **unverified**, as does source-to-XEX reproduction (owned by #2).
- Supplied source: `references/dissasm/seaquest-atari800.s`, 48182 bytes, with
  SHA-256 `73769a9681c1ea4ed5e1d9d34b78f68fd2213b08d023ef774af158f0c9299a89`.
  Its header records a DiStella v3.0 disassembly dated June 8, 2012, and it contains
  Atari 800 hardware adaptations/macros. That header alone does not establish
  the adapter's identity, complete provenance or equivalence to the 2600.

## Baseline switch and mode policy

The [original Activision manual](https://atariage.com/manual_html_page.php?SoftwareLabelID=424)
instructs starting with both difficulty switches at B (fast continuous fire); A
selects slower continuous fire. Game 1 is solo; game 2 alternates two players.
Reset starts at the surface and action begins on diving.

For the first deterministic reference scenario, explicitly set **NTSC, joystick,
both difficulty switches B, color mode, game 1, then reset**. Record the seed/RAM
initialization policy in the capture harness instead of relying on emulator/user
defaults. Test both difficulty settings and both player modes later. Color mode is
our explicit capture setting; the manual does not establish it as a required default.

## Evidence and remaining work

On 2026-10-30, Python 3.14.7 verified all three unchanged inputs and six synthetic
tests passed. Stella 7.0c's noninteractive ROM identification was executed; no
gameplay or physical hardware acceptance is claimed. Stella source metadata was
read at commit `289a40f1b63022b8bbe5b722061c660009d5de2c`; the complete property
file SHA-256 was `647b18305a8fcc7a370195da1b3599a62d56e9588f386b71083a56740560cc4a`.

#2 owns disassembly, code/data distinction and Atari 800 source correspondence;
#3 owns rules derived from code; #4 owns a reproducible full development setup;
#6 owns measured, aligned reference traces. Unknown provenance and timing are
explicit open research items, not assertions that block inventory acceptance.
