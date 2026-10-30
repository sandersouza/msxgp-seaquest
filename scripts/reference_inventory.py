#!/usr/bin/env python3
"""Read-only identification and integrity checks for local research inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'references/manifest.json'
INPUTS = (
    ('references/roms/seaquest-atari2600.a26', 'atari2600-4k'),
    ('references/roms/seaquest-atari800.xex', 'atari8-xex'),
    ('references/dissasm/seaquest-atari800.s', 'source-text'),
)


def inspect_xex(data):
    """Parse standard Atari binary load segments, retaining inclusive bounds."""
    if not data.startswith(b'\xff\xff'):
        raise ValueError('missing XEX marker')
    offset = 2
    segments = []
    memory = {}
    while offset < len(data):
        if data[offset:offset + 2] == b'\xff\xff':
            offset += 2
        if offset + 4 > len(data):
            raise ValueError(f'truncated XEX segment header at {offset}')
        start = int.from_bytes(data[offset:offset + 2], 'little')
        end = int.from_bytes(data[offset + 2:offset + 4], 'little')
        offset += 4
        size = end - start + 1
        if size <= 0 or offset + size > len(data):
            raise ValueError(f'invalid/truncated XEX segment ${start:04X}-${end:04X}')
        segments.append({'start': start, 'end': end, 'size': size})
        for index, value in enumerate(data[offset:offset + size]):
            if start + index in (0x2e0, 0x2e1):
                memory[start + index] = value
        offset += size
    if not segments:
        raise ValueError('XEX contains no load segments')
    run = memory[0x2e0] | memory[0x2e1] << 8 if 0x2e0 in memory and 0x2e1 in memory else None
    return {'segments': segments, 'run_address': run}


def check_digest(data, expected):
    errors = []
    if len(data) != expected['size']:
        errors.append(f"size {len(data)} != {expected['size']}")
    for algorithm in ('sha256', 'md5'):
        if algorithm in expected and hashlib.new(algorithm, data).hexdigest() != expected[algorithm]:
            errors.append(f'{algorithm} mismatch')
    return errors


def describe(path, kind):
    data = (ROOT / path).read_bytes()
    result = {'path': path, 'format': kind, 'size': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'md5': hashlib.md5(data).hexdigest()}
    if kind == 'atari8-xex':
        result['structure'] = inspect_xex(data)
    elif kind == 'atari2600-4k':
        if len(data) != 4096:
            raise ValueError('expected a plain 4096-byte Atari 2600 cartridge')
        result['structure'] = {'nmi_vector': int.from_bytes(data[-6:-4], 'little'),
                               'reset_vector': int.from_bytes(data[-4:-2], 'little'),
                               'irq_vector': int.from_bytes(data[-2:], 'little')}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--describe', action='store_true', help='print current metadata without changing files')
    args = parser.parse_args(argv)
    try:
        if args.describe:
            print(json.dumps({'schema_version': 1, 'inputs': [describe(*item) for item in INPUTS]}, indent=2))
            return 0
        manifest = json.loads(MANIFEST.read_text())
        if manifest['schema_version'] != 1:
            raise ValueError('unsupported reference manifest schema')
        errors = []
        for expected in manifest['inputs']:
            path = expected['path']
            data = (ROOT / path).read_bytes()
            errors.extend(f'{path}: {error}' for error in check_digest(data, expected))
            actual = describe(path, expected['format'])
            if actual.get('structure') != expected.get('structure'):
                errors.append(f'{path}: binary structure mismatch')
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        print(f"Verified {len(manifest['inputs'])} original inputs; hashes and binary structures match.")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f'Reference check failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
