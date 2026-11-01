"""Build the native DOS1 executable for unexpanded 64 KiB MSX1 machines.

Reference-derived data and all binaries stay in ignored outputs/. The original
ASCII16 cartridge target is independent. Both targets share the native game core.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import re
import random
import subprocess
import sys
import shutil
from source_identity import fingerprint,verify as verify_source

root=Path(__file__).resolve().parents[1]
out=root/'src/disk'
dest=root/'outputs/disk'
dest.mkdir(exist_ok=True,parents=True)
sys.path.insert(0,str(root/'scripts'))

def absolute(text,base):
    return re.sub(r'(INCLUDE|INCBIN) "([^"]+)"',lambda m:
                  f'{m[1]} "{(base/m[2]).resolve()}"' if not Path(m[2]).is_absolute() else m[0],text)

def verify_no_mapper(path,visited=None):
    """Scan the actual include tree, including generated role-loading code."""
    visited=set() if visited is None else visited
    path=path.resolve()
    if path in visited:
        return
    visited.add(path)
    text=path.read_text()
    if re.search(r'\(\s*\$7000\s*\)',text,re.I):
        raise ValueError(f'remaining mapper access: {path.name}')
    for child in re.findall(r'^\s*INCLUDE "([^"]+)"',text,re.M|re.I):
        verify_no_mapper(path.parent/child,visited)

def extract(text,first,last):
    a=text.index(first);b=text.index(last,a)
    return text[:a]+text[b:],text[a:b]


def verify_writer_map(linked, generated):
    """Reject stale absolute pointers, including same-size Python-cache errors."""
    actual={n:v for n,v in linked.items() if n.startswith('colour_writer_')}
    expected={n:v for n,v in generated.items() if n.startswith('colour_writer_')}
    if not actual or actual!=expected:
        raise ValueError('stale or incomplete numeric writer addresses')


def verify_layout(symbols):
    ranges=(('native_static_start','native_static_end',0x100,0xc000),
            ('native_cold_start','native_cold_end',0xf000,0xf300),
            ('native_high_start','native_high_end',0xf400,0xfff4))
    for first,last,start,ceiling in ranges:
        if symbols[first]!=start or not start<symbols[last]<=ceiling:
            raise ValueError(f'{first}: overlaps workspace, stack, or slot register')

def generate(writerbase):
    import disk_palette_tables
    disk_palette_tables.WRITER_BASE=writerbase
    sys.modules['palette_tables']=disk_palette_tables
    from hud_tables import generate as hud_generate
    hud_generate(True)


def sources():
    cold=(out/'boot.asm').read_text()
    renderer=absolute((root/'src/render.asm').read_text(),root/'src')
    renderer=renderer.replace('render_commit:\n','render_commit:\n    CALL compact_commit_enemies\n').replace('    CALL upload_banked_lane','    compact_prepare (3-lane_index)')
    renderer=renderer.replace('CALL $005F','CALL native_chgmod').replace('CALL $0056','CALL native_filvrm').replace('CALL $0047','CALL native_wrtvdp')
    renderer,part=extract(renderer,'render_init:\n','; OUTI (')
    cold+='\n'+part
    (dest/'render.asm').write_text(renderer)
    hud=(root/'src/hud.asm').read_text()
    a=hud.index('    LD HL,hud_packed\n');b=hud.index('    XOR A\n',a)
    hud=hud[:a]+hud[b:]
    hud,part=extract(hud,'hud_init:\n','hud_unpack:\n')
    cold+='\n'+part
    hud,_=extract(hud,'hud_unpack:\n','hud_load_patterns:\n')
    hud,part=extract(hud,'hud_load_patterns:\n','    IFNDEF WITH_PALETTE\nhud_prepare_palette:')
    cold+='\n'+part
    (dest/'hud.asm').write_text(hud)
    inputs=(root/'src/input.asm').read_text().replace('CALL $0141','CALL native_snsmat').replace('CALL $0096','CALL native_rdpsg').replace('CALL $0093','CALL native_wrtpsg')
    inputs+='\n    INCLUDE \"'+str(out/'io.asm')+'\"\n'
    inputs,part=extract(inputs,'input_init:\n','sample_input:\n')
    cold+='\n'+part
    (dest/'input.asm').write_text(inputs)
    audio=(root/'src/audio.asm').read_text().replace('CALL $0093','CALL native_wrtpsg')
    audio,part=extract(audio,'audio_init:\n','audio_sync:\n')
    cold+='\n'+part
    (dest/'audio.asm').write_text(audio)
    video=(root/'src/video.asm').read_text().replace('($002B)','($F3F0)')
    (dest/'video.asm').write_text(video)
    backend=absolute((out/'palette.asm').read_text(),out)
    (dest/'palette.asm').write_text(backend)
    (dest/'enemy.asm').write_text(absolute((out/'enemies.asm').read_text(),out))
    (dest/'prepare.inc').write_text((out/'enemy_prepare.inc').read_text())
    sprite=(root/'outputs/graphics/sprites-fast.inc').read_text()
    sprite=sprite.replace('original_sprite_catalog:\n    INCBIN "sprite-patterns.bin"',
                          'original_sprite_catalog EQU $-1504\n    INCBIN "sprite-patterns.bin",1504')
    sprite=absolute(sprite,root/'outputs/graphics')
    sprite+='\ntia_to_tms EQU original_tia_to_tms\n'
    (dest/'sprites.asm').write_text(sprite)
    tables=(root/'outputs/presentation/palette-tables.inc').read_text()
    tables=re.sub(r'^palette_(?:forecast_tick|forecast_apply|current_field)_banked EQU .*\n','',tables,flags=re.M)
    tables=tables.replace('palette_mask_groups EQU $9C00', '')
    tables=tables.replace('INCBIN "palette-locations.bin"','INCLUDE "'+str(dest/'locations.inc')+'"')
    tables=absolute(tables,root/'outputs/presentation')
    (dest/'tables.inc').write_text(tables)
    locations=[]
    for i in range(196):
        name,offset=('palette_records_high',i*17) if i<180 else ('palette_records_low',(i-180)*17)
        locations += [f'    DW {name}+{offset}','    DB 0']
    (dest/'locations.inc').write_text('\n'.join(locations)+'\n')
    records=(root/'outputs/presentation/palette-bank6.bin').read_bytes()[:196*17]
    (dest/'records.bin').write_bytes(records)
    forecast=(root/'outputs/presentation/palette-forecast.asm').read_text()
    forecast=re.sub(r'^    ORG .*\n','',forecast)
    forecast=forecast.replace('    ASSERT $ <= $C000','')
    forecast=absolute(forecast,root/'outputs/presentation')
    lookup=(root/'outputs/presentation/palette-program-lookup.bin').read_bytes()
    labels=json.loads((root/'outputs/presentation/hud-tables.json').read_text())['labels']
    labels={k:int(v,16) for k,v in labels.items()}
    groups=(('hud_pairs','hud_single',3),('hud_single','hud_blank_pair',3),
            ('hud_blank_pair','hud_lives',3),('hud_lives','hud_pairs1',9),
            ('hud_lives1','hud_divers',9),('hud_divers','hud_logo',18),
            ('hud_logo','hud_oxygen_label',9),('hud_oxygen_label','hud_oxygen',6),
            ('hud_oxygen','hud_background_names',13))
    keys={p-0xd000:lookup[p-0xd000] for a,b,stride in groups for p in range(labels[a],labels[b],stride)}
    buckets={i:[] for i in range(64)}
    for address,value in keys.items(): buckets[address&63].append((address>>6,value))
    rng=random.Random(35)
    for attempt in range(1000):
        slots=[None]*256;disps=[0]*64
        order=sorted(buckets,key=lambda k:(-len(buckets[k]),rng.random()))
        for bucket in order:
            if not buckets[bucket]: continue
            choices=[]
            for delta in range(256):
                positions=[((q+delta)&255,value) for q,value in buckets[bucket]]
                if all(slots[p] in (None,v) for p,v in positions):
                    choices.append((sum(slots[p] is None for p,v in positions),delta,positions))
            if not choices: break
            _,delta,positions=min(choices,key=lambda item:item[:2])
            disps[bucket]=delta
            for p,v in positions: slots[p]=v
        else: break
    else: raise ValueError('field hash packing failed')
    table=bytes(0 if v is None else v for v in slots)
    assert all(table[((p>>6)+disps[p&63])&255]==v for p,v in keys.items())
    (dest/'lookup.bin').write_bytes(table)
    (dest/'displacements.bin').write_bytes(bytes(disps))
    forecast=forecast.replace('    INCBIN "'+str(root/'outputs/presentation/palette-program-lookup.bin')+'"',
                              '    INCBIN "'+str(dest/'lookup.bin')+'"\nforecast_hash_displacements:\n    INCBIN "'+str(dest/'displacements.bin')+'"')
    first=forecast.index('forecast_dynamic_writers:\n');last=forecast.index('forecast_program_0:\n',first)
    words=[int(v.strip()) for line in forecast[first:last].splitlines() if ' DW ' in line for v in line.split('DW ',1)[1].split(',')]
    assert len(words)==256 and all(v==0 for i,v in enumerate(words) if 1<=i<185 or i>250)
    forecast=forecast[:first]+'forecast_dynamic_zero:\n    DW '+str(words[0])+'\nforecast_dynamic_writers:\n    DW '+','.join(map(str,words[185:251]))+'\n'+forecast[last:]
    fore_code=(root/'src/palette_forecast.asm').read_text()
    for name in ('palette_forecast_tick','palette_forecast_apply'):
        fore_code=fore_code.replace(name,name+'_banked')
    old='    LD DE,forecast_lookup\n    ADD HL,DE\n    LD L,(HL)\n    LD H,0\n'
    fore_code=fore_code.replace(old,'    CALL forecast_lookup_program\n')
    dyn='    LD L,A\n    LD H,0\n    ADD HL,HL\n    LD DE,forecast_dynamic_writers\n    ADD HL,DE\n    LD E,(HL)\n    INC HL\n    LD D,(HL)\n'
    fore_code=fore_code.replace(dyn,'    CALL forecast_dynamic_writer\n')
    (dest/'forecast-code.asm').write_text(fore_code)
    curr=(out/'current_fields.asm').read_text().replace('palette_current_field:', 'palette_current_field_banked:')
    curr=curr.replace(old,'    CALL forecast_lookup_program\n').replace(dyn,'    CALL forecast_dynamic_writer\n')
    (dest/'current-fields.asm').write_text(curr)
    forecast=forecast.replace(str(root/'src/palette_forecast.asm'),str(dest/'forecast-code.asm'))
    forecast=forecast.replace(str(out/'current_fields.asm'),str(dest/'current-fields.asm'))
    forecast+='\n    INCLUDE "'+str(out/'lookups.asm')+'"\n'
    (dest/'forecast.asm').write_text(forecast)
    source=(out/'main.asm').read_text()
    for token in ('render','hud','input','audio','palette','enemy','video'):
        source=source.replace('@'+token+'@',str(dest/(token+'.asm')))
    source=source.replace('@tables@',str(dest/'tables.inc'))
    source=absolute(source,out)
    enemy_colors=(root/'outputs/presentation/enemy-colors.inc').read_text()
    split=enemy_colors.index('enemy_top_ids:')
    init=enemy_colors.index('hud_enemy_init:')
    addresses=re.findall(r'    LD DE,\$([0-9A-Fa-f]+)\n    CALL hud_fill48',enemy_colors[init:])
    assert len(addresses)==56
    compact='''hud_enemy_init:
    LD IX,enemy_initial_addresses
    LD IY,enemy_normal_rgba
    LD C,ENEMY_SLOT_COUNT
.slot:
    LD B,8
.block:
    LD E,(IX+0)
    LD D,(IX+1)
    INC IX
    INC IX
    LD A,(IY+0)
    CALL hud_fill48
    DJNZ .block
    INC IY
    DEC C
    JR NZ,.slot
    RET
enemy_initial_addresses:
    DW '''+','.join('$'+v for v in addresses)+'\n'
    (dest/'enemy-colors.asm').write_text(enemy_colors[split:init]+compact)
    source='    INCLUDE "'+str(dest/'prepare.inc')+'"\n    INCLUDE "'+str(root/'outputs/presentation/hud.inc')+'"\n'+enemy_colors[:split]+'\n    ORG $0100\nnative_static_start:\nnative_entry:\n    DI\n    JP native_init\n'+source
    source+='''
native_prefix_end:
    ALIGN 16
native_writers_start:
'''
    for file in ('palette-writers.inc',):
        source+='    INCLUDE "'+str(root/'outputs/presentation'/file)+'"\n'
    pal_enemy=(root/'src/palette_enemy.asm').read_text()
    pal_enemy,part=extract(pal_enemy,'palette_enemy_init:\n',"; The opposite player's font")
    cold+='\n'+part
    (dest/'palette-enemy.asm').write_text(absolute(pal_enemy,root/'src'))
    source+='    INCLUDE "'+str(dest/'palette-enemy.asm')+'"\n'
    source+='    INCLUDE "'+str(root/'outputs/presentation/palette-generations.inc')+'"\n'
    source+='palette_default:\n    INCBIN "'+str(root/'outputs/presentation/palette-default.bin')+'"\n'
    source+='    INCLUDE "'+str(root/'outputs/presentation/palette-default-bases.inc')+'"\n'
    source+='    INCLUDE "'+str(dest/'enemy-colors.asm')+'"\n'
    source+='    INCLUDE "'+str(root/'outputs/native/core.inc')+'"\n'
    source+='    ALIGN 256\noriginal_rom EQU $-$C00\n    INCBIN "'+str(root/'outputs/native/original.rom')+'",$C00,$400\n'
    audio=absolute((root/'outputs/presentation/audio-tables.inc').read_text(),root/'outputs/presentation')
    source+=audio+'\n    ALIGN 256\ncolumn_lut:\n    INCBIN "'+str(root/'outputs/render/columns.bin')+'",0,160\n'
    source+='    ALIGN 256\nexpand_lut:\n    INCBIN "'+str(root/'outputs/collision/enemy-cache.bin')+'"\n'
    source+='    INCLUDE "'+str(dest/'sprites.asm')+'"\n'
    source+='    INCLUDE "'+str(dest/'forecast.asm')+'"\n'
    source+='palette_records_low:\n    INCBIN "'+str(dest/'records.bin')+'",3060,272\nnative_static_end:\n'
    source+='    ORG $F000\nnative_cold_start:\n'+cold+'\nnative_cold_end:\n'
    source+='    ORG $F400\nnative_high_start:\npalette_records_high:\n    INCBIN "'+str(dest/'records.bin')+'",0,3060\nnative_high_end:\n'
    (dest/'flat.asm').write_text(source)

def main():
    identity=fingerprint(root)
    dirty=subprocess.check_output(['git','status','--porcelain','--','src','scripts','Makefile','references/tools-lock.json'],cwd=root,text=True).strip()
    revision=None if dirty else subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    # The shared asset generators use outputs/presentation and outputs/native.
    # Match render_bench's lock ordering and retain locks through packaging.
    locks=[]
    for directory in ('render','native'):
        folder=root/'outputs'/directory
        folder.mkdir(exist_ok=True,parents=True)
        lock=(folder/'.lock').open('w')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks.append(lock)
    from render_tables import generate as render_generate
    from original_graphics import generate as graphics_generate, build_sprite_bank
    from collision_reference import generate as collision_generate
    from enemy_patterns import generate as enemy_generate
    from audio_reference import generate as audio_generate
    from core_codegen import main as core_generate
    render_generate()
    graphics_generate()
    build_sprite_bank()
    collision_generate()
    enemy_generate(True)
    audio_generate()
    if core_generate():
        raise ValueError('native reference generation failed')
    writerbase=0x4000
    for iteration in range(4):
        generate(writerbase)
        sources()
        verify_no_mapper(dest/'flat.asm')
        with (dest/'build.log').open('w') as log:
            subprocess.run([str(root/'.tools/sjasmplus/sjasmplus'),'--nologo',
                            '--raw='+str(dest/'flat.raw'),'--sym='+str(dest/'flat.sym'),
                            *('-D'+s for s in ('WITH_NATIVE','WITH_GRAPHICS','WITH_INPUT','WITH_COLLISIONS','WITH_STREAM','WITH_PACKED_DATA','WITH_HUD','WITH_AUDIO','WITH_PALETTE','WITH_BANKED')),
                            str(dest/'flat.asm')],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
        symbols={n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',(dest/'flat.sym').read_text(),re.M)}
        if symbols['native_writers_start']==writerbase: break
        writerbase=symbols['native_writers_start']
    else:
        raise ValueError('flat writer layout did not converge')
    report={n:hex(symbols[n]) for n in ('native_static_start','native_prefix_end','native_writers_start','native_static_end','native_cold_start','native_cold_end','native_high_start','native_high_end')}
    report['static_overflow_bytes']=max(0,symbols['native_static_end']-0xc000)
    report['cold_overflow_bytes']=max(0,symbols['native_cold_end']-0xf300)
    resolved={n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',(root/'outputs/presentation/palette-writers.sym').read_text(),re.M)}
    verify_writer_map(symbols,resolved)
    verify_layout(symbols)
    (dest/'layout.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_identity'}),flush=True)
    if report['static_overflow_bytes'] or report['cold_overflow_bytes']:
        raise SystemExit(1)
    raw=(dest/'flat.raw').read_bytes()
    memory=bytearray(65536)
    offset=0
    for first,last in (('native_static_start','native_static_end'),('native_cold_start','native_cold_end'),('native_high_start','native_high_end')):
        a,b=symbols[first],symbols[last]
        memory[a:b]=raw[offset:offset+b-a]
        offset+=b-a
    if offset!=len(raw): raise ValueError('flat raw segment accounting failed')
    hud=(root/'outputs/presentation/hud.bin').read_bytes()
    assert len(hud)==7168
    memory[0xd000:0xec00]=hud
    (dest/'flat.bin').write_bytes(memory)
    (dest/'resident.bin').write_bytes((root/'outputs/graphics/sprite-patterns.bin').read_bytes()[:1504])
    package_com(identity,revision)


def package_com(identity,revision):
    """Compress only after the final flat symbol map has converged."""
    from environment import prepare_checkout
    tool=root/'.tools/zx0'
    prepare_checkout(tool,'https://github.com/einar-saukas/ZX0.git',
                     'ecde3a2ae05061fe06469ed46df81a33b7de7d86')
    if not (tool/'zx0').exists():
        subprocess.run(['cc','-O2','-o',str(tool/'zx0'),
                        *(str(tool/'src'/f) for f in ('zx0.c','optimize.c','compress.c','memory.c'))],check=True)
    memory=(dest/'flat.bin').read_bytes()
    deltas={}
    for name,start,end in (('main',0x400,0xf300),('high',0xf400,0xfff4),('low',0x100,0x400)):
        (dest/f'{name}.bin').write_bytes(memory[start:end])
        if name=='low':
            continue
        result=subprocess.run([str(tool/'zx0'),'-f','-b',str(dest/f'{name}.bin')],
                              capture_output=True,text=True,check=True)
        deltas[name]=int(re.search(r'delta (\d+)',result.stdout)[1])
        if deltas[name]>0x400:
            raise ValueError('in-place decoder margin exceeded')
    payload=b''.join((dest/f).read_bytes() for f in ('resident.bin','low.bin','high.bin.zx0','main.bin.zx0'))
    checksum=sum(payload)&65535
    subprocess.run([str(root/'.tools/sjasmplus/sjasmplus'),'--nologo',
                    '--raw='+str(dest/'SEAQUEST.COM'),'--sym='+str(dest/'loader.sym'),
                    f'-DPAYLOAD_SUM={checksum}',str(out/'loader.asm')],check=True)
    shutil.copyfile(dest/'flat.sym',dest/'SEAQUEST.sym')
    data=(dest/'SEAQUEST.COM').read_bytes()
    report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),payload_sum16=checksum,
                runtime_sha256=hashlib.sha256(memory).hexdigest(),zx0_delta=deltas,
                source_identity=identity,source_revision=revision,
                runtime='unexpanded MSX1 64 KiB RAM / 16 KiB VRAM; DOS1 full-RAM takeover; reset to exit')
    verify_source(root,identity)
    (dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_identity'}),flush=True)
    package_rom(report)


def package_rom(com_report):
    subprocess.run([str(root/'.tools/sjasmplus/sjasmplus'),'--nologo',
                    '--raw='+str(dest/'SEAQUEST32.ROM'),'--sym='+str(dest/'plain32-loader.sym'),
                    str(out/'plain32.asm')],check=True)
    data=(dest/'SEAQUEST32.ROM').read_bytes()
    if len(data)!=32768:
        raise ValueError('plain cartridge is not exactly 32768 bytes')
    shutil.copyfile(dest/'flat.sym',dest/'SEAQUEST32.sym')
    verify_source(root,com_report['source_identity'])
    com_report['plain_rom']=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),mapper='Normal, fixed 4000..BFFF')
    (dest/'manifest.json').write_text(json.dumps(com_report,indent=2)+'\n')

if __name__=='__main__': main()
