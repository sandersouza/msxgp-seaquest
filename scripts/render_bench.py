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
    signature.extend(vram[0x3800:0x3900])
    return signature


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
    parser.add_argument('--build-only', action='store_true',help='assemble the probe without running openMSX')
    args = parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    lock = (OUT/'.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    if args.native:
        (ROOT/'outputs/native').mkdir(parents=True,exist_ok=True)
        native_lock = (ROOT/'outputs/native/.lock').open('w')
        fcntl.flock(native_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    generate()
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
    subprocess.run([str(ROOT/'.tools/sjasmplus/sjasmplus'), '--nologo',
                    '--raw='+str(OUT/'bench.rom'), '--sym='+str(OUT/'bench.sym'),
                    *(['-DWITH_NATIVE'] if args.native else []),
                    str(ROOT/'src/render_bench.asm')], cwd=ROOT, check=True)
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)', (OUT/'bench.sym').read_text(), re.M)}
    if args.build_only:
        variant = 'native' if args.native else 'synthetic'
        shutil.copyfile(OUT/'bench.rom',OUT/(variant+'.rom'))
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
    (OUT/'cases.bin').write_bytes(b''.join(struct.pack('<HBBBB',symbols.get(f'core_{entry:04X}',0),a,x,y,c)+ram for ram,(entry,a,x,y,c) in zip(cases,entries)))
    (OUT/'start.tcl').write_text(f'set inject_pixel {int(os.environ.get("SEAQUEST_RENDER_INJECT_PIXEL","-1"))}\nset rpc_start {symbols["rpc_start"]}\nset rpc_done {symbols["rpc_done"]}\nset commit_pc {symbols["render_commit"]}\nsource scripts/render_bench.tcl\n')
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
                  status='renderer feasibility probe; synthetic sprites/HUD, no playable or physical-hardware acceptance')
    if report['io']['min_data_spacing'] < 29: raise ValueError('unsafe VRAM transfer spacing')
    worst = cycles.index(max(cycles))
    (OUT/'worst-case.bin').write_bytes(cases[worst])
    (OUT/'pace-start.tcl').write_text(''.join(f'set {n} {symbols[n]}\n' for n in ('paced_commit','paced_frame_start','paced_prepared','vblank_sample','vblank_clear_sample'))+'source scripts/render_pace.tcl\n')
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
    variant = 'native' if args.native else 'synthetic'
    shutil.copyfile(OUT/'bench.rom',OUT/(variant+'.rom'))
    shutil.copyfile(OUT/'bench.sym',OUT/(variant+'.sym'))
    (OUT/('native-result.json' if args.native else 'synthetic-result.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
