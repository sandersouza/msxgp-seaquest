"""Focused native HUD/color/font sweep, including the full-suite worst frames."""
import json
import os
import re
import struct
import subprocess

from audio_reference import ROOT,OUT
from original_graphics import read_original,extract
from presentation_check import PresentationOracle
from progression_contract import bcd


def main():
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',(OUT/'audio64.sym').read_text(),re.M)}
    private = OUT/'sweep'
    private.mkdir(exist_ok=True)
    data = (ROOT/'outputs/render/cases.bin').read_bytes()
    times = [int(v) for v in (ROOT/'outputs/render/cycles.txt').read_text().split()]
    cases,names = [],[]
    for index in sorted(range(len(times)),key=times.__getitem__,reverse=True)[:32]:
        record = data[index*1034:(index+1)*1034]
        record = symbols['core_F5B8'].to_bytes(2,'little')+record[2:]
        cases.append(record); names.append(f'full-worst-{index}')
    base = bytearray(data[150*1034+10:151*1034])
    base[0x85],base[0x86],base[0xe6],base[0xe1],base[0xa3] = 0,255,64,13,0
    def add(name,ram,entry=0xf00e):
        cases.append(struct.pack('<HBBBB',symbols[f'core_{entry:04X}'],0,130,0,0)+bytes([0,0,0,63])+ram)
        names.append(name)
    for player in range(2):
        for pair in range(100):
            ram = bytearray(base); ram[0xb7] = player
            ram[0xb8:0xbb] = bcd(pair*10101)
            ram[0xbb],ram[0xbe],ram[0xa3] = pair%7,(pair//7)%7,pair*2
            add(f'font-{player}-{pair}',ram)
    for xor in range(0,256,2):
        for mask in (7,15,247,255):
            ram = bytearray(base)
            ram[0x85],ram[0x86],ram[0x82],ram[0xb7] = xor,mask,(xor*29+1)&255,(xor//2)&1
            add(f'palette-{xor}-{mask}',ram)
    for seed in range(256):
        ram = bytearray(base); ram[0x85],ram[0x86],ram[0x82] = 144,247,seed
        add(f'ripple-{seed}',ram)
    for counter in range(127,256):
        ram = bytearray(base)
        ram[0xa2],ram[0xa3],ram[0x81] = counter,159,255
        ram[0x85],ram[0x86] = ((counter*2)&255,247) if counter>=128 else (0,255)
        add(f'attract-transition-{counter}',ram,0xf5b8)
    (private/'cases.bin').write_bytes(b''.join(cases))
    start = f'set bench_dir {private}\nset input_mode 1\nset hud_mode 1\nset prime_entry {symbols["core_F00E"]}\nset prime_start {symbols["audio_prime_start"]}\nset inject_pixel -1\n'
    start += f'set palette_mode {int("palette_prepare" in symbols)}\nset prime_font_stress 1\nset font_prepare {symbols["hud_prepare"]}\nset font_done {symbols["prepare_shapes"]}\n'
    start += ''.join(f'set {key} {symbols[value]}\n' for key,value in
                     (('rpc_start','rpc_start'),('rpc_done','rpc_done'),('commit_pc','render_commit')))
    (private/'start.tcl').write_text(start+'source scripts/render_bench.tcl\n')
    with (private/'openmsx.log').open('wb') as log:
        subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-cart',str(OUT/'audio64.rom'),'-romtype','ASCII16',
                        '-script',str(private/'start.tcl')],cwd=ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
    vram = (private/'vram.bin').read_bytes(); states = (private/'state.bin').read_bytes(); pages = (private/'name-pages.bin').read_bytes()
    registers = (private/'registers.bin').read_bytes()
    phase_registers = (private/'phase-registers.bin').read_bytes()
    if len(phase_registers)!=4*len(cases): raise ValueError('truncated phase registers')
    oracle = PresentationOracle(read_original())
    from render_bench import check_original_sprites,visible_signature
    baseline = (private/'baseline.bin').read_bytes()
    prepared = (private/'prepared.bin').read_bytes()
    original = read_original();assets = extract(original)
    for i,name in enumerate(names):
        try:
            state = states[i*1024:(i+1)*1024];frame = vram[i*16384:(i+1)*16384]
            if phase_registers[i*4:i*4+2]!=phase_registers[i*4+2:i*4+4]:
                raise ValueError('R1/R7 changed before VBlank')
            old_page,prepared_page,new_page = pages[i*3:i*3+3]
            if old_page!=prepared_page or new_page!=(old_page^1):
                raise ValueError('name table changed outside the commit')
            before = baseline[i*16384:(i+1)*16384]
            staged = prepared[i*16384:(i+1)*16384]
            if visible_signature(before,old_page*1024,9)!=visible_signature(staged,old_page*1024,9):
                raise ValueError('visible pixels changed before VBlank')
            oracle.check(state,frame,pages[i*3+2]*1024,registers[i*8+7]&15,bool(registers[i*8+1]&64))
            check_original_sprites(state,frame,assets,original,True)
        except ValueError as error: raise ValueError(f'{name}: {error}') from error
    cycles = [int(v) for v in (private/'cycles.txt').read_text().split()]
    font = json.loads((private/'font-stats.json').read_text())
    io = json.loads((private/'io.json').read_text())
    spacing = io['min_active_spacing']
    if spacing<29 or io['min_data_spacing']<12: raise ValueError('unsafe VRAM data spacing')
    if font['max_glyph_bytes']!=24: raise ValueError('three missing middle glyphs were not exercised')
    result = dict(cases=len(cases),max_cycles=max(cycles),worst=names[cycles.index(max(cycles))],
                  worst_full_cycles=max(cycles[:32]),display_only_cases=len(cases)-32,
                  max_dynamic_font_bytes=font['max_glyph_bytes'],
                  min_vram_spacing=spacing,precommit_visible_pixels_unchanged=True,
                  limitation='F00E projection fixtures isolate display; first32 execute original full update')
    (private/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))


if __name__=='__main__': main()
