#!/usr/bin/env python3
"""Original score/progression instructions versus native Z80 and real contacts.

All original-derived records stay in ignored outputs/progression. Direct routine
checks include independent decimal/field assertions; integrated checks acquire
the original raster contacts and logical alarm before executing F5B8.
"""
import fcntl
import hashlib
import itertools
import json
import os
import re
import struct
import subprocess

from input_contract import hardware
from native_contract import reference
from original_graphics import ROOT, extract, read_original
from oxygen_contract import base_state
from oxygen_reference import acquire

OUT = ROOT/'outputs/progression'


def bcd(value):
    return bytes(int(f'{value:06d}'[i:i+2], 16) for i in (0,2,4))


def score(ram):
    return int(bytes(ram[0xb8:0xbb]).hex())


def direct_cases(rom):
    # Every valid low-byte operand pair, both incoming carries (CLC must win).
    for low,add,carry in itertools.product(range(100),range(100),range(2)):
        value = (low*997+add*101)%10000*100+low
        ram = base_state(rom)
        ram[0xb8:0xbb],ram[0xbb] = bcd(value),(low+add)%7
        yield f'bcd-{low}-{add}-{carry}',0xfb9d,ram,int(f'{add:02d}',16),0,carry
    for high,middle,low,add,reserve in itertools.product(
            (0,1,9,10,98,99),(0,98,99),(0,1,90,99),(0,1,10,50,90,99),range(7)):
        ram = base_state(rom)
        ram[0xb8:0xbb],ram[0xbb] = bcd(high*10000+middle*100+low),reserve
        ram[0xa3] = 255 if high==99 else 0
        yield f'boundary-{high}-{middle}-{low}-{add}-{reserve}',0xfb9d,ram,int(f'{add:02d}',16),0,1
    for amount,carry,reserve,state in itertools.product(range(256),range(2),(0,6),(0,255)):
        ram = base_state(rom)
        ram[0xb8:0xbb],ram[0xbb],ram[0xa3] = bcd(999999),reserve,state
        yield f'terminal-{amount}-{carry}-{reserve}-{state}',0xfb9d,ram,amount,0,carry
    for player,active,saved in itertools.product(range(2),range(7),range(7)):
        ram = base_state(rom)
        ram[0xb7] = player
        ram[0xb8:0xbf] = bytes([0x12,0x34,0x56,active,19,254,5])
        ram[0xbf:0xc6] = bytes([0x65,0x43,0x21,saved,255,17,2])
        yield f'swap-{player}-{active}-{saved}',0xffda,ram,0,0,0
        if active or saved:
            yield f'next-player-{player}-{active}-{saved}',0xfccd,ram,0,0,0


def assert_direct(entry,ram,add,expected):
    if entry==0xfb9d:
        if score(ram)==999999:
            assert expected[0xb8:0xbb]==ram[0xb8:0xbb]
            assert expected[0xbb]==ram[0xbb]
            assert expected[0xa3]==(ram[0xa3]+int(add!=0))&255
            return
        total = score(ram)+int(f'{add:02x}')
        assert expected[0xb8:0xbb] == bcd(min(total,999999))
        overflow = total>999999
        crossing = not overflow and total//10000 != score(ram)//10000
        assert expected[0xbb] == min(6,ram[0xbb]+int(crossing))
        assert expected[0xa3] == (ram[0xa3]+int(overflow))&255
    else:
        swapped = bytearray(ram)
        swapped[0xb8:0xbf],swapped[0xbf:0xc6] = ram[0xbf:0xc6],ram[0xb8:0xbf]
        swapped[0xb7] ^= 1
        if entry==0xfccd:
            if not swapped[0xbb]:
                swapped = bytearray(ram)
            swapped[0xbb] -= 1
        assert expected[0xb7:0xc6] == swapped[0xb7:0xc6]


def transition_cases(rom):
    for groups,kind,lane,event in itertools.product(
            range(256),(0,4,8,12),range(4),('shot','body','both')):
        ram = base_state(rom)
        # Put the torpedo on an occupied source row: shark4 / submarine9.
        ram[0xbc],ram[0xe1] = groups,(34 if kind&4 else 29)+24*(3-lane)
        ram[0xb8:0xbb],ram[0xbb] = bcd(9990),5
        ram[0xd9+lane],ram[0xa4+lane],ram[0x9e+lane] = kind,7,76
        ram[0xc6] = 76 if event!='shot' else 40
        ram[0xe7] = 80 if event!='body' else 0
        yield f'contact-{groups}-{kind}-{lane}-{event}',ram,1,63
    for groups,value,reserve,death,bonus in itertools.product(
            (19,254,255),(9990,999990,999999),(0,5,6),(0,1,23),range(2)):
        ram = base_state(rom)
        ram[0xbc],ram[0xbb],ram[0xe9],ram[0x81] = groups,reserve,death,15
        ram[0xb8:0xbb] = bcd(value)
        if bonus:
            ram[0xe8],ram[0xbe],ram[0xe6] = 6,6,0
        else:
            ram[0xe1],ram[0xc6],ram[0xe7] = 29,76,80
            ram[0xa4+3],ram[0x9e+3] = 7,76
        yield f'scoring-overlap-{groups}-{value}-{reserve}-{death}-{bonus}',ram,65,63
    for groups,oxygen,reserve in itertools.product(range(256),(0,1,64),(0,5,6)):
        ram = base_state(rom)
        ram[0xbc],ram[0xbe],ram[0xe8],ram[0xe6],ram[0x81] = groups,6,6,oxygen,15
        ram[0xb8:0xbb],ram[0xbb] = bcd(9990),reserve
        yield f'bonus-{groups}-{oxygen}-{reserve}',ram,65,63
    for groups,phase in itertools.product(range(256),range(8)):
        ram = base_state(rom)
        ram[0xbc],ram[0x81],ram[0xf6] = groups,phase,100
        yield f'patrol-{groups}-{phase}',ram,0,63
    for wave,phase,switches in itertools.product(range(256),(0,15,31,255),(63,127,191,255)):
        ram = base_state(rom)
        ram[0xbd],ram[0x81],ram[0xe7] = wave,phase,80
        ram[0x9e:0xa2],ram[0xa4:0xa8] = bytes([40,72,112,140]),bytes([7]*4)
        ram[0xd9:0xdd],ram[0xc7:0xcb] = bytes([0,4,8,12]),bytes([20,45,110,140])
        yield f'wave-{wave}-{phase}-{switches}',ram,65,switches
    for groups,wave in itertools.product((0,1,6,18,19,20,253,254,255),(0,1,19,254,255)):
        ram = base_state(rom)
        ram[0xbc],ram[0xbd],ram[0xbe],ram[0xe8],ram[0xe6],ram[0x81] = groups,wave,0,6,0,15
        yield f'group-complete-{groups}-{wave}',ram,65,63
    for mode,player,reserve,other,phase in itertools.product(range(2),range(2),(0,1,6),(0,1,6),range(4)):
        ram = base_state(rom)
        ram[0x80],ram[0xb7],ram[0xbb],ram[0xc2],ram[0xe9],ram[0x81] = mode,player,reserve,other,1,phase
        ram[0xb8:0xbb],ram[0xbf:0xc2] = bcd(123456),bcd(654321)
        ram[0xbc:0xbf],ram[0xc3:0xc6] = bytes([19,254,5]),bytes([255,17,2])
        yield f'death-{mode}-{player}-{reserve}-{other}-{phase}',ram,0,63
    for mode,phase,low,state in itertools.product(range(2),(0,1,127,128,255),(0,1,10),(1,2,255)):
        ram = base_state(rom)
        ram[0x80],ram[0x81],ram[0xba],ram[0xa3] = mode,phase,low,state
        ram[0xbf:0xc6] = bytes([0x65,0x43,0x21,4,7,11,2])
        yield f'attract-{mode}-{phase}-{low}-{state}',ram,0,63


def assert_transition(name,ram,expected):
    if name.startswith('contact-'):
        value = min((ram[0xbc]+2)&255,9)*10
        hits = 2 if name.endswith('-both') else 1
        assert score(expected) == score(ram)+value*hits, name
        if not name.endswith('-shot'): assert expected[0xe9]==23, name
    if name.startswith('patrol-'):
        g = ram[0xbc]
        mask = 3 if g<5 else 1
        assert expected[0xf6] == ram[0xf6]-int(g>=2 and not ((ram[0x81]+1)&mask))
    if name.startswith('bonus-'):
        g = ram[0xbc]
        value = min((g+2)&255,9)*10 if ram[0xe6] else 50*(min(g,19)+1)
        assert score(expected) == score(ram)+value
    if name.startswith('group-complete-'):
        g = (ram[0xbc]+1)&255
        assert expected[0xbc]==g
        assert expected[0xbd]==(ram[0xbd]+int(ram[0xbd]<g))&255


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock = (OUT/'.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with (OUT/'build.log').open('w') as log:
        subprocess.run([str(ROOT/'.venv/bin/python'),'-B','scripts/render_bench.py','--collisions','--build-only'],
                       cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    cartridge = ROOT/'outputs/render/collisions.rom'
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',cartridge.with_suffix('.sym').read_text(),re.M)}
    original = read_original()
    assets = extract(original)
    from progression_reference import audit, score_reference
    audit_report = audit(original,base_state(original),
                         (ram for _,ram,_,_ in itertools.islice(transition_cases(original),48)))
    (OUT/'audit.json').write_text(json.dumps(audit_report,indent=2)+'\n')
    names,counts,chains = [],{},[]
    def record(f,name,ram,mode=1,entry=0xf5b8,a=0,x=0x82,carry=0,keys=0,switches=63,row6=0):
        status = bytes(5)
        if mode==0:
            if entry==0xfb9d:
                expected,status = score_reference(original,ram,a,carry)
            else:
                expected = reference(original,list(ram),entry,a,x,0,carry)[0]
            assert_direct(entry,ram,a,expected)
        else:
            sampled = acquire(ram,original,assets)
            sampled[0x280],sampled[0x282],sampled[12],sampled[13],_,_ = hardware((row6,0,keys,0,0),ram[0xb7],switches,0)
            expected = reference(original,list(sampled),0xf5b8,0,0x82)[0]
            assert_transition(name,ram,expected)
        f.write(struct.pack('<H8B',symbols[f'core_{entry:04X}'],mode,a,x,carry,row6,keys,switches,int(entry==0xfb9d))+ram+expected+status)
        names.append(name)
        return expected
    with (OUT/'cases.bin').open('wb') as f:
        for name,entry,ram,a,x,carry in direct_cases(original):
            record(f,name,ram,0,entry,a,x,carry)
        counts['direct_cases'] = len(names)
        for name,ram,keys,switches in transition_cases(original):
            record(f,name,ram,keys=keys,switches=switches)
        counts['transition_cases'] = len(names)-counts['direct_cases']
        for switches in (63,127,191,255):
            ram = base_state(original)
            ram[0x80],ram[0xbb],ram[0xc2],ram[0xe9] = 1,1,1,23
            ram[0xbf:0xc2],ram[0xc3:0xc6] = bcd(654321),bytes([19,27,5])
            changes = []
            for tick in range(1800):
                keys = 33 if ram[0xe6]<64 and not ram[0xe8] else 65
                row6 = 32 if tick==1600 else (64 if tick in (1700,1732) else 0)
                expected = record(f,f'players-{switches}/tick-{tick}',ram,1 if tick==0 else 2,
                                  keys=keys,switches=switches,row6=row6)
                watched = (*range(0xb7,0xc6),0x80,0xa3,0xe9)
                if any(ram[i]!=expected[i] for i in watched):
                    changes.append(dict(tick=tick,state={f'{i:02x}':expected[i] for i in watched}))
                ram[:251] = expected
            chains.append(dict(switches=switches,ticks=1800,reloads_after_start=0,changes=changes))
            assert {c['state']['b7'] for c in changes}=={0,1}
            assert any(c['tick']<1600 and c['state']['a3'] and not c['state']['e9'] for c in changes)
        for groups in (19,253,254,255):
            ram = base_state(original)
            ram[0xbc],ram[0xbd],ram[0xbe],ram[0xe8],ram[0xe6],ram[0xbb] = groups,255,6,6,64,5
            ram[0xb8:0xbb] = bcd(9900)
            changes = []
            completed = False
            for tick in range(400):
                expected = record(f,f'full-bonus-{groups}/tick-{tick}',ram,1 if tick==0 else 2,keys=65)
                watched = (*range(0xb8,0xbf),0xe6,0xe8)
                if any(ram[i]!=expected[i] for i in watched):
                    changes.append(dict(tick=tick,state={f'{i:02x}':expected[i] for i in watched}))
                completed |= expected[0xbc]==(groups+1)&255
                ram[:251] = expected
            assert completed, groups
            chains.append(dict(groups=groups,ticks=400,reloads_after_start=0,changes=changes))
    counts['chain_ticks'] = sum(c['ticks'] for c in chains)
    (OUT/'chains.json').write_text(json.dumps(chains,indent=2)+'\n')
    (OUT/'case-index.json').write_text(json.dumps(names)+'\n')
    (OUT/'start.tcl').write_text(f'set integrated {symbols["collision_tick_rpc_start"]}\nset done {symbols["collision_rpc_done"]}\nsource scripts/progression_contract.tcl\n')
    result_path = OUT/'result.json'
    result_path.unlink(missing_ok=True)
    with (OUT/'openmsx.log').open('w') as log:
        process = subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-cart',str(cartridge),'-script',str(OUT/'start.tcl')],
                                 cwd=ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                                 stdout=log,stderr=subprocess.STDOUT,timeout=180)
    if not result_path.exists():
        raise ValueError(f'progression harness exited {process.returncode} without a result; see {OUT}/openmsx.log')
    result = json.loads(result_path.read_text())
    if process.returncode or not result['passed'] or result['cases']!=len(names):
        raise ValueError(f'progression failed at {names[result["cases"]]}: {result}')
    result.update(counts,rom_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(original).hexdigest(),machine='C-BIOS_MSX1',
                  ram_kib=64,vram_kib=16,video='NTSC',physical_hardware=False)
    result['omitted_phase_audit'] = audit_report
    result_path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
