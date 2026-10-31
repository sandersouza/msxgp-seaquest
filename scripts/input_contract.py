#!/usr/bin/env python3
"""Real MSX input-device replay versus the independent original CPU.

Expected device levels are not preloaded: full fixtures poison all four hardware
mirrors, then key matrix/MSXJoystick events supply input through the real BIOS.
Chained fixtures retain game RAM and update only devices/neutral collision inputs.
Original-derived ROMs, states and replay snapshots stay in ignored outputs.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import xml.etree.ElementTree as ET

from native_contract import reference
from reference_inventory import ROOT

OUT = ROOT / 'outputs/input'
MASTER_HZ = 3436363200  # NTSC Z80 3579545 Hz * serialized clock period 960


def run(script, rom, name, timeout=60, mapper=None):
    with (OUT / (name+'.log')).open('wb') as log:
        subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1',
                        '-cart',str(rom),*(['-romtype',mapper] if mapper else []),'-script',str(script)],cwd=ROOT,
                       env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,timeout=timeout,check=True)


def replay(seed, events, end, path):
    root = ET.fromstring(gzip.decompress(seed.read_bytes()))
    replay = root.find('replay')
    snapshots = replay.find('snapshots')
    for child in list(snapshots)[1:]:
        snapshots.remove(child)
    log = replay.find('events')
    log.clear()
    next_id = max(int(e.attrib['id']) for e in root.iter() if e.attrib.get('id','').isdigit())+1
    for time,kind,values in events + [(end,'EndLog',{})]:
        item = ET.SubElement(log,'item',id=str(next_id),type=kind)
        next_id += 1
        ET.SubElement(ET.SubElement(ET.SubElement(item,'StateChange'),'time'),'time').text = str(round(time*MASTER_HZ))
        for key,value in values.items():
            field = ET.SubElement(item,key)
            if isinstance(value,list):
                for token in value:
                    ET.SubElement(field,'item').text = token.decode('latin1') if isinstance(token,bytes) else str(token)
            else:
                field.text = str(value)
    replay.find('currentTime/time').text = '0'
    xml = ET.tostring(root,encoding='utf-8').replace(b'\0',b'\xc0\x80')
    # openMSX stores Tcl byte strings using modified UTF-8 (including NUL)
    # and numeric references for control bytes, as its own recorder does.
    for byte in range(1,32):
        if byte not in (9,10,13):
            xml = xml.replace(bytes([byte]),f'&#x{byte:02X};'.encode())
    path.write_bytes(gzip.compress(b'<?xml version="1.0"?>\n<!DOCTYPE serial SYSTEM "openmsx-serialize.dtd">\n'+xml))


def device_events(time, controls):
    row6,row7,row8,joy1,joy2 = controls
    return ([(time,'KeyMatrixState',dict(row=row,press=value,release=255^value))
             for row,value in ((6,row6),(7,row7),(8,row8))] +
            [(time,'MSXJoyState',dict(id=port,press=value,release=63^value))
             for port,value in ((1,joy1),(2,joy2))])


def hardware(controls, player, switches, previous):
    r6,r7,r8,j1,j2 = controls
    difficulty = ((r6&128)>>1) | ((r7&1)<<7)
    switches ^= difficulty & ~previous
    console = switches & (255 ^ ((r6>>5)&3))
    keys = 15 ^ (((r8>>5)&3) | ((r8>>2)&4) | ((r8>>4)&8))
    ports = ((15^(j1&15))<<4) | (15^(j2&15))
    ports &= (keys|240) if player else ((keys<<4)|15)
    fire = [0 if j&16 else 128 for j in (j1,j2)]
    if r8&1:
        fire[player] = 0
    return ports,console,*fire,switches,difficulty


def fixture_cases():
    base = bytearray(1024)
    base[0x81],base[0x82] = 2,87
    base[0x80],base[0xbb],base[0xc2] = 1,3,3
    base[0xe6] = 64
    base[0xb0:0xb7] = bytes([255]*7)
    cases = []
    # All 16 combinations, including diagonals/opposites, at every corner and
    # both firing thresholds; both players and both independent switch bits.
    for player in range(2):
        for switches in (63,127,191,255):
            for x,y in ((21,13),(134,13),(21,108),(134,108),(76,17),(76,18),(76,19),(76,20)):
                for keys in range(16):
                    for fire in range(2):
                        for source in ('keyboard','joystick'):
                            ram = bytearray(base)
                            ram[0xb7],ram[0xc6],ram[0xe1] = player,x,y
                            ram[0xd6] = 8*(keys&1)
                            mask = ((keys&1)<<5)|((keys&2)<<5)|((keys&4)<<2)|((keys&8)<<4)|fire
                            controls = (0,0,mask,0,0) if source=='keyboard' else (0,0,0,(keys|fire*16) if not player else 0,(keys|fire*16) if player else 0)
                            cases.append((f'{source}-p{player}-{switches}-{x}-{y}-{keys}-{fire}',ram,controls,switches))
    # Independent ports and keyboard union; never accept the other player's fire.
    for player in range(2):
        for first in range(32):
            ram = bytearray(base)
            ram[0xb7],ram[0xc6],ram[0xe1] = player,76,50
            cases.append((f'mixed-ports-{player}-{first}',ram,(0,0,0x11,first,31^first),63))
    original = (ROOT/'outputs/native/original.rom').read_bytes()
    for chain,(player,switches) in enumerate(((0,63),(0,127),(1,63),(1,191),(0,63))):
        console_chain = chain==4
        ram = bytearray(base)
        ram[0xb7],ram[0xc6],ram[0xe1] = player,76,50
        current,previous = switches,0
        for tick in range(300):
            controls = (0,0,0,16 if not player else 0,16 if player else 0)
            if console_chain:
                r6 = 64 if tick<36 else (32 if tick==50 else (128 if 60<=tick<100 or 160<=tick<190 else 0))
                controls = (r6,int(110<=tick<130),0,0,0)
            ram[0xb0:0xb7],ram[0xf8] = bytes([255]*7),0
            ports,console,f1,f2,current,previous = hardware(controls,ram[0xb7],current,previous)
            ram[0x280],ram[0x282],ram[0xc],ram[0xd] = ports,console,f1,f2
            cases.append((f'chain-{player}-{switches}-{tick}',bytearray(ram),controls,switches,int(tick>0)))
            expected,_ = reference(original,list(ram),0xf5b8,0,0x82)
            ram[:251] = expected
    return cases


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run(['make','controls'],cwd=ROOT,stdout=(OUT/'build.log').open('w'),stderr=subprocess.STDOUT,check=True)
    rom = ROOT/'outputs/render/controls.rom'
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',(ROOT/'outputs/render/controls.sym').read_text(),re.M)}
    # Seed serializes plugged standard MSX joysticks. Its original-derived
    # cartridge contents and emulator snapshots are never public artifacts.
    seed_script = OUT/'seed.tcl'
    seed_script.write_text('set renderer none\nset throttle off\nset power true\nplug joyporta msxjoystick1\nplug joyportb msxjoystick2\nreverse start\nafter time 1 {reverse savereplay outputs/input/seed.omr; exit}\n')
    run(seed_script,rom,'seed')
    original = (ROOT/'outputs/native/original.rom').read_bytes()
    cases = fixture_cases()
    events,records = [],[]
    current,previous = 63,0
    for i,case in enumerate(cases):
        name,ram,controls,switches = case[:4]
        chained = case[4] if len(case)>4 else 0
        if not chained:
            current,previous = switches,0
        time = 6+i*.01
        events += device_events(time,controls)
        ports,console,f1,f2,current,previous = hardware(controls,ram[0xb7],current,previous)
        ram[0x280],ram[0x282],ram[0xc],ram[0xd] = ports,console,f1,f2
        expected,_ = reference(original,list(ram),0xf5b8,0,0x82)
        # Poison all hardware mirrors in the target fixture. The actual sampler
        # must overwrite them; expected CPU results alone cannot pre-seed inputs.
        for address in (0x280,0x282,0xc,0xd):
            ram[address] ^= 255
        if not chained:
            events += [(time+.0002,'MSXCommandEvent',dict(tokens=['debug','write_block','memory','0xC000',bytes(ram)])),
                       (time+.0002,'MSXCommandEvent',dict(tokens=['debug','write_block','memory','0xC420',bytes([switches,0])]))]
        events += [(time+.0002,'MSXCommandEvent',dict(tokens=['debug','write_block','CPU regs','20',struct.pack('>H',symbols['input_rpc_start'])]))]
        records.append(bytes([switches])+ram+expected)
    (OUT/'cases.bin').write_bytes(b''.join(records))
    (OUT/'case-index.json').write_text(json.dumps([c[0] for c in cases]))
    replay(OUT/'seed.omr',events,7+len(cases)*.01,OUT/'cases.omr')
    start = OUT/'start.tcl'
    start.write_text(''.join(f'set {n} {symbols[n]}\n' for n in ('input_rpc_done','sample_input','idle'))+
                     f'set total_cases {len(cases)}\nset sample_input_return {symbols["core_F6A7"]+3}\n'+
                     'if {[catch {source scripts/input_contract.tcl} detail]} {puts stderr $detail; exit 1}\n')
    (OUT/'result.json').unlink(missing_ok=True)
    run(start,rom,'cases')
    result = json.loads((OUT/'result.json').read_text())
    if not result['passed'] or result['cases'] != len(cases):
        failed = cases[result['cases']][0] if result['cases']<len(cases) else 'completion'
        raise ValueError(f'input contract failed {failed}: {result}')
    result.update(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),rom_bytes=rom.stat().st_size,
                  machine='C-BIOS_MSX1',cpu_hz=3579545,ram_kib=64,vram_kib=16,video='NTSC',
                  openmsx=subprocess.check_output(['openmsx','-v'],text=True).splitlines()[0],
                  method='actual keyboard matrix and standard MSXJoystick device replay; full F5B8 to F00E original CPU comparison',
                  physical_hardware=False)
    actual = (OUT/'actual.bin').read_bytes()
    if len(actual) != len(cases)*251:
        raise ValueError('truncated native input state evidence')
    cadences = []
    for chain in range(4):
        first = 4160+chain*300
        shots = [actual[i*251+0xe7] for i in range(first,first+300)]
        births = [i for i,shot in enumerate(shots) if shot and (i==0 or not shots[i-1])]
        intervals = sorted({b-a for a,b in zip(births,births[1:])})
        cadences.append(dict(player=chain//2,setting='A' if chain&1 else 'B',ticks=300,
                             birth_ticks=births,intervals=intervals))
        if intervals != ([26] if chain&1 else [16]):
            raise ValueError(f'held-fire cadence mismatch: {cadences[-1]}')
    result['held_fire'] = cadences
    (OUT/'contract-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
