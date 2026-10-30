#!/usr/bin/env python3
"""Extract verified local TIA art; never write original-derived data to Git paths."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA256 = 'fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43'
OUT = ROOT / 'outputs/graphics'


def read_original():
    data = (ROOT / 'references/roms/seaquest-atari2600.a26').read_bytes()
    if len(data) != 4096 or hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('unverified original graphics revision')
    return data


def bitmap(data, address, height, reflect=False, stretch=1):
    """TIA GRP bit 7 is leftmost unless REFP bit 3 is set; Y counts down."""
    rows = []
    for offset in reversed(range(height)):
        value = data[address - 0xf000 + offset]
        rows.append([x*stretch+n for x in range(8)
                     if value & (1 << (x if reflect else 7-x))
                     for n in range(stretch)])
    return rows


def ball(data, selection):
    """Decode the original ball's per-scanline HMOVE and CTRLPF writes."""
    motion = 0xfd00 + data[0xf7e+selection]
    control = 0xfd00 + data[0xf92+selection]
    # Positioning uses LFC2C rather than the enemy's LFC29: ball anchor is +2.
    x = 2
    rows = []
    for row in reversed(range(15)):
        value = data[motion-0xf000+row] >> 4
        x -= value if value < 8 else value-16
        value = data[control-0xf000+row]
        rows.append(list(range(x, x+(1 << ((value >> 4) & 3)))) if value & 2 else [])
    return rows, [motion, control]


def scale_rows(rows, x=0, left=0, right=160):
    """Absolute floor(3*x/2) mapping; clip in canonical space before scaling."""
    return [sorted({dx for sx in row if left <= x+sx < right
                    for dx in range(8+(x+sx)*3//2, 8+(x+sx+1)*3//2)})
            for row in rows]


def sprite_bytes(rows, origin=0):
    """TMS9918 16x16 order: left 16 rows, then right 16 rows."""
    if len(rows) > 16 or any(not 0 <= x-origin < 16 for row in rows for x in row):
        raise ValueError('shape exceeds hardware sprite box')
    rows = rows + [[] for _ in range(16-len(rows))]
    return bytes(sum(128 >> (x-origin-column*8) for x in row
                     if column*8 <= x-origin < column*8+8)
                 for column in range(2) for row in rows)


def extract(data):
    assets = {}

    def add(name, rows, addresses, **metadata):
        xs = [x for row in rows for x in row]
        ys = [y for y, row in enumerate(rows) if row]
        assets[name] = dict(rows=rows, source_addresses=addresses,
                            bounds=[min(xs), min(ys), max(xs), max(ys)] if xs else None,
                            **metadata)

    for frame in range(3):
        address = 0xfd00+data[0xcfb+frame]
        for reflect in range(2):
            add(f'player-{frame}-{reflect}', bitmap(data,address,12,bool(reflect),2),
                [address], canonical_width=16)
        # Last GRP1 write is suppressed before it reaches the visible scanline.
        add(f'patrol-{frame}', [[]]+bitmap(data,address+5,7,True), [address+5])
    for death in range(10,15):
        address = 0xfd00+data[0xdf0+death]
        for reflect in range(2):
            add(f'explosion-{death}-{reflect}', bitmap(data,address,12,bool(reflect),2),
                [address], canonical_width=16)
    for selection in range(16):
        rows, addresses = ball(data,selection)
        add(f'ball-{selection}', rows, addresses, anchor='C7+lane; signed row offsets')
        kind = selection & 7
        for animation in (range(8) if kind<4 else (0,)):
            # Low frame3/7 is never selected by the original's 0..2 animation.
            # Its nonzero tail would persist beyond the lane's 15-row window.
            if kind in (3,7): continue
            address = 0xfd00+data[0xfa2+kind]+(animation if kind<4 else 0)
            add(f'enemy-{selection}-{animation}', bitmap(data,address,15,bool(selection&8)),
                [address], canonical_width=8)
    for digit in range(10):
        add(f'digit-{digit}', bitmap(data,0xfe00+digit*8,8), [0xfe00+digit*8])
    add('blank-digit', bitmap(data,0xfe50,8), [0xfe50])
    add('life', bitmap(data,0xff5d,9), [0xff5d])
    # The bottom kernel draws indices9..1; index0 is deliberately omitted.
    add('rescued-diver', bitmap(data,0xfff2,9), [0xfff2])
    for name, top in (('activision',15),('seaquest',7)):
        rows = [[] for _ in range(8)]
        addresses = [0xfe5b+16*n+top-7 for n in range(6)]
        for n,address in enumerate(addresses):
            for y,row in enumerate(bitmap(data,address,8)):
                rows[y].extend(n*8+x for x in row)
        add(name, rows, addresses, canonical_width=48)
    # LF166 sets NUSIZ0=$35: missile width is eight canonical pixels.
    add('torpedo', [list(range(8))] if data[0xe58]&2 else [[]], [0xfe58],
        width_register=0x35)
    # Display-only view: the kernel clears GRP0 at raw lines53..56. Keep the
    # complete canonical mask above for the collision implementation.
    for name,asset in list(assets.items()):
        if name.startswith(('player-','explosion-')):
            for y in range(13,24):
                rows = [row[:] if not 53 <= y+33+n <= 56 else []
                        for n,row in enumerate(asset['rows'])]
                add(f'surface-{name}-{y}',rows,asset['source_addresses'],
                    display_variant_of=name,player_y=y)
    return assets


def sprite_bank(assets):
    """ROM catalog, normal images first; clipped images use inactive VRAM slots."""
    bank = [bytes(32)]
    lookup = {}
    names = [name for name in assets if name.startswith(
        ('player-','explosion-','ball-','patrol-','torpedo'))]
    # First enumerate interior images so they form a contiguous resident bank.
    for name in names:
        rows = assets[name]['rows']
        for x in (64,65):
            scaled = scale_rows(rows,x)
            for chunk in range(2 if name.startswith(('player-','explosion-')) else 1):
                origin = 8+x*3//2+16*chunk
                crop = [[px for px in row if origin <= px < origin+16] for row in scaled]
                if name.startswith('patrol-'): crop = [[] for _ in range(8)]+crop
                value = sprite_bytes(crop,origin)
                if value not in bank: bank.append(value)
    # The eight unused VRAM slots are best spent on missile edge variants:
    # these can coincide with all four clipped lane objects and the patrol.
    for x in range(153,160):
        rows = scale_rows(assets['torpedo']['rows'],x)
        value = sprite_bytes(rows,8+x*3//2)
        if value not in bank: bank.append(value)
    resident = len(bank)
    for name, asset in assets.items():
        if not name.startswith(('player-','explosion-','ball-','patrol-','torpedo','surface-')):
            continue
        # All edges, including signed diver offsets; invisible X is handled by SAT.
        positions = (range(64,65) if name.startswith('surface-') else
                     range(21,135) if name.startswith(('player-','explosion-')) else range(160))
        for x in positions:
            rows = scale_rows(asset['rows'],x)
            anchor = 8+x*3//2
            chunks = 2 if name.startswith(('player-','explosion-','surface-')) else 1
            indices = []
            for chunk in range(chunks):
                origin = anchor+16*chunk
                crop = [[px for px in row if origin <= px < origin+16] for row in rows]
                if name.startswith('patrol-'):
                    crop = [[] for _ in range(8)] + crop
                value = sprite_bytes(crop,origin)
                if value not in bank:
                    bank.append(value)
                indices.append(bank.index(value))
            lookup[f'{name}@{x}'] = dict(x=anchor,patterns=indices)
    return b''.join(bank), lookup, resident


def write_assembly(bank,lookup,resident):
    if resident+16 > 64: raise ValueError('resident bank plus two scratch banks exceeds VRAM')
    if len(bank)//32 > 256: raise ValueError('ROM catalog exceeds byte lookup indices')
    def entry(name,x,chunk=0): return lookup[f'{name}@{x}']['patterns'][chunk]
    def table(label, values):
        return label+':\n'+''.join('    DB '+','.join(map(str,values[n:n+16]))+'\n'
                                   for n in range(0,len(values),16))
    players = [f'player-{f}-{r}' for r in range(2) for f in range(3)]
    players += [f'explosion-{d}-{r}' for d in range(10,15) for r in range(2)]
    text = f'SPRITE_RESIDENT EQU {resident}\n'
    text += 'original_sprite_catalog:\n    INCBIN "sprite-patterns.bin"\n'
    text += table('player_images',[entry(name,64,chunk) for name in players for chunk in range(2)])
    text += table('surface_images',[entry(f'surface-{name}-{y}',64,chunk)
                                   for name in players for y in range(13,24) for chunk in range(2)])
    text += 'surface_pointers:\n    DW '+','.join('surface_images+'+str(n*22) for n in range(16))+'\n'
    for prefix,count in (('ball',16),('patrol',3),('torpedo',1)):
        text += table(prefix+'_images',[entry(f'{prefix}-{n}' if count>1 else prefix,
                                               64+i if i<2 else min(159,151+i))
                                       for n in range(count) for i in range(16)])
    from graphics_palette import tms_color
    text += table('tia_to_tms',[tms_color(n) for n in range(256)])
    (OUT/'sprites.inc').write_text(text)


def generate():
    data = read_original()
    assets = extract(data)
    bank,lookup,resident = sprite_bank(assets)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'canonical.json').write_text(json.dumps(assets,sort_keys=True)+'\n')
    (OUT/'sprite-patterns.bin').write_bytes(bank)
    (OUT/'sprite-lookup.json').write_text(json.dumps(lookup,sort_keys=True)+'\n')
    write_assembly(bank,lookup,resident)
    from graphics_palette import tms_color
    colors = dict(main=[tms_color(n) for n in data[0xcf0:0xcfb]],
                  horizon=[tms_color(n) for n in data[0xce6:0xcf0]],
                  enemies=[tms_color(n) for n in data[0xf0f:0xf17]],
                  explosions=[tms_color(n) for n in data[0xf17:0xf2f]],patrol=tms_color(8))
    (OUT/'palette.json').write_text(json.dumps(colors,indent=2)+'\n')
    report = dict(original_sha256=SHA256,assets=len(assets),rom_catalog_patterns=len(bank)//32,
                  rom_catalog_bytes=len(bank),resident_patterns=resident,
                  scratch_patterns=16,vram_sprite_bytes=(resident+16)*32,sprite_limit_bytes=2048,
                  files={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest()
                         for name in ('canonical.json','sprite-patterns.bin','sprite-lookup.json')})
    (OUT/'extraction.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return assets,bank,lookup


if __name__ == '__main__': generate()
