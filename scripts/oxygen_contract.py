#!/usr/bin/env python3
"""Omitted original HUD state and ordered rescue transitions on the real Z80."""
import fcntl
import hashlib
import itertools
import json
import os
import re
import subprocess

from input_contract import hardware
from native_contract import reference
from original_graphics import ROOT, extract, read_original
from oxygen_reference import acquire, alarm

OUT = ROOT/'outputs/oxygen'


def base_state(rom):
    ram = bytearray(1024)
    ram[0x82] = 87
    ram[:251] = reference(rom,list(ram),0xfb54)[0]
    ram[0xe8],ram[0xe6],ram[0xe1],ram[0xa3] = 0,64,50,0
    ram[0x9e:0xa2],ram[0xa4:0xa8] = bytes([168]*4),bytes(4)
    ram[0xc7:0xcb],ram[0xd9:0xdd] = bytes(4),bytes(4)
    ram[0xf6],ram[0xe9] = 0,0
    return ram


def transition_cases(rom):
    base = base_state(rom)
    for divers,oxygen,state,phase,y,keys in itertools.product(
            (0,1,5,6),(0,1,15,16,17,63,64),(0,1,6),
            (0,1,14,15,30,31,254,255),(13,19,20,108),(0,65)):
        ram = bytearray(base)
        ram[0xbe],ram[0xe6],ram[0xe8],ram[0x81],ram[0xe1] = divers,oxygen,state,phase,y
        ram[0xbc],ram[0xbd] = 19,255
        yield f'transition-{divers}-{oxygen}-{state}-{phase}-{y}-{keys}',ram,keys
    for divers,oxygen,phase,y,keys in itertools.product(
            (0,1,5,6),(1,16,63,64),(0,30,31,254,255),(14,20),(32,33)):
        ram = bytearray(base)
        ram[0xbe],ram[0xe6],ram[0x81],ram[0xe1] = divers,oxygen,phase,y
        yield f'ascent-{divers}-{oxygen}-{phase}-{y}-{keys}',ram,keys
    for lane,divers,kind,phase in itertools.product(range(4),(0,1,5,6),(0,8,4,12),(0,31,255)):
        ram = bytearray(base)
        ram[0xbe],ram[0xe6],ram[0x81],ram[0xe1] = divers,1,phase,32+24*(3-lane)
        ram[0xc7+lane],ram[0xd9+lane] = 76,kind
        yield f'pickup-{lane}-{divers}-{kind}-{phase}',ram,0
        ram = bytearray(ram)
        ram[0x9e+lane],ram[0xa4+lane],ram[0xe7] = 76,7,80
        yield f'simultaneous-{lane}-{divers}-{kind}-{phase}',ram,65
    for death,reserve,state in itertools.product((0,1,9,10,23),(0,1,3),(0,1,6)):
        ram = bytearray(base)
        ram[0xe1],ram[0xc6],ram[0xf6],ram[0xe6] = 13,76,76,16
        ram[0xe9],ram[0xbb],ram[0xe8],ram[0xbc] = death,reserve,state,2
        yield f'patrol-{death}-{reserve}-{state}',ram,65


def chains(rom):
    for divers,oxygen,phase in itertools.product((0,1,5,6),(1,16,63,64),(0,31,255)):
        ram = base_state(rom)
        ram[0xbe],ram[0xe1],ram[0xe6],ram[0x81] = divers,14,oxygen,phase
        yield f'ascent-{divers}-{oxygen}-{phase}',ram,4,33
    for divers in (0,1,5,6):
        for phase in (0,255):
            ram = base_state(rom)
            ram[0xbe],ram[0xe1],ram[0xe6],ram[0x81] = divers,13,16,phase
            ram[0xbc],ram[0xbd] = 19,255
            yield f'surface-{divers}-{phase}',ram,400,65
    for phase in (0,1,2,3):
        ram = base_state(rom)
        ram[0xe6],ram[0x81] = 1,phase
        yield f'depletion-{phase}',ram,400,0
    for groups,wave in ((19,0),(255,0),(255,255)):
        ram = base_state(rom)
        ram[0xbe],ram[0xe1],ram[0xe6],ram[0xe8],ram[0xbc],ram[0xbd] = 6,13,1,6,groups,wave
        yield f'bonus-progression-{groups}-{wave}',ram,400,65


def verify_raster_alarm(original):
    from graphics_reference import Reference
    raster = Reference()
    count = 0
    for oxygen,y,death,phase in itertools.product(
            (0,1,15,16,17,64),(13,14,19,20),(0,23),range(0,32,2)):
        # Bonus bit with an even OLD phase freezes the following gameplay tick
        # without clearing F9; pickup audio must also be inactive.
        raster.image(e6=oxygen,e1=y,e9=death,**{'81':phase,'ea':0,'eb':0,'ec':0,'f9':165})
        ram = bytearray(1024)
        ram[128:256] = bytes(raster.ale.getRAM())
        before = bytearray(ram)
        before[0x81] = phase
        if ram[0xf9] != alarm(original,before):
            raise ValueError(f'original raster alarm differs at {oxygen}/{y}/{death}/{phase}')
        count += 1
    return count


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock = (OUT/'.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with (OUT/'build.log').open('w') as log:
        subprocess.run([str(ROOT/'.venv/bin/python'),'-B','scripts/render_bench.py',
                        '--collisions','--build-only'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    rom_path = ROOT/'outputs/render/collisions.rom'
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',rom_path.with_suffix('.sym').read_text(),re.M)}
    original = read_original()
    raster_alarm_cases = verify_raster_alarm(original)
    assets = extract(original)
    names,summary,render_cases = [],{},[]
    def record(f,name,mode,ram,keys):
        if mode==0:
            expected = bytearray(ram[:251])
            expected[0xf9] = alarm(original,ram)
        else:
            sampled = acquire(ram,original,assets)
            sampled[0x280],sampled[0x282],sampled[12],sampled[13],_,_ = hardware((0,0,keys,0,0),ram[0xb7],63,0)
            expected = reference(original,list(sampled),0xf5b8,0,0x82)[0]
        f.write(bytes([mode,keys])+ram+expected)
        names.append(name)
        return expected
    with (OUT/'cases.bin').open('wb') as f:
        for oxygen,y,death,phase in itertools.product(range(256),(13,14,19,20,108),(0,1,23),(0,16,255)):
            ram = base_state(original)
            ram[0xe6],ram[0xe1],ram[0xe9],ram[0x81],ram[0xf9] = oxygen,y,death,phase,165
            record(f,f'alarm-{oxygen}-{y}-{death}-{phase}',0,ram,0)
        for phase in range(256):
            for oxygen in (1,16,17):
                ram = base_state(original)
                ram[0x81],ram[0xe6],ram[0xf9] = phase,oxygen,phase
                record(f,f'alarm-phase-{phase}-{oxygen}',0,ram,0)
        summary['alarm_cases'] = len(names)
        for name,ram,keys in transition_cases(original):
            record(f,name,1,ram,keys)
            render_cases.append((name,bytes(ram).hex(),keys))
        summary['transition_cases'] = len(names)-summary['alarm_cases']
        chain_reports = []
        for chain,ram,ticks,keys in chains(original):
            changes = []
            for tick in range(ticks):
                expected = record(f,f'{chain}/tick-{tick}',1 if tick==0 else 2,ram,keys)
                watched = (0xe6,0xbe,0xe8,0xe9,0xbc,0xbd,0xe1)
                if any(ram[a]!=expected[a] for a in watched):
                    changes.append(dict(tick=tick,state={f'{a:02x}':expected[a] for a in watched}))
                ram[:251] = expected
            chain_reports.append(dict(name=chain,ticks=ticks,reloads_after_start=0,changes=changes))
        summary['chain_ticks'] = sum(c['ticks'] for c in chain_reports)
    # Save original-derived details locally for renderer coverage and review.
    (OUT/'chains.json').write_text(json.dumps(chain_reports,indent=2)+'\n')
    (OUT/'render-cases.json').write_text(json.dumps(render_cases)+'\n')
    (OUT/'case-index.json').write_text(json.dumps(names)+'\n')
    (OUT/'start.tcl').write_text(
        f'set entries {{{symbols["oxygen_rpc_start"]} {symbols["collision_tick_rpc_start"]} {symbols["collision_tick_rpc_start"]}}}\n'
        f'set done {symbols["collision_rpc_done"]}\nsource scripts/oxygen_contract.tcl\n')
    result_path = OUT/'result.json'
    result_path.unlink(missing_ok=True)
    with (OUT/'openmsx.log').open('w') as log:
        process = subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1',
            '-cart',str(rom_path),'-script',str(OUT/'start.tcl')],cwd=ROOT,
            env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
            stdout=log,stderr=subprocess.STDOUT,timeout=90)
    result = json.loads(result_path.read_text())
    if process.returncode or not result['passed'] or result['cases']!=len(names):
        raise ValueError(f'oxygen contract failed at {names[result["cases"]]}: {result}')
    result.update(summary,original_raster_alarm_cases=raster_alarm_cases,
                  rom_sha256=hashlib.sha256(rom_path.read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(original).hexdigest(),
                  machine='C-BIOS_MSX1',ram_kib=64,vram_kib=16,video='NTSC',
                  method='original F44F..F473 CPU execution; acquired raster contacts; original F5B8..F00E; actual BIOS controls',
                  physical_hardware=False)
    result_path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
