#!/usr/bin/env python3
"""Build and validate the synthetic MSX1 diagnostic cartridge."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / 'outputs/seaquest-diagnostic.rom'


def validate_rom(data):
    errors = []
    if len(data) != 32768:
        errors.append('expected a 32768-byte plain cartridge')
    if data[:2] != b'AB':
        errors.append('missing AB cartridge header')
    if len(data) < 4 or not 0x4010 <= int.from_bytes(data[2:4], 'little') < 0x8000:
        errors.append('entry point must lie in the first cartridge page after the header')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'check', 'run'))
    args = parser.parse_args()
    try:
        if args.action == 'build':
            ROM.parent.mkdir(exist_ok=True)
            subprocess.run([str(ROOT / '.tools/sjasmplus/sjasmplus'), '--nologo', '--raw=' + str(ROM),
                            str(ROOT / 'src/main.asm')], cwd=ROOT, check=True)
        data = ROM.read_bytes()
        errors = validate_rom(data)
        if errors:
            raise ValueError('; '.join(errors))
        manifest = {'path': ROM.name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                    'entry': int.from_bytes(data[2:4], 'little'), 'target': 'MSX1 64 KiB RAM / 16 KiB VRAM',
                    'status': 'hardware diagnostic only; no gameplay'}
        if args.action == 'build':
            ROM.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps(manifest))
        if args.action == 'run':
            subprocess.run(['openmsx', '-machine', 'C-BIOS_MSX1', '-cart', str(ROM)], cwd=ROOT, check=True)
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'ROM operation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
