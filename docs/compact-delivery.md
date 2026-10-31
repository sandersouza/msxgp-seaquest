# Disk and plain32 delivery investigation — issue #35

Status: **delivery remains open**. Neither an MSX-DOS executable nor a plain32
cartridge has passed acceptance. No experimental image is a release download.
The tested compact-enemy candidate is rejected for exceeding the frame budget.
This result does not establish that a redesigned port is impossible.

The production runtime is unchanged from `c987420`. Rebuilding its playable
128 KiB cartridge reproduces the existing 1.0.0 SHA256:
`41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8`.
Tag `1.0.0`, its original assets and existing WebMSX links remain intact.

## Storage and runtime are different constraints

The [storage receipt](../references/compact-delivery/storage.json) records
occupied extents, not a minimal live working set. Its 115,903-byte total includes
alignment, duplicated representations and startup-only data. Adding the current
`C000..F37F` RAM reservation yields 129,087 bytes of unchanged-layout accounting.
A redesigned loader can discard or overlay cold data; that number is not a
lower bound for all possible implementations.

| Current representation | Bytes |
| --- | ---: |
| Physical ASCII16 image | 131,072 |
| Whole-image host zlib level 9 | 40,925 |
| Whole-image host LZMA preset 6, XZ container | 28,632 |
| Prepared enemy transfers, 608 variants | 29,184 |
| Enemy bank-boundary padding | 16 |
| Existing exact source-row expansion cache | 8,192 |
| Palette records, 196 × 125 | 24,500 |
| Compiled HUD colour field programs | 10,545 |
| Palette forecast code/descriptors | 6,644 |
| HUD atlas after startup unpacking | 7,168 |

The XZ size is a host compression measurement. There is no corresponding Z80
decoder, decoder workspace, destination layout or measured executable in that
figure. Unpacking the entire current layout cannot fit physical 64 KiB RAM.
Changing mapper metadata or truncating banks does not address these constraints.

The current RAM contract is:

| Range, end exclusive | Ownership |
| --- | --- |
| `C000..C400` | Canonical state, input/contact mirrors and forecast shadows |
| `C400..C800` | Renderer/input/clock state, palette queues and colour state |
| `C800..CF00` | Name staging, palette lookup, SAT and scratch |
| `CF00..D000` | HUD pointers, signatures and presentation state |
| `D000..EC00` | Unpacked immutable HUD data |
| `EC00..F000` | HUD cache tags and current/next RGB pages |
| `F000..F380` | Stack reservation, including guard headroom |
| `F380..10000` | BIOS/system work area |

Unused bytes inside these reservations are not automatically contiguous free
RAM. Page0 normally exposes BIOS. Using underlying RAM requires an explicit
slot/BIOS-call contract, including expanded slots; it adds no physical RAM.

## Measured compact-enemy experiment

`src/experiments/compact_enemy.asm` substitutes the existing exact 8 KiB
source-row cache for prepared 48-byte transfers. It preserves the distinct
top/bottom SCREEN2 banks and display-off fast transfers. Scratch `CE80..CE81`
lies beyond the `CE00..CE7F` initialized SAT area.

The experiment conceptually removes 21,008 bytes of prepared enemy payload.
Its diagnostic image is still **131,072 bytes, ASCII16**: other obsolete bank
contents deliberately remain in place to isolate this hot path. It is neither
a measured smaller cartridge nor a DOS load path.

The baseline ran the existing original-6502, original-pixel and HUD oracle over
39,328 fixtures. The probe then replayed those identical fixtures and compared
canonical RAM, full final/prepared/primed VRAM, VDP registers and name pages.
Controlled fixtures include density, clipping, controls, oxygen and progression.
Receipts: [baseline](../references/compact-delivery/baseline.json) and
[rejected probe](../references/compact-delivery/enemy-cache.json).

| Gate | Existing renderer | Compact-enemy probe |
| --- | ---: | ---: |
| Compared fixtures | 39,328 | 39,328 |
| Canonical state and VRAM | pass | identical |
| Worst unpaced frame | 59,110 cycles | 61,243 cycles |
| Margin below 59,736 cycles | +626 | **−1,507** |
| Worst paced busy work | 58,782 cycles | **60,915 cycles** |
| Paced VDP frame increments | 1 | **1 or 2** |
| Longest paced period | 59,736 cycles | **119,464 cycles** |
| Minimum active-display VRAM spacing | 29 cycles | 29 cycles |
| Minimum touched stack address | `F370` | `F370` |

The paced probe repeats the worst fixture for 240 measured frames, after one
priming frame. It visibly misses the one-display-frame cadence even though its
RAM guards and transfer spacing pass. It is rejected; no lower frame rate or
reduced scene density is accepted as a workaround.

These are NTSC renderer/RAM/VDP measurements. They do not establish PSG event
equivalence, PAL timing, cold disk loading, complete games, rescues, manual
viewing/listening or physical hardware qualification for a new format. Those
gates must run against each eventual final binary and its actual loading path.

## MSX-DOS ownership

The [MSX Technical Handbook, chapter 3](https://konamiman.github.io/MSX2-Technical-Handbook/md/Chapter3.html)
specifies entry at `0100h`, the TPA ceiling through the word at `0006h`, and
resident system memory above that ceiling. The existing cartridge's fixed
`SP=F380h` and HUD data through `EFFFh` cannot simply be assumed safe under DOS.
An ordinary returning `.COM` must respect the actual TPA and preserve the kernel.
A takeover loader would need a documented reset/exit policy and explicit system,
stack and slot ownership after all required disk reads finish.

The [MSX-DOS programming environment specification](https://map.grauw.nl/resources/dos2_environment.php)
also documents page0 and inter-slot BIOS entry conventions. The cartridge's
direct BIOS calls, ROM frequency-byte read, page2 mapping and `$7000` writes need
real adaptation. DOS2 mapper support must not become a hidden requirement for
the unexpanded MSX1/DOS1 target.

## Remaining design work

Role factorization is a promising, independently checked storage alternative.
All 70 RGB run fields in every palette record reconstruct exactly from two
nibbles selected from its 24 role values, or zero. Retaining current class IDs
would use 4,704 role bytes plus 6,076 ID bytes, totalling 10,780 bytes before
descriptors and code. A simple explicit descriptor map adds 140 bytes. This
is an exact host reconstruction result, **not a validated Z80 implementation**.

Next work must:

1. Generate current/next RGB pages from role records in bounded prefetch work;
   measure synchronous transitions as well as steady state, retaining exact
   generation-token semantics and the existing fast commit writers.
2. Reduce duplication between field programs and forecast descriptors, and
   separate startup-only sprite/HUD sources from the live runtime working set.
3. Produce a complete shared 64 KiB DOS layout and plain32 storage/slot map,
   including loader, decoder, stack and BIOS/DOS ownership. Re-budget CPU work
   before promoting a compact enemy implementation.
4. Implement and qualify both real load paths, then run PAL/NTSC full-game,
   restart, rescue, state/pixel/PSG, density and memory gates. Publish distinct
   assets/manifests/checksums only after independent review and all delivery gates.

## Reproduction

Use the existing local reference inputs and project environment. Original ROMs,
BIOS, generated cartridges and research replay bundles remain local/ignored.
Run these serially; the renderer generators share output paths.

```sh
cd /Users/sandersouza/Developer/msx-gamePorts/seaquest
.venv/bin/python -B scripts/video_check.py --build-only
.venv/bin/python -B scripts/compact_audit.py
.venv/bin/python -B scripts/compact_probe.py
```

The first command reproduces the original playable and symbols. The second
writes `outputs/issue35/audit.json`. The third runs the full baseline oracle,
builds/replays the diagnostic, compares state/images/VDP and measures pacing.
It intentionally returns **exit status 1** with a `rejected_timing_or_io` receipt
under `outputs/issue35/probe/result.json` for this rejected candidate. Earlier
build/oracle/comparison failures are errors, not a timing verdict.
