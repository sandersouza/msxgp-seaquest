# Reproducible reference disassembly — issue #2

## Result

Both complete rebuilt inputs match the originals **byte for byte**, including all
Atari 800 XEX load headers and RUNAD. Rebuilding the supplied source with MADS
therefore establishes its correspondence to the supplied executable. It does not
prove that the Atari 800 hardware adaptation is behaviorally identical to the 2600.

```sh
python3 -B scripts/reference_rebuild.py
python3 -B -m unittest discover -s tests -v
```

The runner verifies the immutable input manifest before invoking tools. It emits
the generated 2600 source, DASM listing/symbols, rebuilt binaries, MADS
listing/symbols and address-only report under ignored `outputs/reference/`.
`references/rebuild-report.json` is the checked-in evidence snapshot; it contains
addresses, classifications and hashes, not ROM bytes. Original inputs remain local.

Verified SHA-256 values:

| Target | Bytes | Rebuilt SHA-256 |
|---|---:|---|
| Atari 2600 | 4096 | fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43 |
| Atari 800 XEX | 4393 | e97cee62f9a99003d78df122eacdd99a24d8e14bd3d0e7d6a497275e4aed86a1 |

## Tools and regeneration

`references/tools-lock.json` identifies the exact tested upstream revisions:
[DiStella](https://github.com/johnkharvey/distella/tree/1015ae53b2d222320eb706c220186305fcac55dd),
[MADS](https://github.com/tebe6502/Mad-Assembler/tree/ecc27e941c41d41dedce64de98162101fbef8261)
and the installed DASM formula/banner. DiStella is built with `make auto` into
`.tools/distella/distella`; the pinned MADS macOS ARM binary is `.tools/mads`.
DASM is on PATH. Flags `--distella`, `--mads`, `--dasm` allow explicit tool paths.
The repeatable setup command is owned by #4, not supplied by this research step.

DiStella command is `distella -paf references/roms/seaquest-atari2600.a26`.
Do **not** add `-r`: its mirrored-address relocation can change original bytes.
DiStella's upstream filename buffer is only 50 bytes; the runner passes a short
repository-relative input path from an explicit working directory. Absolute paths
to the local tool and repository can be long without overflowing that filename.

The generated listing's timestamp is not deterministic; the rebuilt ROM/XEX bytes,
hashes and address metadata are. Successful reassembly proves byte preservation,
not that every generated code/data classification is semantically correct.

## Code/data and entry points

The report covers `$F000–$FFFF` without gaps. Its `code`/`data` ranges are
**DiStella's automatic reachability classification**, exported through DASM's
listing. They are an initial map for analysis and can require correction for
indirect control flow or embedded tables. They are not a verified execution trace.

The report maps 196 preserved `LFxxx` labels between the original listing and
the assembled 800 program. A shared label documents a source correspondence,
not a claim that the blocks contain identical code or hardware semantics.

| Role / source label | 2600 address | Atari 800 address |
|---|---|---|
| Entry | `$F000` (START) | `$20C0` (_MAIN / RUNAD) |
| Main display preparation LF00E | `$F00E` | `$2235` |
| Lane processing LF219 | `$F219` | `$2486` |
| Enemy scanline graphics LF34F | `$F34F` | `$2510` |
| Frame counter increment LF689 | `$F689` | `$271D` |
| Console/color processing LF6A7 | `$F6A7` | `$2728` |
| Reset LFB54 / LFB56 | `$FB54` / `$FB56` | `$2BCF` / `$2BD1` |
| PRNG LFEDB | `$FEDB` | `$2CA0` |
| Score helper LFFDA | `$FFDA` | `$2CDB` |

Important table families in the original listing: `$FC18` and following
positioning data; `$FCE6/$FCF0` palette/lane data; `$FCFB–$FEBA`
graphic/table region; `$FEEB` repeat masks and later animation/color
tables; `$FFAD` signed missile movement offsets. Exact generated ranges are in
the report; semantic table boundaries remain subject to #3's rule analysis.

## RAM map used by the port

These addresses are preserved in the supplied source and can be followed in the
2600 listing. Treat pointers/temporary aliases as phase-dependent:

| RAM | Role |
|---|---|
| `$80/$81/$82` | game selection / frame counter / PRNG state |
| `$85–$91` | attract/color state |
| `$92–$9D` | score-digit temporary pointers, aliased with graphics pointers |
| `$9E–$A1`, `$A4–$AB` | lane positions and repeated/visible enemy flags |
| `$B4/$B5/$B6` | collision/rescue lane results |
| `$B7`, `$B8–$BA`, `$BB` | active player, BCD score, reserve lives |
| `$BD/$BE` | wave and rescued-diver count |
| `$BF–$C5` | saved other-player state (exact field semantics in #3) |
| `$C6`, `$C7–$CA` | player X and lane diver/enemy-shot X |
| `$D6/$D7`, `$D9–$DC` | player/projectile facing and lane enemy flags |
| `$E0/$E1`, `$E6/$E7/$E8` | player animation/Y, oxygen, missile X, refill/bonus flags |
| `$F6/$F8` | patrol position and collision snapshot |

## Atari 800 adaptations that must not be copied blindly

- Display: TIA raster timing/register writes become ANTIC/GTIA playfield and
  player/missile graphics. Repeated lane enemies are drawn through a horizontally
  scrolled quick framebuffer at `$20–$5F`, with player/missile buffers at
  `$3300–$3700` and HUD buffers at `$3800/$3900`.
- Collision: TIA collision latches are replaced by GTIA player/playfield/missile
  reads; LF219–LF3B3 also clears and reads adapted latches. These are explicit
  fidelity audit points, not interchangeable with MSX sprite collision flags.
- Self-modification: ENEMY_WRITE_2/3 at `$2514/$2516` patch store operands.
  An MSX ROM backend needs a different implementation, not direct copying.
- Input: START/SELECT map to virtual reset/select; OPTION toggles both difficulty
  bits together. Joystick trigger reads use GTIA; virtual SWCHB initializes to
  `$3F`. This adaptation cannot establish independent original switch behavior.
- Audio: TIA control/frequency/volume values become RAM shadow registers and POKEY
  tables, updated by startvbl/updateAudio. Frequencies and event phase are adapted.
- Clock: VCOUNT/WSYNC waits and display-list timing replace TIA/RIOT framing.
  Startup waits for VCOUNT 124. Region, cadence and runtime alignment still require
  measurement; no timing equivalence follows from successful assembly.
- Core arithmetic: both CPUs are 6502-family, but the target is Z80. Preserve
  carry/overflow/BCD behavior and instruction/event ordering when deriving #3's
  contract, especially score helpers, movement and the PRNG.

## Validation boundary

Nine synthetic inspector/rebuild tests and both real-input byte comparisons passed
on macOS ARM with Python 3.14.7. Original inputs still match their initial manifest.
No Atari 800 runtime session, full game comparison or MSX gameplay validation has
been performed here. #3 proceeds from verified original addresses; #6 must settle
runtime capture alignment rather than assuming the 800 conversion is an oracle.
