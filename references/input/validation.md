# Issue #9 validation ledger

Date: 2026-10-30. Target: C-BIOS_MSX1/openMSX21.0, standard Z80,
64 KiB RAM/16 KiB VRAM, NTSC. No expansions. Local Python3.14.7;
public CI targets Python3.12. Pinned assembler revision:
`d379eeac9ad3857fb48fd3a3929175d0a56038ce`.

- `make native-contract`:2,707 cases pass against independent original6502.
- `make input-natural`:5,660 actual-device cases pass, including four300-tick
  held-fire chains and one300-tick console/switch chain;659 uninterrupted
  cold-boot updates pass. Hardware mirrors are poisoned in full fixtures.
  Registers, sample phase, IFF1/2, VDP IRQ and PSG15 checks pass.
- `make render-input-bench`:9,598 native/state/pixel/palette/transaction cases
  pass; maximum59,369 cycles,367-cycle margin;240 paced frames without skips.
  Minimum VRAM spacing29 cycles; maximum commit11,529; stack minimumF370,
  intact RAM guard. Padding1,792 bytes in the32 KiB timed probe.
- `make render-graphics-bench`:6,526 cases pass, max52,886 cycles,240 paced frames.
- `make render-bench`:256 synthetic cases pass, max36,884 cycles,240 paced frames.
- Host tests:31 pass, including exhaustive unsigned-copy edge-mask admission.
- `bash scripts/ci.sh`:passes; builds public synthetic diagnostics and assembles
  the input adapter without original inputs. Remote CI is a separate delivery gate.
- Negative `SEAQUEST_INPUT_CORRUPT_PORT2=1 make input-contract`:fails as required
  at case0, C00D actual0 vs expected128. Normal input/natural builds pass afterwards.

Exact ROM hashes, timings, held-fire birth intervals and latency pulses are in
the adjacent JSON metadata. No source-derived ROMs/art/listings/replay snapshots
or state/VRAM blobs are included in this directory.

Latency is actual emulated-device event→native-state completion and completed
SAT upload, reading VRAM after commit. It excludes visible scanout and host OS
event latency. All contacts are neutral in the controls workload. This does not
establish real collision acquisition, complete gameplay/HUD/audio, PAL or
physical-machine acceptance. Those paths require new whole-frame measurements.
