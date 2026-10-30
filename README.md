# Seaquest MSX1

Native Seaquest port targeting MSX1 with **64 KiB RAM, 16 KiB VRAM**, standard
Z80 and PSG, with no expansions. The Atari 2600 original is the gameplay authority.

Development is tracked in [MSX Game Ports](https://github.com/users/sandersouza/projects/7).
See the [roadmap](docs/superpowers/specs/2026-10-30-seaquest-msx1-design.md),
[reference inventory](docs/reference-inventory.md) and [local issue copies](.github/issues/).

Current delivery: reference identification and integrity checks. A playable MSX ROM
is not available yet. Original ROMs/source must be supplied locally; they are not
distributed here.

```sh
python3 -B scripts/reference_inventory.py
python3 -B -m unittest discover -s tests -v
```
