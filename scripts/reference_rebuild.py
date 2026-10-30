#!/usr/bin/env python3
"""Rebuild both local references and export address-only research metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from reference_inventory import ROOT, main as verify_inputs


def binary_identity(original, rebuilt):
    mismatch = next((n for n, (a, b) in enumerate(zip(original, rebuilt)) if a != b), None)
    if mismatch is None and len(original) != len(rebuilt):
        mismatch = min(len(original), len(rebuilt))
    return {'byte_identical': original == rebuilt, 'original_size': len(original),
            'rebuilt_size': len(rebuilt), 'sha256': hashlib.sha256(rebuilt).hexdigest(),
            'first_difference': mismatch}


def listing_map(listing, end=0x10000):
    """Export DiStella's classification through DASM; not independent semantics."""
    rows = []
    for line in listing.splitlines():
        match = re.match(r'^\s*\d+\s+([0-9a-fA-F]{4})\s+([0-9a-fA-F]{2})(?=\s|\*)', line)
        if match:
            address = int(match[1], 16)
            if 0xf000 <= address < end:
                rows.append((address, 'data' if '.byte' in line.lower() else 'code'))
    if not rows or rows[0][0] != 0xf000:
        raise ValueError('listing does not start at $F000')
    ranges = []
    for n, (address, kind) in enumerate(rows):
        stop = rows[n + 1][0] if n + 1 < len(rows) else end
        if stop <= address:
            raise ValueError('listing addresses are not strictly increasing')
        if ranges and ranges[-1]['kind'] == kind:
            ranges[-1]['end'] = stop - 1
        else:
            ranges.append({'start': address, 'end': stop - 1, 'kind': kind})
    return ranges


def symbols(text, mads=False):
    pattern = r'^00\s+([0-9A-Fa-f]{4})\s+(\S+)' if mads else r'^(\S+)\s+([0-9a-fA-F]{4})\s'
    result = {}
    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            name, address = (match[2], match[1]) if mads else (match[1], match[2])
            result[name] = int(address, 16)
    return result


def run(command, stdout=None):
    subprocess.run([str(x) for x in command], cwd=ROOT, check=True, stdout=stdout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--distella', default=str(ROOT / '.tools/distella/distella'))
    parser.add_argument('--mads', default=str(ROOT / '.tools/mads'))
    parser.add_argument('--dasm', default='dasm')
    args = parser.parse_args(argv)
    try:
        if verify_inputs([]):
            return 1
        out = ROOT / 'outputs/reference'
        out.mkdir(parents=True, exist_ok=True)
        source = out / 'seaquest-atari2600.asm'
        listing = out / 'seaquest-atari2600.lst'
        symbol_file = out / 'seaquest-atari2600.sym'
        binary = out / 'seaquest-atari2600-rebuilt.a26'
        # Never use DiStella -r: relocating mirrored addresses changes ROM bytes.
        with source.open('w') as stream:
            # Upstream DiStella has a small fixed filename buffer. Keep the input
            # relative to our explicit cwd instead of passing a long absolute path.
            run([args.distella, '-paf', 'references/roms/seaquest-atari2600.a26'], stdout=stream)
        run([args.dasm, source, '-f3', f'-o{binary}', f'-l{listing}', f'-s{symbol_file}'])
        xex = out / 'seaquest-atari800-rebuilt.xex'
        lab = out / 'seaquest-atari800.lab'
        run([args.mads, ROOT / 'references/dissasm/seaquest-atari800.s', f'-o:{xex}',
             f'-l:{out / "seaquest-atari800.lst"}', f'-t:{lab}'])
        original_symbols = symbols(symbol_file.read_text())
        port_symbols = symbols(lab.read_text(), mads=True)
        correspondence = [{'label': name, 'atari2600': original_symbols[name], 'atari800': port_symbols[name]}
                          for name in sorted(original_symbols.keys() & port_symbols.keys())
                          if re.fullmatch(r'LF[0-9A-F]{3}', name)]
        report = {
            'schema_version': 1,
            'atari2600': binary_identity((ROOT / 'references/roms/seaquest-atari2600.a26').read_bytes(), binary.read_bytes()),
            'atari800': binary_identity((ROOT / 'references/roms/seaquest-atari800.xex').read_bytes(), xex.read_bytes()),
            'classification': 'DiStella automatic reachability heuristic, not independent proof of code/data semantics',
            'atari2600_ranges': listing_map(listing.read_text()),
            'shared_labels': correspondence,
        }
        (out / 'rebuild-report.json').write_text(json.dumps(report, indent=2) + '\n')
        for name in ('atari2600', 'atari800'):
            if not report[name]['byte_identical']:
                raise ValueError(f'{name} rebuild mismatch: {report[name]}')
        print(f'Both complete binaries are byte-identical; exported {len(correspondence)} shared label addresses.')
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Reference rebuild failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
