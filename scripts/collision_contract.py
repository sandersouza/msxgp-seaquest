#!/usr/bin/env python3
"""Compare original TIA latches, occupancy, native acquisition and resolution."""
import hashlib
import fcntl
import json
import os
import platform
import random
import re
import subprocess

from collision_reference import contacts
from graphics_reference import Reference
from native_contract import reference
from original_graphics import ROOT, extract, read_original

OUT = ROOT/'outputs/collision'
KINDS = (0,1,2,4,5,6,8,9,10,12,13,14)


def scenarios():
    rng = random.Random(10)
    for n in range(8192):
        y = rng.randrange(13,109)
        x = rng.randrange(21,135)
        changes = dict(e1=y,c6=x,e0=rng.randrange(3),d6=rng.choice((0,8)),
                       dd=rng.randrange(8),f6=rng.randrange(160),e7=rng.randrange(160),
                       e9=rng.choice((0,0,0,*range(1,24))),bb=n%7,**{'82':n&255})
        for lane in range(4):
            near = n%3!=0
            changes.update({f'{0x9e+lane:x}':(x+rng.randrange(-35,24))&255 if near else rng.randrange(256),
                            f'{0xa4+lane:x}':rng.randrange(8),
                            f'{0xc7+lane:x}':(x+rng.randrange(-10,17))&255 if near else rng.randrange(256),
                            f'{0xd9+lane:x}':rng.choice(KINDS)})
        yield f'mixed-{n}',changes
    # Exhaust every original base coordinate / repeat mask, including ghost P1.
    for x in range(256):
        for mask in range(8):
            changes = dict(e1=100,c6=76,e7=x%160,dd=x%8,e0=x%3)
            for lane in range(4):
                changes.update({f'{0x9e+lane:x}':x,f'{0xa4+lane:x}':mask,
                                f'{0xc7+lane:x}':(x+lane*3)&255,
                                f'{0xd9+lane:x}':KINDS[(x+lane)%len(KINDS)]})
            yield f'edge-{x}-{mask}',changes
    # Surface clear/blank rows, every source player shape and patrol separation.
    for death in (0,*range(1,24)):
        for y in range(13,24):
            for dx in range(-8,17):
                yield f'patrol-{death}-{y}-{dx}',dict(e1=y,c6=76,f6=76+dx,
                                                     e9=death,e0=death%3,d6=(death&1)*8)
    for lane in range(4):
        for kind in KINDS:
            for facing in (0,8):
                for divers in (0,6):
                    yield f'simultaneous-{lane}-{kind}-{facing}-{divers}',{
                        'e1':32+24*(3-lane),'c6':76,'e7':80,'dd':5,'e0':0,'d6':facing,
                        f'{0x9e+lane:x}':80,f'{0xa4+lane:x}':7,
                        f'{0xc7+lane:x}':76,f'{0xd9+lane:x}':kind,'be':divers}
    for reserve in (0,1):
        for frame in range(3):
            for facing in (0,8):
                for y in range(13,24):
                    for dx in range(-8,17):
                        yield f'low-reserve-patrol-{reserve}-{frame}-{facing}-{y}-{dx}',dict(
                            bb=reserve,e9=0,e0=frame,e1=y,c6=76,f6=76+dx,d6=facing)
    for state in (0,1,6):
        for y in range(13,20):
            for facing in (0,8):
                yield f'patrol-state-{state}-{y}-{facing}',dict(e1=y,c6=76,f6=76,
                    e0=2,e9=0,d6=facing,_native={0xe8:state,0xe6:16,0xbc:2})


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock = (OUT/'.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with (OUT/'build.log').open('w') as log:
        subprocess.run([str(ROOT/'.venv/bin/python'),'-B','scripts/render_bench.py','--collisions','--build-only'],
                       cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    rom = ROOT/'outputs/render/collisions.rom'
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',rom.with_suffix('.sym').read_text(),re.M)}
    original = read_original()
    assets = extract(original)
    ale = Reference()
    names = []
    hit_counts = [0]*8
    combinations = {}
    phases,waves,seeds,player_ys = set(),set(),set(),set()
    with (OUT/'cases.bin').open('wb') as f:
        for name,changes in scenarios():
            changes = dict(changes)
            native_overrides = changes.pop('_native',{})
            ale.image(**changes)
            ram = bytearray(1024)
            ram[128:256] = bytes(ale.ale.getRAM())
            player_ys.add(ram[0xe1])
            actual = bytes(ram[0xb0:0xb7])+bytes([ram[0xf8]])
            expected = contacts(ram,original,assets)
            if expected != actual:
                raise ValueError(f'{name}: occupancy={expected.hex()} TIA={actual.hex()}')
            for i,v in enumerate(actual): hit_counts[i] += int(v!=255 if i<7 else bool(v&128))
            combo = ''.join(str(int(v)) for v in (any(v!=255 for v in actual[:4]),
                            actual[4]!=255,actual[5]!=255,actual[6]!=255,bool(actual[7]&128)))
            combinations[combo] = combinations.get(combo,0)+1
            # Poison acquired outputs; all other source state must be preserved.
            ram[0xb0:0xb7],ram[0xf8] = bytes([127]*7),127
            expected_ram = bytearray(ram[:251])
            expected_ram[0xb0:0xb7],expected_ram[0xf8] = expected[:7],expected[7]
            f.write(bytes([0])+ram+expected_ram)
            names.append(name+'/acquire')
            # Resolution uses normal native gameplay (not the oracle's frozen
            # bonus early exit), plus varied phase, seeds, full groups and waves.
            ram[0xe8],ram[0xe6],ram[0xa3] = 0,64,0
            phase = len(names)//2
            ram[0x81] = phase&255
            ram[0xbd],ram[0xbc] = (phase*17)&255,phase%32
            for address,value in native_overrides.items(): ram[address] = value
            phases.add(ram[0x81]); waves.add(ram[0xbd]); seeds.add(ram[0x82])
            ram[0x280],ram[0x282],ram[0xc],ram[0xd] = 255,63,128,128
            expected_ram = bytearray(ram)
            expected_ram[0xb0:0xb7],expected_ram[0xf8] = expected[:7],expected[7]
            expected_ram,_ = reference(original,list(expected_ram),0xf5b8,0,0x82)
            f.write(bytes([1])+ram+expected_ram)
            names.append(name+'/resolve')
    (OUT/'case-index.json').write_text(json.dumps(names))
    if any(len(values)!=256 for values in (phases,waves,seeds)) or len(player_ys)!=96:
        raise ValueError('incomplete phase/wave/seed/player-Y coverage')
    (OUT/'start.tcl').write_text(f'set entries {{{symbols["collision_rpc_start"]} {symbols["collision_tick_rpc_start"]}}}\nset done {symbols["collision_rpc_done"]}\nsource scripts/collision_contract.tcl\n')
    result_path = OUT/'contract-result.json'
    result_path.unlink(missing_ok=True)
    with (OUT/'openmsx.log').open('w') as log:
        run = subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-cart',str(rom),'-script',str(OUT/'start.tcl')],
                             cwd=ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                             stdout=log,stderr=subprocess.STDOUT,timeout=60)
    result = json.loads(result_path.read_text())
    if run.returncode or not result['passed'] or result['cases']!=len(names):
        raise ValueError(f'collision contract failed at {names[result["cases"]]}: {result}')
    result.update(original_tia_cases=len(names)//2,hit_counts=hit_counts,
                  contact_combinations=combinations,
                  contact_combination_order='any enemy/ball, missile/enemy, player/enemy, player/ball, patrol',
                  phase_values=len(phases),wave_values=len(waves),seed_values=len(seeds),legal_player_y_values=len(player_ys),
                  rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),python=platform.python_version(),
                  method='unmodified ALE/Stella raster latches; independent occupancy; Z80 acquisition and original py65 ordered resolution',
                  physical_hardware=False)
    result_path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
