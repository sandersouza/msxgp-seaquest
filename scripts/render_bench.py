#!/usr/bin/env python3
"""Execute the SCREEN 2 renderer on a standard MSX1 and compare actual VRAM."""
import hashlib
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import struct
import shutil
import platform

from render_tables import generate, sprite_peak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/render'
SHAPE = bytes.fromhex('18 3c 7e ff db ff 7e 3c 7e db ff 7e 3c 18 08')


def expected_pixels(ram, rom=None):
    pixels = bytearray(256*192)
    for lane in range(4):
        shape = SHAPE
        if rom:
            kind = ram[0xd9+lane] & 7
            offset = rom[0xfa2+kind] + (ram[0xdd] if kind < 4 else 0)
            shape = rom[0xd00+offset:0xd00+offset+15]
        base = ram[0x9e+lane]
        for copy in range(3):
            if not ram[0xa4+lane] & (4 >> copy):
                continue
            x = (base + copy*16) & 255
            if x >= 160:
                continue
            for y, value in enumerate(reversed(shape)):
                for bit in range(8):
                    source_bit = bit if ram[0xd9+lane] & 8 else 7-bit
                    if value & (1 << source_bit):
                        for dx in range(8+(x+bit)*3//2, 8+(x+bit+1)*3//2):
                            if 8 <= dx < 248:
                                pixels[(48+24*(3-lane)+y)*256+dx] = 1
    return pixels


def decode(vram):
    pixels = bytearray(256*192)
    for y in range(192):
        for column in range(32):
            tile = vram[0x1800+(y//8)*32+column]
            value = vram[(y//64)*2048+tile*8+y%8]
            for bit in range(8):
                pixels[y*256+column*8+bit] = (value >> (7-bit)) & 1
    return pixels


def visible_signature(vram):
    signature = bytearray(vram[0x1800:0x1b20])
    for bank in range(3):
        for tile in set(vram[0x1800+bank*256:0x1900+bank*256]):
            start = bank*2048+tile*8
            signature.extend(vram[start:start+8])
            signature.extend(vram[start+8192:start+8200])
    for slot in range(8):
        pattern = vram[0x1b00+slot*4+2] & 252
        signature.extend(vram[0x3800+pattern*8:0x3820+pattern*8])
    return signature


def check_original_sprites(ram,vram,assets,rom):
    from original_graphics import early_patrol, scale_rows
    from graphics_palette import sprite_colors
    actual = set()
    ys = []
    for slot in range(8):
        y,x,pattern,color = vram[0x1b00+slot*4:0x1b04+slot*4]
        y = (y+1)&255
        ys.append(y)
        if not color & 15: raise ValueError('transparent original sprite color')
        for row in range(16):
            for column in range(16):
                value = vram[0x3800+(pattern&252)*8+(column//8)*16+row]
                if value & (128>>(column%8)) and x+column<256 and y+row<192:
                    actual.add((x+column,y+row,slot))
    frame = ram[0xe0] if ram[0xe0]<3 else 0
    reflect = int(bool(ram[0xd6]&8))
    player = (f'explosion-{max(ram[0xe9],10)}-{reflect}' if 0<ram[0xe9]<15
              else f'player-{frame}-{reflect}')
    expected = set()
    objects = [(player,ram[0xc6],ram[0xe1]+17,0, bool(ram[0xe1])),
               ('torpedo',ram[0xe7],ram[0xe1]+24,2,ram[0xe1]>=17 and ram[0xe7]!=0)]
    objects += [(f'ball-{ram[0xd9+lane]&15}',ram[0xc7+lane],120-lane*24,3+lane,
                 ram[0xc7+lane]!=0) for lane in range(4)]
    patrol_prefix = 'early-patrol' if early_patrol(ram) else 'patrol'
    objects += [(f'{patrol_prefix}-{frame}',ram[0xf6],30,7,ram[0xf6]!=0)]
    for name,x,y,slot,enabled in objects:
        if not enabled or x>=160: continue
        for row, pixels in enumerate(scale_rows(assets[name]['rows'],x)):
            if slot==0 and 37 <= y+row <= 40: continue
            for px in pixels:
                part = int(px >= 8+x*3//2+16) if slot==0 else 0
                if 0 <= y+row < 192: expected.add((px,y+row,slot+part))
    if actual != expected:
        raise ValueError(f'original sprite pixel mismatch: extra={list(actual-expected)[:3]}, missing={list(expected-actual)[:3]}')
    if vram[0x1b20]!=208 or sprite_peak(ys)>4:
        raise ValueError('original sprite terminator/scanline budget exceeded')
    if list(vram[0x1b03:0x1b20:4]) != sprite_colors(ram,rom):
        raise ValueError('original sprite palette selection mismatch')


def check_sprites(ram,vram):
    scale = lambda x: (8+x*3//2)&255
    player = (ram[0xe1]+16)&255
    positions = [(player,scale(ram[0xc6])),(player,(scale(ram[0xc6])+16)&255),
                 ((player+5)&255,scale(ram[0xe7]))]
    positions += [(120-24*lane,scale(ram[0xc7+lane])) for lane in range(4)]
    positions += [(21,scale(ram[0xf6]))]
    expected = bytes(v for n,(y,x) in enumerate(positions) for v in (y,x,n*4,15-n))
    if vram[0x1b00:0x1b20] != expected or vram[0x1b20] != 208:
        raise ValueError('sprite attributes or terminator mismatch')
    if sprite_peak([y+1 for y,x in positions]) > 4:
        raise ValueError('hardware sprite occupancy exceeded')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--graphics', action='store_true',help='local original sprite integration, includes native core')
    parser.add_argument('--input', action='store_true',help='measure real BIOS input at original sample phase, with graphics')
    parser.add_argument('--controls', action='store_true',help='build an automatically running controls diagnostic')
    parser.add_argument('--collisions', action='store_true',help='acquire original raster contacts before the native update')
    parser.add_argument('--oxygen', action='store_true',help='include the issue #11 oxygen/rescue workload')
    parser.add_argument('--progression', action='store_true',help='include score/lives/late-game progression and oxygen workloads')
    parser.add_argument('--input-synthetic', action='store_true',help='assemble the input adapter without original inputs (CI)')
    parser.add_argument('--build-only', action='store_true',help='assemble the probe without running openMSX')
    args = parser.parse_args()
    args.oxygen = args.oxygen or args.progression
    args.collisions = args.collisions or args.controls or args.oxygen
    args.input = args.input or args.controls or args.collisions
    args.graphics = args.graphics or args.input
    args.native = args.native or args.graphics
    OUT.mkdir(parents=True,exist_ok=True)
    lock = (OUT/'.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    if args.native:
        (ROOT/'outputs/native').mkdir(parents=True,exist_ok=True)
        native_lock = (ROOT/'outputs/native/.lock').open('w')
        fcntl.flock(native_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    generate()
    assets = None
    if args.graphics:
        from original_graphics import generate as graphics_generate
        assets,_,_ = graphics_generate()
    if args.collisions:
        from collision_reference import generate as collision_generate
        collision_generate()
    rom = None
    cases = []
    entries = []
    reference_states = []
    case_names = []
    if args.native:
        from core_codegen import main as core_generate
        from native_contract import fixtures, reference
        if core_generate(): raise ValueError('native generation failed')
        rom = (ROOT/'outputs/native/original.rom').read_bytes()
        for item in fixtures():
            name,entry,ram,a,x,y,carry = item[:7]
            if entry != 0xf5b8: continue
            expected,_ = reference(rom, list(ram),entry,a,x,y,carry)
            cases.append(ram)
            entries.append((entry,a,x,y,carry))
            reference_states.append(expected)
            case_names.append(name)
        template = bytearray(cases[150])
        for x in range(256):
            for mask in range(8):
                ram = bytearray(template)
                ram[0x9e:0xa2] = bytes([x]*4)
                ram[0xa4:0xa8] = bytes([mask]*4)
                ram[0xd9:0xdd] = bytes([8*(x&1)]*4)
                ram[0x81] = (x*13+mask)&255
                expected,_ = reference(rom,list(ram),0xf5b8,0,0x82)
                cases.append(ram)
                entries.append((0xf5b8,0,0x82,0,0))
                reference_states.append(expected)
                case_names.append(f'dense-{x}-{mask}')
        if args.graphics:
            for x in range(145,160):
                for kind in range(16):
                    ram = bytearray(template)
                    ram[0x9e:0xa2] = bytes([64]*4)
                    ram[0xa4:0xa8] = bytes([7]*4)
                    ram[0xc7:0xcb] = bytes([x]*4)
                    ram[0xd9:0xdd] = bytes([kind]*4)
                    ram[0xe7],ram[0xf6] = x,x
                    ram[0x81] = 2
                    expected,_ = reference(rom,list(ram),0xf5b8,0,0x82)
                    cases.append(ram)
                    entries.append((0xf5b8,0,0x82,0,0))
                    reference_states.append(expected)
                    case_names.append(f'graphics-edge-{x}-{kind}')
            # Independent lane shapes/edge phases; do not assume four balls
            # share an animation, position or VRAM image.
            import random
            rng = random.Random(8)
            for n in range(2048):
                ram = bytearray(template)
                ram[0x9e:0xa2] = bytes([64]*4)
                ram[0xa4:0xa8] = bytes([7]*4)
                ram[0xc7:0xcb] = bytes(rng.randrange(150,160) for _ in range(4))
                ram[0xd9:0xdd] = bytes(rng.randrange(16) for _ in range(4))
                ram[0xe7],ram[0xf6] = rng.randrange(150,160),rng.randrange(150,160)
                ram[0x81] = rng.randrange(256)
                if n>=1024:
                    ram[0xe1] = 13+rng.randrange(96)
                    ram[0xc6] = rng.randrange(21,135)
                    if n%4==0: ram[0xe9] = rng.randrange(1,24)
                expected,_ = reference(rom,list(ram),0xf5b8,0,0x82)
                cases.append(ram)
                entries.append((0xf5b8,0,0x82,0,0))
                reference_states.append(expected)
                case_names.append(f'graphics-mixed-{n}')
    if args.collisions:
        from collision_contract import scenarios as collision_scenarios
        import itertools
        for n,(name,changes) in enumerate(itertools.islice(collision_scenarios(),1024)):
            ram = bytearray(cases[150])
            for address,value in changes.items(): ram[int(address,16)] = value
            ram[0xa4:0xa8] = bytes([7]*4)
            ram[0xe8],ram[0xe6],ram[0xa3],ram[0xbd],ram[0x81] = 0,64,0,n&255,n&255
            cases.append(ram)
            entries.append((0xf5b8,0,0x82,0,0))
            case_names.append('collision-full-'+name)
        # Earlier renderer probes deliberately include unused frame3/7 pointers.
        # Keep their density/positions while selecting reachable source frames.
        for ram in cases:
            for lane in range(4):
                if ram[0xd9+lane]&7 in (3,7): ram[0xd9+lane] ^= 1
    if args.input:
        # The emulator has neutral physical devices in this exhaustive renderer
        # pass. Dedicated input replays exercise natural controls separately.
        for ram in cases:
            ram[0x280],ram[0x282],ram[0x0c],ram[0x0d] = 255,63,128,128
            ram[0xb0:0xb7],ram[0xf8] = bytes([255]*7),0
        input_controls = [(0,0,0,63)]*len(cases)
        from input_contract import hardware
        dense = [cases[case_names.index(f'graphics-mixed-{n}')] for n in (708,109,411,615)]
        variants = [(ram,None,None,None) for ram in dense]
        variants += [(dense[0],y,shot,facing) for y in (13,17,18,20,108)
                     for shot in (0,153) for facing in (0,8)]
        for variant,(base,y,shot,facing) in enumerate(variants):
            for keys in range(16):
                for fire in range(2):
                    for switches in (63,127,191,255):
                        ram = bytearray(base)
                        if y is not None:
                            ram[0xe1],ram[0xe7],ram[0xd6] = y,shot,facing
                            ram[0xe8],ram[0xe6],ram[0xe9],ram[0xa3] = 0,64,0,0
                        row8 = ((keys&1)<<5)|((keys&2)<<5)|((keys&4)<<2)|((keys&8)<<4)|fire
                        ports,console,f1,f2,_,_ = hardware((0,0,row8,0,0),ram[0xb7],switches,0)
                        ram[0x280],ram[0x282],ram[0xc],ram[0xd] = ports,console,f1,f2
                        cases.append(ram)
                        entries.append((0xf5b8,0,0x82,0,0))
                        case_names.append(f'controls-dense-{variant}-{keys}-{fire}-{switches}')
                        input_controls.append((0,0,row8,switches))
        if args.oxygen:
            oxygen_start = len(cases)
            from oxygen_contract import transition_cases
            for name,ram,keys in transition_cases(rom):
                cases.append(ram)
                entries.append((0xf5b8,0,0x82,0,0))
                case_names.append('oxygen-'+name)
                input_controls.append((0,0,keys,63))
            # Low oxygen with the same full-density clipped source shapes as
            # the previous worst workload; retain every object and transfer.
            import itertools
            for base,oxygen,phase,state,groups in itertools.product(
                    dense,(1,15,16,17,63),(0,15,16,31,255),(0,1,6),(0,19,255)):
                ram = bytearray(base)
                ram[0xe6],ram[0x81],ram[0xe8],ram[0xe9],ram[0xa3] = oxygen,phase,state,0,0
                ram[0xbc] = groups
                cases.append(ram)
                entries.append((0xf5b8,0,0x82,0,0))
                case_names.append(f'oxygen-dense-{len(cases)}')
                input_controls.append((0,0,65,63))
        if args.progression:
            progression_start = len(cases)
            from progression_contract import transition_cases
            for name,ram,keys,switches in transition_cases(rom):
                cases.append(ram)
                entries.append((0xf5b8,0,0x82,0,0))
                case_names.append('progression-'+name)
                input_controls.append((0,0,keys,switches))
            for base,groups,oxygen,value,reserve in itertools.product(
                    dense,(6,18,19,20,253,254,255),(0,1,64),(9990,999990),(0,5,6)):
                from progression_contract import bcd
                ram = bytearray(base)
                ram[0xbc],ram[0xe6],ram[0xe8],ram[0x81],ram[0xbe] = groups,oxygen,6,15,6
                ram[0xe9],ram[0xa3],ram[0xbb] = 0,0,reserve
                ram[0xb8:0xbb] = bcd(value)
                cases.append(ram)
                entries.append((0xf5b8,0,0x82,0,0))
                case_names.append(f'progression-dense-{len(cases)}')
                input_controls.append((0,0,65,63))
        reference_states = []
        for ram,entry,controls in zip(cases,entries,input_controls):
            sampled = bytearray(ram)
            if args.collisions:
                from oxygen_reference import acquire
                sampled = acquire(ram,rom,assets)
            r6,r7,r8,switches = controls
            sampled[0x280],sampled[0x282],sampled[12],sampled[13],_,_ = hardware(
                (r6,r7,r8,0,0),ram[0xb7],switches,0)
            reference_states.append(reference(rom,list(sampled),*entry)[0])
    subprocess.run([str(ROOT/'.tools/sjasmplus/sjasmplus'), '--nologo',
                    '--raw='+str(OUT/'bench.rom'), '--sym='+str(OUT/'bench.sym'),
                    *(['-DWITH_NATIVE'] if args.native else []),
                    *(['-DWITH_GRAPHICS'] if args.graphics else []),
                    *(['-DWITH_INPUT'] if args.input or args.input_synthetic else []),
                    *(['-DWITH_COLLISIONS'] if args.collisions else []),
                    *(['-DCOLLISION_CORRUPT'] if args.collisions and os.environ.get('SEAQUEST_COLLISION_CORRUPT')=='1' else []),
                    *(['-DOXYGEN_CORRUPT'] if args.collisions and os.environ.get('SEAQUEST_OXYGEN_CORRUPT')=='1' else []),
                    *(['-DINPUT_CORRUPT_PORT2'] if args.input and os.environ.get('SEAQUEST_INPUT_CORRUPT_PORT2')=='1' else []),
                    *(['-DCONTROL_DEMO'] if args.controls else []),
                    str(ROOT/'src/render_bench.asm')], cwd=ROOT, check=True)
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)', (OUT/'bench.sym').read_text(), re.M)}
    if args.build_only:
        variant = 'synthetic-input' if args.input_synthetic else ('controls' if args.controls else ('collisions' if args.collisions else ('input' if args.input else ('graphics' if args.graphics else ('native' if args.native else 'synthetic')))))
        shutil.copyfile(OUT/'bench.rom',OUT/(variant+'.rom'))
        shutil.copyfile(OUT/'bench.sym',OUT/(variant+'.sym'))
        manifest = {'rom':variant+'.rom','bytes':32768,'sha256':hashlib.sha256((OUT/'bench.rom').read_bytes()).hexdigest(),
                    'status':'renderer diagnostic only; no emulator acceptance'}
        (OUT/(variant+'-build.json')).write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(manifest))
        return
    for x in range(256) if not args.native else ():
        ram = bytearray(1024)
        ram[0x9e:0xa2] = bytes((x+lane*19)&255 for lane in range(4))
        ram[0xd9:0xdd] = bytes(8*((x+lane)&1) for lane in range(4))
        ram[0xa4:0xa8] = bytes([7]*4)
        ram[0xc6],ram[0xe1],ram[0xe7],ram[0xf6] = 70,13+x%94,100,65
        ram[0xc7:0xcb] = bytes([36,72,108,144])
        cases.append(ram)
        entries.append((0,0,0,0,0))
        case_names.append(f'position-{x}')
    (OUT/'cases.bin').write_bytes(b''.join(struct.pack('<HBBBB',symbols.get(f'core_{entry:04X}',0),a,x,y,c)+
                                          (bytes(input_controls[i]) if args.input else b'')+ram
                                          for i,(ram,(entry,a,x,y,c)) in enumerate(zip(cases,entries))))
    (OUT/'start.tcl').write_text(f'set input_mode {int(args.input)}\nset inject_pixel {int(os.environ.get("SEAQUEST_RENDER_INJECT_PIXEL","-1"))}\nset rpc_start {symbols["rpc_start"]}\nset rpc_done {symbols["rpc_done"]}\nset commit_pc {symbols["render_commit"]}\nsource scripts/render_bench.tcl\n')
    (OUT/'complete.txt').unlink(missing_ok=True)
    with (OUT/'openmsx.log').open('wb') as log:
        result = subprocess.run(['openmsx', '-control','stdio','-machine','C-BIOS_MSX1',
                                 '-cart',str(OUT/'bench.rom'),'-script',str(OUT/'start.tcl')],
                                cwd=ROOT, env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                                stdout=log,stderr=subprocess.STDOUT,timeout=60)
    if result.returncode or not (OUT/'complete.txt').exists() or int((OUT/'complete.txt').read_text()) != len(cases):
        raise ValueError('renderer harness incomplete; see outputs/render/openmsx.log')
    dumps = (OUT/'vram.bin').read_bytes()
    states = (OUT/'state.bin').read_bytes()
    prepared = (OUT/'prepared.bin').read_bytes()
    if len(dumps) != len(cases)*16384 or len(prepared) != len(dumps) or len(states) != len(cases)*1024:
        raise ValueError('truncated emulator evidence')
    for index,ram in enumerate(cases):
        if index and visible_signature(prepared[index*16384:(index+1)*16384]) != visible_signature(dumps[(index-1)*16384:index*16384]):
            raise ValueError(f'visible VRAM changed before VBlank commit in case {index}')
        ram = states[index*1024:(index+1)*1024]
        if args.native and ram[:251] != reference_states[index]:
            raise ValueError(f'native state mismatch in render case {index}')
        actual = decode(dumps[index*16384:(index+1)*16384])
        if args.graphics:
            check_original_sprites(ram,dumps[index*16384:(index+1)*16384],assets,rom)
        else:
            check_sprites(ram,dumps[index*16384:(index+1)*16384])
        expected = expected_pixels(ram,rom)
        if actual != expected:
            first = next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
            raise ValueError(f'case {index} pixel ({first%256},{first//256}): actual={actual[first]} expected={expected[first]}')
    cycles = [int(v) for v in (OUT/'cycles.txt').read_text().split()]
    if len(cycles) != len(cases): raise ValueError('incomplete cycle measurements')
    report = {'cases':len(cases),'max_cycles':max(cycles),'worst_case':case_names[cycles.index(max(cycles))],
              'rom_sha256':hashlib.sha256((OUT/'bench.rom').read_bytes()).hexdigest(),
              'io':json.loads((OUT/'io.json').read_text())}
    report.update(machine='C-BIOS_MSX1',cpu_hz=3579545,vdp='TMS9918A',ram_kib=64,vram_kib=16,
                  video='NTSC',rom_bytes=32768,python=platform.python_version(),
                  openmsx=subprocess.check_output(['openmsx','-v'],text=True).splitlines()[0],
                  sjasmplus_revision=subprocess.check_output(['git','-C',str(ROOT/'.tools/sjasmplus'),'rev-parse','HEAD'],text=True).strip(),
                  original_sha256=hashlib.sha256(rom).hexdigest() if rom else None,
                  status=('original sprite integration probe; synthetic HUD/background colors; no playable or physical-hardware acceptance'
                          if args.graphics else 'renderer feasibility probe; synthetic sprites/HUD, no playable or physical-hardware acceptance'))
    if args.input:
        report.update(status='controls integration diagnostic with neutral collision inputs; synthetic HUD/background colors; no full-game or physical-hardware acceptance',
                      input_sweep_cases=len(cases)-6526,
                      collision_inputs='isolated adapter regression: neutral B0..B6=FF/F8=0; the controls and collision targets acquire real contacts',
                      rom_padding_bytes=0xc000-symbols['original_rom']-4096,
                      cpu_margin_cycles=59736-max(cycles))
    if args.collisions:
        report.update(status='original collision/input/graphics integration; synthetic HUD/background; full-game and hardware unverified',
                      collision_inputs='original raster occupancy and F44F HUD alarm acquired before F5B8; original resolution order',
                      input_sweep_cases=len(variants)*128)
    if args.oxygen:
        report['oxygen_sweep_cases'] = len(cases)-oxygen_start
    if args.progression:
        report['progression_sweep_cases'] = len(cases)-progression_start
        report['oxygen_sweep_cases'] = progression_start-oxygen_start
    if report['io']['min_data_spacing'] < 29: raise ValueError('unsafe VRAM transfer spacing')
    worst = cycles.index(max(cycles))
    (OUT/'worst-case.bin').write_bytes(cases[worst])
    input_setup = ''
    if args.input:
        r6,r7,r8,switches = input_controls[worst]
        input_setup = f'keymatrixdown 6 {r6}\nkeymatrixdown 7 {r7}\nkeymatrixdown 8 {r8}\ndebug write memory 0xC420 {switches}\n'
    (OUT/'pace-start.tcl').write_text(''.join(f'set {n} {symbols[n]}\n' for n in ('paced_commit','paced_frame_start','paced_prepared','vblank_sample','vblank_clear_sample'))+
                                   'set input_setup {'+input_setup+'}\nsource scripts/render_pace.tcl\n')
    (OUT/'pace.json').unlink(missing_ok=True)
    with (OUT/'pace.log').open('wb') as log:
        result = subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-cart',str(OUT/'bench.rom'),'-script',str(OUT/'pace-start.tcl')],cwd=ROOT,
                                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=30)
    if result.returncode or not (OUT/'pace.json').exists(): raise ValueError('pacing failed; see outputs/render/pace.log')
    pace = json.loads((OUT/'pace.json').read_text())
    if pace['frames'] != 241 or any(b-a != 1 for a,b in zip(pace['frame_counts'],pace['frame_counts'][1:])): raise ValueError('missed display frame')
    if any(0 <= y < 192 for y in pace['commit_start_y']+pace['commit_end_y']): raise ValueError('visible commit outside VBlank')
    report['pace'] = {'frames':240,'min_period':min(pace['periods']),'max_period':max(pace['periods']),
                      'max_commit_cycles':max(pace['commit_cycles']),'max_busy_cycles':pace['max_busy_cycles'],
                      'stack_min':pace['stack_min'],'min_commit_y':min(pace['commit_start_y']),
                      'max_commit_end_y':max(pace['commit_end_y'])}
    if pace['max_busy_cycles'] >= 59736: raise ValueError('frame CPU budget exceeded')
    if max(cycles) >= 59736: raise ValueError('unpaced frame CPU budget exceeded')
    variant = 'collisions' if args.collisions else ('input' if args.input else ('graphics' if args.graphics else ('native' if args.native else 'synthetic')))
    shutil.copyfile(OUT/'bench.rom',OUT/(variant+'.rom'))
    shutil.copyfile(OUT/'bench.sym',OUT/(variant+'.sym'))
    (OUT/(variant+'-result.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
