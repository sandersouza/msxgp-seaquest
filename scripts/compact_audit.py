"""Measure current cartridge storage and RAM obstacles; never builds a loader.

Run video_check.py --build-only first. Original-derived inputs and generated
binary data remain in ignored outputs/. The JSON contains sizes and hashes only.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import platform
import re
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = '41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8'


def storage_metrics(data):
    z = zlib.compress(data, 9)
    x = lzma.compress(data, preset=6)
    if zlib.decompress(z) != data or lzma.decompress(x) != data:
        raise ValueError('host compression round trip failed')
    return dict(raw_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                zlib9_bytes=len(z), lzma6_xz_bytes=len(x), runtime_fit_proven=False)


def occupied_banks(symbols, palette, pattern_bytes):
    # Last object in bank1 is seven four-byte base memos, not an FF sentinel.
    if not 0x4000 <= symbols['fixed_bank_end'] <= 0x8000:
        raise ValueError('fixed bank extent outside page1')
    if pattern_bytes != 608*48:
        raise ValueError('unknown enemy layout; re-audit bank-boundary padding')
    banks = [symbols['fixed_bank_end']-0x4000,
             symbols['palette_base_memo']+7*4-0x8000,
             16384, int(palette['bank_ends']['3']),
             palette['colour_program_bytes'],
             *(int(palette['bank_ends'][str(n)]) for n in (5, 6, 7))]
    if any(not 0 <= n <= 16384 for n in banks):
        raise ValueError('occupied bank extent outside 16 KiB')
    return banks


def role_factorization(records, rgb_bytes=70, class_bytes=31, role_bytes=24):
    if not records or any(len(r) != rgb_bytes+class_bytes+role_bytes for r in records):
        raise ValueError('invalid palette records')
    columns = [tuple(r[rgb_bytes+class_bytes+i] for r in records) for i in range(role_bytes)]
    columns.append((0,)*len(records))
    for i in range(rgb_bytes):
        if (tuple(r[i] >> 4 for r in records) not in columns or
                tuple(r[i] & 15 for r in records) not in columns):
            raise ValueError('RGB field cannot be reconstructed from roles')
    return dict(exact_rgb_nibble_columns=rgb_bytes, roles_bytes=len(records)*role_bytes,
                retained_class_ids_bytes=len(records)*class_bytes,
                combined_bytes=len(records)*(role_bytes+class_bytes),
                explicit_two_index_descriptor_bytes=2*rgb_bytes,
                generated_decoder_and_runtime_validated=False)


def audit(rom):
    data = rom.read_bytes()
    if len(data) != 131072:
        raise ValueError('audit expects eight ASCII16 banks, not a compact artifact')
    symbols = {n: int(v, 16) for n, v in re.findall(
        r'^(\w+): EQU 0x([0-9A-Fa-f]+)', rom.with_suffix('.sym').read_text(), re.M)}
    palette = json.loads((ROOT/'outputs/presentation/palette-tables.json').read_text())
    enemy = json.loads((ROOT/'outputs/presentation/enemy-patterns.json').read_text())
    hud = json.loads((ROOT/'outputs/presentation/hud-tables.json').read_text())
    occupied = occupied_banks(symbols, palette, enemy['pattern_bytes'])
    locations = symbols['palette_locations']-0x4000
    records = []
    for index in range(palette['records']):
        entry = data[locations+index*3:locations+(index+1)*3]
        address = int.from_bytes(entry[:2], 'little')
        offset = entry[2]*16384+address-0x8000
        records.append(data[offset:offset+palette['record_bytes']])
    factorization = role_factorization(records)
    banks = [dict(bank=n, occupied_extent_bytes=occupied[n],
                  **storage_metrics(data[n*16384:(n+1)*16384])) for n in range(8)]
    regions = [
        dict(start='0xc000', end_exclusive='0xc400', owner='canonical state, hardware mirrors, palette forecast shadows'),
        dict(start='0xc400', end_exclusive='0xc800', owner='renderer, input, clock, palette queue and colour state'),
        dict(start='0xc800', end_exclusive='0xcf00', owner='name staging, enemy palette lookup, sprite attributes and scratch'),
        dict(start='0xcf00', end_exclusive='0xd000', owner='HUD state and field/class signatures'),
        dict(start='0xd000', end_exclusive='0xec00', owner='unpacked read-only HUD atlas and field data'),
        dict(start='0xec00', end_exclusive='0xf000', owner='HUD caches and two palette RGB buffers'),
        dict(start='0xf000', end_exclusive='0xf380', owner='stack reservation; measured usage is smaller'),
        dict(start='0xf380', end_exclusive='0x10000', owner='BIOS/system work area; DOS also owns memory below this boundary'),
    ]
    metrics = storage_metrics(data)
    return dict(
        schema=1, verdict='audit only; no native DOS or plain32 artifact validated',
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        python=platform.python_version(), zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
        rom=metrics, matches_accepted_release=metrics['sha256'] == ACCEPTED,
        banks=banks, occupied_extents_total_bytes=sum(occupied),
        occupied_extents_note='Includes internal alignment and bank-boundary padding; not a minimal runtime lower bound.',
        upper_ram_reservation_bytes=0x3380, ram_regions=regions,
        unchanged_layout_accounting_bytes=sum(occupied)+0x3380,
        enemy=dict(variants=enemy['variants'], prepared_transfer_bytes=enemy['pattern_bytes'],
                   bank_boundary_padding_bytes=16, compact_cache_bytes=8192,
                   payload_reduction_bytes=enemy['pattern_bytes']+16-8192),
        palette=dict(records=palette['records'], record_bytes=palette['record_bytes'],
                     compact_records_bytes=palette['records']*palette['record_bytes'],
                     compiled_field_program_bytes=palette['colour_program_bytes'],
                     forecast_bytes=(ROOT/'outputs/presentation/palette-forecast.bin').stat().st_size,
                     role_factorization=factorization),
        hud=dict(unpacked_bytes=hud['uncompressed_bytes'], packed_bytes=hud['packed_bytes']),
        constraints=dict(plain32_max_bytes=32768, physical_ram_bytes=65536, vram_bytes=16384,
                         mapper_or_turbo_expansion_allowed=False),
        limitations=[
            'Host compression sizes exclude a Z80 decoder, its state and destination working set.',
            'A smaller storage image does not establish timing, slots, DOS TPA safety or a real load path.',
            'The unchanged expanded layout exceeds 64 KiB; this does not prove a redesigned port impossible.',
            'DOS1 TPA ends at the word at 0006h; preserving DOS requires respecting it.',
            'A DOS takeover would need an explicit BIOS/slot/stack contract and reset/exit policy.',
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'outputs/video/seaquest-video.rom')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/issue35/audit.json')
    args = parser.parse_args()
    report = audit(args.rom.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Audit saved: {args.output}; no release candidate generated.')


if __name__ == '__main__':
    main()
