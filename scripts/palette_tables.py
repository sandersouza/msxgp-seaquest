"""Exact source-palette colour rows and class IDs, banked on standard ASCII16.

Only derived output files contain reference-derived pixels/colour rows. ByteIDs
are interned independently inside each fixed tile class,0 invalid, never hashes.
"""
import json
import itertools
import re
import subprocess
from pathlib import Path
from graphics_palette import tms_color
from original_graphics import ROOT

OUT = ROOT/'outputs/presentation'


def colour_programs(classes,fields,labels,default,future_base):
    """Bank4 native span routines; bank1/source data remain untouched."""
    limit = labels['hud_background_names']-0xd000
    lookup = bytearray(limit)
    programs,spans = {},{}
    background = {}
    groups = [('hud_pairs',3,0),('hud_single',3,0),('hud_blank_pair',3,0),
              ('hud_lives',9,0),('hud_lives1',9,0),('hud_divers',18,2),
              ('hud_logo',9,2),('hud_oxygen_label',6,2),('hud_oxygen',13,2),
              ('hud_background_top',len(fields['hud_background_top']),0),
              ('hud_background_bottom',len(fields['hud_background_bottom']),2)]
    for name,stride,bank in groups:
        class_map = fields['hud_top_class_ids' if not bank else 'hud_bottom_class_ids']
        cache_page = labels['hud_top_cache' if not bank else 'hud_bottom_cache']>>8
        for offset in range(0,len(fields[name]),stride):
            vector = []
            for tile in sorted(set(fields[name][offset:offset+stride])):
                cls = class_map[tile]
                if vector and vector[-1][0]+vector[-1][1]==tile and vector[-1][2]==cls:
                    vector[-1][1] += 1
                else: vector.append([tile,1,cls,bank,cache_page])
            key = tuple(map(tuple,vector))
            if key not in programs: programs[key] = len(programs)
            for span in key:
                if span not in spans: spans[span] = len(spans)
            index = programs[key]
            if name.startswith('hud_background_'): background[name] = index
            else: lookup[labels[name]+offset-0xd000] = index
    if len(programs)>256: raise ValueError('colour program byte index overflow')
    score_class = fields['hud_top_class_ids'][fields['hud_lives1'][0]]
    dynamic_tiles = set(range(245,251))|set(fields['hud_blank_pair'])
    for name in ('hud_pairs1','hud_single1'):
        for offset in range(0,len(fields[name]),4):
            dynamic_tiles.update(fields[name][offset:offset+3])
    dynamic_spans = {}
    for tile in sorted(dynamic_tiles):
        span = (tile,1,score_class,0,labels['hud_top_cache']>>8)
        if span not in spans: spans[span] = len(spans)
        dynamic_spans[tile] = spans[span]
    bases = []
    for player,life,logo in [(p,0,l) for p in range(2) for l in range(9)]+[(0,3,l) for l in range(9)]:
        life_name = 'hud_lives1' if player else 'hud_lives'
        vectors = [(fields[life_name][life*9:life*9+9],0),
                   (fields['hud_blank_pair'],0),(fields['hud_divers'][:18],2),
                   (fields['hud_logo'][logo*9:logo*9+9],2),(fields['hud_oxygen'][:13],2),
                   (fields['hud_oxygen_label'],2),(fields['hud_background_top'],0),
                   (fields['hud_background_bottom'],2)]
        zero = list(fields['hud_single1'][:3] if player else fields['hud_single'][:3])
        if 0 in zero:
            zero = [tile for tile in zero if tile]+[247,250]
        vectors.append((zero,0))
        keys = []
        for bank in (0,2):
            ids = sorted({tile for vector,which in vectors if which==bank for tile in vector})
            clsmap = fields['hud_top_class_ids' if not bank else 'hud_bottom_class_ids']
            page = labels['hud_top_cache' if not bank else 'hud_bottom_cache']>>8
            merged = []
            for tile in ids:
                cls = clsmap[tile]
                if merged and merged[-1][0]+merged[-1][1]==tile and merged[-1][2]==cls:
                    merged[-1][1] += 1
                else: merged.append([tile,1,cls,bank,page])
            keys += list(map(tuple,merged))
        for span in keys:
            if span not in spans: spans[span] = len(spans)
        if len(keys)+9>=120: raise ValueError('default queue overlaps static palette state')
        pointers = [labels[life_name]+life*9,labels['hud_divers'],labels['hud_logo']+logo*9,
                    labels['hud_oxygen'],labels['hud_oxygen_label'],
                    labels['hud_background_top'],labels['hud_background_bottom']]
        bases.append((keys,pointers))
    # VBlank uses a return-address stream. Each writer has constant VRAM
    # coordinates/class and returns directly to the next queued writer.
    writers = ['    ORG $9B00']
    for (tile,count,cls,bank,_),index in spans.items():
        address = 0x2000+bank*2048+tile*8
        uniform = len(set(classes[cls]))==1
        writers += [f'colour_writer_{index}:',f'    LD A,{address&255}',
                    '    OUT ($99),A',f'    LD A,{(address>>8)|64}','    OUT ($99),A',
                    f'    LD L,{cls*8}']
        if uniform:
            writers += ['    LD A,(HL)',f'    LD B,{count}','    JP (IX)']
        else:
            writers += [f'    LD D,{count}',f'    LD E,{cls*8}','    JP (IY)']
    writers += ['palette_writers_end:','    ASSERT $ <= $C000']
    # Resolve constant writer addresses before assembling the independent bank4.
    # Stub targets only fix three-byte JP encoding; the final link resolves them.
    stubs = []
    (OUT/'palette-writers.asm').write_text('\n'.join(stubs+writers)+'\n')
    subprocess.run([str(ROOT/'.tools/sjasmplus/sjasmplus'),'--nologo',
                    '--sym='+str(OUT/'palette-writers.sym'),str(OUT/'palette-writers.asm')],check=True)
    writer_symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',
                                                      (OUT/'palette-writers.sym').read_text(),re.M)}
    (OUT/'palette-writers.inc').write_text('\n'.join(writers[1:])+'\n')
    gen = ['palette_restore_default_roles:']
    # Roles remain real TMS indices; only the class rows substitute water0.
    default_roles = bytes(tms_color(value) for value in fields['hud_role_sources'])
    for offset in range(0,24,2):
        word = int.from_bytes(default_roles[offset:offset+2],'little')
        gen += [f'    LD HL,${word:04X}',f'    LD (HUD_ROLES+{offset}),HL']
    gen += ['    RET','palette_translate_ids_banked:',
            '    LD A,(PAL_GEN_SERIAL)','    CP 240','    CALL NC,palette_rebase_generations',
            '    LD A,(PAL_GEN_SERIAL)','    INC A','    LD (PAL_GEN_SERIAL),A','    LD C,A',
            '    LD A,(PAL_STATIC_DEFAULT)','    OR A','    JP NZ,.from_default']
    for cls in range(31):
        # Token1 is permanently reserved for this class's default RGB.
        static = default[248+cls]
        gen += [f'    LD A,(PAL_PENDING_STATIC+{cls})',f'    CP {static}',
                '    LD A,1','    JR Z,.store_'+str(cls),
                f'    LD A,(PAL_PENDING_STATIC+{cls})',f'    LD HL,PAL_CURRENT_STATIC+{cls}',
                '    CP (HL)','    LD A,C','    JR NZ,$+5',
                f'    LD A,(HUD_CLASS_SIGNATURES+{cls})',f'.store_{cls}:',
                f'    LD (PAL_NEXT_IDS+{cls}),A']
    gen += ['    RET','.from_default:']
    for cls in range(31):
        gen += [f'    LD A,(PAL_PENDING_STATIC+{cls})',f'    CP {default[248+cls]}',
                '    LD A,1','    JR Z,$+3','    LD A,C',f'    LD (PAL_NEXT_IDS+{cls}),A']
    gen += ['    RET','palette_rebase_current_tokens:',
            '    LD A,(PAL_STATIC_DEFAULT)','    OR A','    JP NZ,palette_generations_default']
    for cls in range(31):
        gen += [f'    LD A,(PAL_CURRENT_STATIC+{cls})',f'    CP {default[248+cls]}',
                '    LD A,1','    JR Z,$+3','    INC A',f'    LD (HUD_CLASS_SIGNATURES+{cls}),A']
    gen += ['    RET','palette_base_clear_cache:','    XOR A','    LD HL,0']
    for bank in (0,2):
        tiles = sorted({tile for keys,_ in bases for first,count,cls,which,_ in keys if which==bank
                        for tile in range(first,first+count)})
        while tiles:
            tile = tiles.pop(0)
            address = labels['hud_top_cache' if not bank else 'hud_bottom_cache']+tile
            if tiles and tiles[0]==tile+1:
                tiles.pop(0)
                gen += [f'    LD (${address:04X}),HL']
            else: gen += [f'    LD (${address:04X}),A']
    gen += ['    RET']
    (OUT/'palette-generations.inc').write_text('\n'.join(gen)+'\n')
    base_code = ['palette_default_bases:',
                 '    DW '+','.join(f'palette_default_base_{n}' for n in range(len(bases)))]
    for index,(keys,pointers) in enumerate(bases):
        base_code += [f'palette_default_base_{index}:',f'    DB {len(keys)}',
                      '    DW '+','.join(str(writer_symbols[f'colour_writer_{spans[span]}']) for span in keys)]
    base_code += ['palette_base_memo:']
    for field,pointer in enumerate(bases[0][1]):
        sig = '0' if field<3 else 'PALETTE_DEFAULT_INDEX'
        base_code += [f'    DW ${pointer:04X}',f'    DB {sig},0']
    (OUT/'palette-default-bases.inc').write_text('\n'.join(base_code)+'\n')
    (OUT/'palette-program-lookup.bin').write_bytes(lookup)
    code = ['    ORG $8000','palette_program_lookup:',
            '    INCBIN "palette-program-lookup.bin"','palette_program_pointers:']
    code += ['    DW '+','.join(f'colour_program_{n}' for n in range(start,min(start+16,len(programs))))
             for start in range(0,len(programs),16)]
    for key,index in programs.items():
        code += [f'colour_program_{index}:']
        code += [f'    CALL colour_span_{spans[span]}' for span in key]+['    RET']
    for (tile,count,cls,bank,cache_page),index in spans.items():
        code += [f'colour_span_{index}:',f'    LD A,(${0xcfb0+cls:04X})',
                 f'    LD HL,${cache_page*256+tile:04X}']
        if count==1:
            code += ['    CP (HL)','    RET Z','    LD (HL),A']
        else:
            code += ['    LD C,A',f'    LD B,{count}','    PUSH HL',
                     '.test:','    LD A,(HL)','    CP C','    JR NZ,.dirty',
                     '    INC L','    DJNZ .test','    POP HL','    RET',
                     '.dirty:','    POP HL',f'    LD B,{count}',
                     '.mark:','    LD (HL),C','    INC L','    DJNZ .mark']
        writer = writer_symbols[f'colour_writer_{index}']
        code += ['    EX DE,HL',f'    LD (HL),{writer&255}','    INC HL',
                 f'    LD (HL),{writer>>8}','    INC HL','    EX DE,HL',
                 '    LD HL,$C6DC','    INC (HL)','    RET']
    for name,index in background.items():
        code += [f'palette_{"top" if name.endswith("top") else "bottom"}_background_program EQU colour_program_{index}']
    code += ['palette_dynamic_programs:']
    for start in range(0,256,16):
        code += ['    DW '+','.join(f'colour_span_{dynamic_spans[tile]}' if tile in dynamic_spans else '0'
                                   for tile in range(start,start+16))]
    code += ['palette_program_end:','    ASSERT $ <= $C000','    DS $C000-$,$FF']
    (OUT/'palette-programs.asm').write_text('\n'.join(code)+'\n')
    subprocess.run([str(ROOT/'.tools/sjasmplus/sjasmplus'),'--nologo',
                    '--raw='+str(OUT/'palette-bank4.bin'),
                    '--sym='+str(OUT/'palette-programs.sym'),str(OUT/'palette-programs.asm')],check=True)
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',
                                               (OUT/'palette-programs.sym').read_text(),re.M)}
    definitions = ''.join(f'{name} EQU ${symbols[name]:04X}\n' for name in
                          ('palette_program_lookup','palette_program_pointers','palette_dynamic_programs',
                           'palette_top_background_program','palette_bottom_background_program'))
    future = [f'    ORG ${future_base:04X}',
              f'F_HUD_LOGO EQU ${labels["hud_logo"]:04X}',
              f'F_SCORE0 EQU {classes.index(tuple([(0,5)]*8))}',
              f'F_SCORE1 EQU {score_class}',
              f'F_BLANK_TILE EQU {fields["hud_blank_pair"][0]}',
              f'F_DIVER EQU {classes.index(tuple([(11,8)]*8))}',
              f'F_LOGO EQU {classes.index(tuple([(10,6)]*8))}',
              'forecast_lookup:','    INCBIN "palette-program-lookup.bin"',
              'forecast_program_pointers:']
    for start in range(0,len(programs),16):
        future += ['    DW '+','.join(f'forecast_program_{n}' for n in range(start,min(start+16,len(programs))))]
    future += ['forecast_dynamic_writers:']
    for start in range(0,256,16):
        future += ['    DW '+','.join(str(writer_symbols[f'colour_writer_{dynamic_spans[tile]}'])
                                     if tile in dynamic_spans else '0' for tile in range(start,start+16))]
    for key,index in programs.items():
        future += [f'forecast_program_{index}:',f'    DB {len(key)}']
        for tile,count,cls,bank,cache_page in key:
            writer = writer_symbols[f'colour_writer_{spans[tile,count,cls,bank,cache_page]}']
            future += [f'    DB {tile},{count|(128 if bank else 0)},{cls},{writer&255},{writer>>8}']
    for name,index in background.items():
        future += [f'forecast_{"top" if name.endswith("top") else "bottom"} EQU forecast_program_{index}']
    future += [f'F_BACKGROUND_NAMES EQU ${labels["hud_background_names"]:04X}',
               f'F_BACKGROUND_TOP EQU ${labels["hud_background_top"]:04X}',
               f'F_BACKGROUND_BOTTOM EQU ${labels["hud_background_bottom"]:04X}',
               f'    INCLUDE "{ROOT}/src/palette_forecast.asm"',
               'forecast_end:','    ASSERT $ <= $C000']
    (OUT/'palette-forecast.asm').write_text('\n'.join(future)+'\n')
    subprocess.run([str(ROOT/'.tools/sjasmplus/sjasmplus'),'--nologo',
                    '--raw='+str(OUT/'palette-forecast.bin'),
                    '--sym='+str(OUT/'palette-forecast.sym'),str(OUT/'palette-forecast.asm')],check=True)
    future_symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',
                                                      (OUT/'palette-forecast.sym').read_text(),re.M)}
    definitions += ''.join(f'{name}_banked EQU ${future_symbols[name]:04X}\n'
                           for name in ('palette_forecast_tick','palette_forecast_apply'))
    return definitions,symbols['palette_program_end']-0x8000,(OUT/'palette-forecast.bin').read_bytes()


def generate(sources,pairs,classes,fields,labels):
    intern = [dict() for _ in classes]
    records,unique,directory = [],{},bytearray()
    for mask in (7,15,247,255,0):
        for xor in range(0,256,2):
            roles = bytes(tms_color((value^xor)&mask) for value in sources)
            # Water uses transparent colour0 and the VDP backdrop. Its hue
            # changes once in R7, independent of every enemy's colour cache.
            rows = bytes(((0 if f==2 else roles[f])<<4)|(0 if b==2 else roles[b])
                         for descriptor in classes for f,b in descriptor)
            identifiers = bytearray()
            for index in range(len(classes)):
                vector = rows[8*index:8*index+8]
                if vector not in intern[index]: intern[index][vector] = len(intern[index])+1
                identifiers.append(intern[index][vector])
            record = rows+identifiers+roles
            if len(record)!=303: raise ValueError('palette record layout changed')
            if record not in unique:
                unique[record] = len(records); records.append(record)
            directory.append(unique[record])
    if len(records)>255 or any(len(pool)>255 for pool in intern): raise ValueError('palette byteID overflow')
    # Store one colour per descriptor run, rather than eight copies for a solid
    # tile. Fixed native expanders restore the full248-byte RGB image in eight
    # bounded prefetch chunks. IDs/roles retain their original31/24-byte layout.
    runs = []
    for cls,descriptor in enumerate(classes):
        offset = 0
        for pair,group in itertools.groupby(descriptor):
            count = len(list(group))
            runs.append((8*cls+offset,count))
            offset += count
    copy_code = ['palette_rgb_copies:', '    DW '+','.join(f'palette_rgb_copy_{n}' for n in range(8))]
    for chunk in range(8):
        copy_code += [f'palette_rgb_copy_{chunk}:']
        for offset,count in runs:
            if offset//32!=chunk: continue
            copy_code += ['    LD A,(HL)','    INC HL']
            copy_code += ['    LD (DE),A','    INC E']*count
        copy_code += ['    RET']
    compact = [bytes(record[offset] for offset,_ in runs)+record[248:] for record in records]
    record_bytes = len(compact[0])
    banks = {bank:bytearray([255])*16384 for bank in (3,5,6,7)}
    sprites = (ROOT/'outputs/graphics/sprite-bank5-head.bin').read_bytes()
    packed = (OUT/'hud-packed.bin').read_bytes()
    if len(sprites)!=0x2200: raise ValueError('sprite bank layout changed')
    banks[5][:len(sprites)] = sprites
    banks[5][0x2200:0x2200+len(packed)] = packed
    enemy = (OUT/'enemy-patterns.bin').read_bytes()
    banks[3][:] = enemy[16384:]
    info = json.loads((OUT/'enemy-patterns.json').read_text())
    starts = {6:0,7:0,5:0x2200+len(packed),3:info['pattern_bytes']+16-16384}
    locations = []
    for record in compact:
        bank = next(bank for bank in (6,7,5,3) if starts[bank]+len(record)<=16384-(7000 if bank==7 else 0))
        offset = starts[bank]
        banks[bank][offset:offset+len(record)] = record
        starts[bank] += len(record)
        locations.extend(((0x8000+offset)&255,(0x8000+offset)>>8,bank))
    (OUT/'palette-key-ids.bin').write_bytes(directory)
    (OUT/'palette-locations.bin').write_bytes(bytes(locations))
    default_index = directory[3*128]
    default = records[default_index]
    (OUT/'palette-default.bin').write_bytes(default)
    definitions,program_bytes,future = colour_programs(classes,fields,labels,default,0x8000+starts[7])
    banks[7][starts[7]:starts[7]+len(future)] = future
    starts[7] += len(future)
    for bank,data in banks.items():
        if len(data)!=16384: raise ValueError('palette bank size changed')
        (OUT/f'palette-bank{bank}.bin').write_bytes(data)
    (OUT/'palette-tables.inc').write_text(
        f'PALETTE_DEFAULT_INDEX EQU {default_index}\n'+
        f'PALETTE_BLACK_INDEX EQU {directory[4*128]}\n'+
        f'PALETTE_COMPACT_RGB_BYTES EQU {len(runs)}\n'+
        definitions+'\n'.join(copy_code)+'\n'+
        'palette_key_ids:\n    INCBIN "palette-key-ids.bin"\n'+
        'palette_locations:\n    INCBIN "palette-locations.bin"\n'+
        '    ALIGN 256\npalette_mask_groups:\n'+''.join('    DB '+','.join(str((7,15,247,255,0).index(n)) if n in (7,15,247,255,0) else '255' for n in range(start,start+32))+'\n' for start in range(0,256,32)))
    (OUT/'palette-tables.json').write_text(json.dumps(dict(records=len(records),record_bytes=record_bytes,
        class_id_max=max(map(len,intern)),bank_ends=starts,default_index=default_index,
        colour_program_bytes=program_bytes),indent=2)+'\n')
