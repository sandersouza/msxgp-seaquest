"""Generate original-derived SCREEN2 HUD data locally, compressed for startup.

Glyph fields move one MSX pixel right to align six8-pixel source glyphs with
nine tiles. Oxygen retains absolute3:2 horizontal projection. No source state
is changed by this display mapping.
"""
import hashlib
import json
from pathlib import Path
from original_graphics import ROOT, read_original, extract, bitmap

OUT = ROOT/'outputs/presentation'
BASE = 0xd000


def compress(data):
    """Literal1..127; match128..255(length3..130)+absolute RAM word; zero ends."""
    positions, result, literals = {}, bytearray(), bytearray()

    def flush():
        while literals:
            length = min(127, len(literals))
            result.append(length)
            result.extend(literals[:length])
            del literals[:length]

    cursor = 0
    while cursor < len(data):
        key = data[cursor:cursor+3]
        best, source = 0, 0
        for candidate in positions.get(key, [])[-32:]:
            length = 3
            while length < 130 and cursor+length < len(data) and data[candidate+length] == data[cursor+length]:
                length += 1
            if length > best:
                best, source = length, candidate
        length = best if best >= 3 else 1
        if best >= 3:
            flush()
            result.append(128 + best-3)
            result.extend((BASE+source).to_bytes(2, 'little'))
        else:
            literals.append(data[cursor])
            if len(literals) == 127: flush()
        for index in range(cursor, cursor+length):
            positions.setdefault(data[index:index+3], []).append(index)
        cursor += length
    flush()
    result.append(0)
    return bytes(result)


def decompress(data):
    result, cursor = bytearray(), 0
    while data[cursor]:
        control = data[cursor]
        cursor += 1
        if control < 128:
            result.extend(data[cursor:cursor+control])
            cursor += control
        else:
            source = int.from_bytes(data[cursor:cursor+2], 'little')-BASE
            cursor += 2
            for index in range((control & 127)+3): result.append(result[source+index])
    if cursor != len(data)-1: raise ValueError('trailing packed HUD bytes')
    return bytes(result)


class Catalog:
    def __init__(self, excluded):
        self.free = [n for n in range(1, 256) if n not in excluded]
        self.entries, self.ids = [], {}

    def tile(self, pattern, descriptor):
        key = bytes(pattern), tuple(descriptor)
        if key not in self.ids:
            if len(self.entries) >= len(self.free): raise ValueError('HUD tile budget exceeded')
            index = self.free[len(self.entries)]
            self.ids[key] = index
            self.entries.append((index, key[0], key[1]))
        return self.ids[key]


def tiles(rows, width, catalog, descriptor):
    rows = rows + [[]]*(8*(-(-len(rows)//8))-len(rows))
    return bytes(catalog.tile(
        [sum(128 >> (x-column*8) for x in row if column*8 <= x < column*8+8)
         for row in rows[band:band+8]], descriptor[band:band+8])
        for band in range(0, len(rows), 8) for column in range(width//8))


def glyph_rows(assets, digits):
    return [[8*column+x for column, digit in enumerate(digits)
             for x in assets['blank-digit' if digit is None else f'digit-{digit}']['rows'][y]]
            for y in range(8)]


def scale(rows):
    return [sorted({dx for x in row for dx in range(x*3//2, (x+1)*3//2)}) for row in rows]


def generate(palette_fast=False):
    rom = read_original()
    assets = extract(rom)
    # Six normal source foregrounds have their own enemy pattern slots. Only
    # the black slot is recolored for other attract hues/backgrounds.
    font_first = 85 if palette_fast else 73
    top = Catalog(set(range(1,font_first)))
    bottom = Catalog(set(range(1,43 if palette_fast else 37)))
    fields = {}
    # Roles0..10 are the source FCF0 main palette.11 is the rescued-diver
    # source82 color,12 selects main0/1 according to active B7.
    fields['hud_pairs'] = b''.join(tiles(scale(glyph_rows(assets, (n//10, n%10))), 24, top,
                                        [(0,5)]*8) for n in range(100))
    fields['hud_single'] = b''.join(tiles(scale(glyph_rows(assets, (None, n))), 24, top,
                                         [(0,5)]*8) for n in range(10))
    fields['hud_blank_pair'] = tiles([[]]*8, 24, top, [(0,5)]*8)
    fields['hud_lives'] = b''.join(tiles(scale([[8*copy+x for copy in range(n) for x in row]
                                               for row in assets['life']['rows'][:8]]), 72,
                                        top, [(0,5)]*8) for n in range(7))
    font_count = len(top.entries)
    if font_count!=106: raise ValueError('source font atlas changed; revisit VRAM allocation')
    # Keep every outer pair tile and life icon resident for player2. Only a
    # middle pair tile can be dynamic, at most three8-byte tiles per update.
    required = set(fields['hud_lives']) | set(fields['hud_blank_pair'])
    for name in ('hud_pairs','hud_single'):
        required.update(identifier for offset,identifier in enumerate(fields[name]) if offset%3!=1)
    selected = set(required)
    resident_count = 54 if palette_fast else 66
    for identifier,_,_ in top.entries:
        if len(selected)==resident_count: break
        selected.add(identifier)
    if len(selected)!=resident_count: raise ValueError('player2 resident font selection exceeded budget')
    player2 = {}
    for identifier,pattern,_ in top.entries[:font_count]:
        if identifier in selected: player2[identifier] = top.tile(pattern,[(1,5)]*8)
    for source_name,target_name in (('hud_pairs','hud_pairs1'),('hud_single','hud_single1')):
        source = fields[source_name]
        fields[target_name] = b''.join(bytes([player2[source[n]],player2.get(source[n+1],0),
                                            player2[source[n+2]],source[n+1]])
                                      for n in range(0,len(source),3))
    fields['hud_lives1'] = bytes(player2[identifier] for identifier in fields['hud_lives'])
    scratch_ids = []
    for _ in range(6):
        identifier = top.free[len(top.entries)]
        top.entries.append((identifier,bytes(8),tuple([(1,5)]*8)))
        scratch_ids.append(identifier)
    if scratch_ids!=list(range(245,251)): raise ValueError('font scratch layout changed')
    fields['hud_divers'] = b''.join(tiles(scale([[8*copy+x for copy in range(n) for x in row]
                                                for row in assets['rescued-diver']['rows']]),
                                         72, bottom, [(11,8)]*9+[(8,8)]*7) for n in range(7))
    fields['hud_logo'] = b''
    for window in range(7, 16):
        rows = [[] for _ in range(8)]
        for column in range(6):
            for y, row in enumerate(bitmap(rom, 0xfe5b+16*column+window-7, 8)):
                rows[y].extend(8*column+x for x in row)
        fields['hud_logo'] += tiles(scale(rows), 72, bottom, [(10,6)]*8)

    from graphics_reference import Reference
    import numpy as np
    ref = Reference()
    roles = {0:6, 6:8, 12:7, 50:9}
    overlays = []
    oxygen = bytearray()
    for flashing in range(2):
        for value in range(17 if flashing else 65):
            image = ref.image(e6=value, e1=20 if flashing else 13)
            sampled = np.full((8, 152), 6, dtype=np.uint8)
            sampled[:5] = image[169:174, 8:160]
            projected = np.full((8, 256), 6, dtype=np.uint8)
            for x in range(8, 160):
                projected[:, 8+3*x//2:8+3*(x+1)//2] = sampled[:, x-8:x-7]
            for column in range(3, 22):
                pattern, descriptor = [], []
                for y in range(8):
                    pixels = list(map(int, projected[y, column*8:column*8+8]))
                    counts = {v:pixels.count(v) for v in set(pixels)}
                    colors = sorted(counts, key=lambda c:(-counts[c], c))[:2]
                    if len(colors) == 1: colors *= 2
                    background, foreground = colors
                    if len(counts) > 2:
                        # The first bar tile needs three colors at oxygen1..4.
                        # One resident sprite restores the lone border pixel;
                        # the pattern plane keeps filled/empty bar geometry.
                        foreground, background = (12 if 12 in counts else 0), 50
                        if column != 10 or y not in range(1,5) or pixels[0] != 6 or pixels.count(6) != 1:
                            raise ValueError('oxygen overlay geometry changed')
                        overlays.append((flashing, value, column*8, y, 6))
                    pattern.append(sum(128 >> bit for bit, color in enumerate(pixels)
                                       if color == foreground or len(counts)>2 and color==6))
                    descriptor.append((roles[foreground],roles[background]))
                oxygen.append(bottom.tile(pattern, descriptor))
    vectors = [oxygen[offset:offset+19] for offset in range(0,len(oxygen),19)]
    prefix = bytes(vectors[0][:6])
    if any(bytes(vector[:6])!=prefix for vector in vectors): raise ValueError('oxygen lettering is not invariant')
    fields['hud_oxygen_label'] = prefix
    fields['hud_oxygen'] = b''.join(vector[6:] for vector in vectors)

    # Empty-source raster supplies the original sky, water and seabed. Keep
    # every colored sky row, remove blank header gaps, retain the established
    # actor/lane coordinate contract and fill the TIA HMOVE strip consistently
    # with the port's full160-pixel canonical viewport.
    sources = list(rom[0xcf0:0xcfb])+[0x82,0x1a]
    source_image = ref.image(bb=0,be=0,e6=0)
    source_image[:,:8] = source_image[:,8:9]
    projected = np.zeros((192,256),dtype=np.uint8)
    for y in range(192):
        source_y = (32 if y<17 else y+16 if y<29 else 45 if y==29 else
                    y+15 if y<41 else y+17 if y<152 else None)
        row = source_image[source_y] if source_y is not None else np.full(160,6 if y<176 else 0,dtype=np.uint8)
        projected[y,:] = row[8] # extend the display's outer8-pixel margins
        for x in range(160): projected[y,8+3*x//2:8+3*(x+1)//2] = row[x]
    canvas = bytearray(768)
    backgrounds = [set(),set()]
    for tile_y in range(24):
        for tile_x in range(32):
            if 6<=tile_y<16:
                canvas[tile_y*32+tile_x] = 0
                continue
            catalog, bank = (top,0) if tile_y<8 else (bottom,2)
            pattern, descriptor = [], []
            for row in projected[tile_y*8:tile_y*8+8,tile_x*8:tile_x*8+8]:
                values = sorted(set(map(int,row)))
                if len(values)>2: raise ValueError('background exceeds TMS row color budget')
                background,foreground = values[0],values[-1]
                for color in values:
                    if color not in sources: sources.append(color)
                descriptor.append((sources.index(foreground),sources.index(background)))
                pattern.append(sum(128>>bit for bit,color in enumerate(row)
                                   if len(values)>1 and color==foreground))
            identifier = catalog.tile(pattern,descriptor)
            canvas[tile_y*32+tile_x] = identifier
            backgrounds[bank//2].add(identifier)
    fields['hud_background_names'] = bytes(canvas)
    fields['hud_background_top'] = bytes(sorted(backgrounds[0]))
    fields['hud_background_bottom'] = bytes(sorted(backgrounds[1]))
    fields['hud_role_sources'] = bytes(sources)
    from graphics_palette import tms_color
    fields['hud_default_roles'] = bytes(tms_color(value) for value in sources)

    classes, class_ids = [], {}
    for catalog in (top, bottom):
        for _, _, descriptor in catalog.entries:
            if descriptor not in class_ids:
                class_ids[descriptor] = len(classes)
                classes.append(descriptor)
    if len(classes)>32: raise ValueError('class-color staging exceeds C510..C60F')
    records = lambda catalog:b''.join(bytes([n])+pattern+bytes([class_ids[descriptor]])
                                     for n, pattern, descriptor in catalog.entries)
    fields['hud_top_records'] = records(top)
    fields['hud_bottom_records'] = records(bottom)
    pairs = sorted({pair for descriptor in classes for pair in descriptor})
    fields['hud_color_pairs'] = bytes(value for pair in pairs for value in pair)
    fields['hud_color_classes'] = bytes(pairs.index(pair) for descriptor in classes for pair in descriptor)
    for name, catalog in (('hud_top_class_ids',top),('hud_bottom_class_ids',bottom)):
        lookup = bytearray(256)
        for identifier,_,descriptor in catalog.entries: lookup[identifier] = class_ids[descriptor]
        fields[name] = bytes(lookup)
    image, labels = bytearray(), {}
    for name, data in fields.items():
        if palette_fast and name in ('hud_top_class_ids','hud_bottom_class_ids'):
            if name=='hud_top_class_ids':
                if len(image)>0x1a00: raise ValueError('HUD data overlaps fixedclass lookup')
                image.extend(bytes(0x1a00-len(image)))
            image.extend(bytes((-len(image))%256))
        labels[name] = BASE+len(image)
        image.extend(data)
    labels['hud_data_end'] = BASE+len(image)
    labels['hud_top_cache'] = BASE+len(image)
    labels['hud_bottom_cache'] = labels['hud_top_cache']+(256 if palette_fast else 512)
    labels['hud_ram_end'] = labels['hud_bottom_cache']+(768 if palette_fast else 512)
    if palette_fast:
        labels['hud_rgb0'] = labels['hud_bottom_cache']+256
        labels['hud_rgb1'] = labels['hud_rgb0']+256
    if labels['hud_ram_end'] > 0xf000: raise ValueError('HUD data/cache exceed declared RAM region')
    packed = compress(bytes(image))
    if decompress(packed) != image: raise ValueError('HUD compression roundtrip failed')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'hud.bin').write_bytes(image)
    (OUT/'hud-packed.bin').write_bytes(packed)
    palette_code = ['; Generated source-palette composition; local original-derived data.',
                    'hud_build_colors:']
    for index,(foreground,background) in enumerate(pairs):
        palette_code += [f'    LD A,(HUD_ROLES+{foreground})',
                         *['    RLCA']*4, '    LD B,A',
                         f'    LD A,(HUD_ROLES+{background})', '    OR B',
                         f'    LD (HUD_PAIR_COLORS+{index}),A']
    import itertools
    for index,descriptor in enumerate(classes):
        row = 0
        for pair,run in itertools.groupby(descriptor):
            count = len(list(run))
            palette_code += [f'    LD A,(HUD_PAIR_COLORS+{pairs.index(pair)})']
            if count>=2:
                palette_code += ['    LD H,A','    LD L,A']
                for offset in range(count//2):
                    palette_code += [f'    LD (HUD_CLASS_COLORS+{8*index+row+2*offset}),HL']
            if count&1:
                palette_code += [f'    LD (HUD_CLASS_COLORS+{8*index+row+count-1}),A']
            row += count
        signature_roles = sorted({role for pair in descriptor for role in pair})
        if len(signature_roles)>4:
            palette_code += ['    LD HL,(HUD_KEY)',
                             f'    LD (HUD_CLASS_SIGNATURES+{2*index}),HL']
        else:
            for half in range(2):
                roles_in_byte = signature_roles[half*2:half*2+2]
                if not roles_in_byte:
                    palette_code += ['    XOR A']
                elif len(roles_in_byte)==1:
                    palette_code += [f'    LD A,(HUD_ROLES+{roles_in_byte[0]})']
                else:
                    palette_code += [f'    LD A,(HUD_ROLES+{roles_in_byte[1]})',
                                     *['    RLCA']*4,'    LD B,A',
                                     f'    LD A,(HUD_ROLES+{roles_in_byte[0]})','    OR B']
                palette_code += [f'    LD (HUD_CLASS_SIGNATURES+{2*index+half}),A']
    # Every oxygen vector can reference roles6/7/8/9. Their four color nibbles
    # give an exact16-bit field signature, independent of source-byte aliases.
    for half in range(2):
        palette_code += [f'    LD A,(HUD_ROLES+{7+half*2})',*['    RLCA']*4,'    LD B,A',
                         f'    LD A,(HUD_ROLES+{6+half*2})','    OR B',
                         f'    LD (HUD_OXYGEN_SIGNATURE+{half}),A']
    palette_code += ['    RET']
    (OUT/'hud-palette.inc').write_text('\n'.join(palette_code)+'\n')
    (OUT/'hud.inc').write_text(''.join(f'{name} EQU ${address:04X}\n' for name, address in labels.items())+
                              f'HUD_TOP_COUNT EQU {len(top.entries)}\nHUD_BOTTOM_COUNT EQU {len(bottom.entries)}\n'+
                              f'HUD_CLASS_COUNT EQU {len(classes)}\n'+
                              f'HUD_PAIR_COUNT EQU {len(pairs)}\nHUD_ROLE_COUNT EQU {len(sources)}\n'+
                              f'HUD_BACKGROUND_TOP_COUNT EQU {len(backgrounds[0])}\nHUD_BACKGROUND_BOTTOM_COUNT EQU {len(backgrounds[1])}\n'+
                              f'HUD_SCORE_CLASS0 EQU {class_ids[tuple([(0,5)]*8)]}\n'+
                              f'HUD_SCORE_CLASS1 EQU {class_ids[tuple([(1,5)]*8)]}\n'+
                              f'HUD_DIVER_CLASS EQU {class_ids[tuple([(11,8)]*8)]}\n'+
                              f'HUD_LOGO_CLASS EQU {class_ids[tuple([(10,6)]*8)]}\n'+
                              f'HUD_FONT_SOURCE_FIRST EQU {font_first}\nHUD_FONT_SCRATCH_FIRST EQU {scratch_ids[0]}\n'+
                              f'HUD_BLANK_TILE EQU {fields["hud_blank_pair"][0]}\n'+
                              f'HUD_FONT_P0_COUNT EQU {font_count}\nHUD_FONT_P1_COUNT EQU {resident_count+6}\n'+
                              f'HUD_RIPPLE_ROLE EQU {sources.index(0x92)}\n'+
                              ('hud_packed EQU $A200\n' if palette_fast else 'hud_packed:\n    INCBIN "hud-packed.bin"\n'))
    if palette_fast:
        from palette_tables import generate as palette_generate
        palette_generate(sources,pairs,classes,fields,labels)
    metadata = dict(top_tiles=len(top.entries), bottom_tiles=len(bottom.entries),
                    color_classes=len(classes), uncompressed_bytes=len(image), packed_bytes=len(packed),
                    ram_end=hex(labels['hud_ram_end']), labels={n:hex(a) for n,a in labels.items()},
                    sha256=hashlib.sha256(image).hexdigest(),
                    oxygen_border_overlay=overlays)
    (OUT/'hud-tables.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps({k:v for k,v in metadata.items() if k not in ('labels','oxygen_border_overlay')}))
    return metadata


if __name__ == '__main__': generate()
