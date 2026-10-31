"""Precalculate the same48-byte enemy transfers for a64KiB ASCII16 cartridge."""
from pathlib import Path
import hashlib
import json
from original_graphics import read_original, ROOT
from render_tables import shifted_row


def generate(palette_fast=False):
    rom = read_original()
    starts = sorted({rom[0xfa2+kind]+offset for kind in (0,1,2,4,5,6)
                     for offset in (range(8) if kind<4 else (0,))})
    windows = bytearray([255]*256)
    images, pointers = bytearray(), bytearray()
    count = 0
    for slot, start in enumerate(starts):
        windows[start+14] = slot
        for reflect in range(2):
            for parity in range(2):
                for phase in range(8):
                    if len(images)%16384+48>16384:
                        images.extend(bytes(16384-len(images)%16384))
                    bank = 2+len(images)//16384
                    address = 0x8000+len(images)%16384
                    pointers.extend(address.to_bytes(2,'little')+bytes([bank]))
                    rows = list(reversed(rom[0xd00+start:0xd00+start+15]))+[0]
                    if reflect: rows = [int(f'{value:08b}'[::-1],2) for value in rows]
                    images.extend(shifted_row(value,phase,parity)[column]
                                  for half in range(2) for column in range(3)
                                  for value in rows[half*8:half*8+8])
                    count += 1
    used = len(images)
    if used>32768: raise ValueError('enemy precomputation exceeds two16KiB banks')
    images.extend(bytes(32768-used))
    out = ROOT/'outputs/presentation'
    out.mkdir(parents=True,exist_ok=True)
    (out/'enemy-patterns.bin').write_bytes(images)
    (out/'enemy-windows.bin').write_bytes(windows)
    pointer_code = []
    for part in ('LOW','HIGH'):
        pointer_code += [f'enemy_windows_{part.lower()}:']
        for start in range(0,256,16):
            pointer_code += ['    DB '+','.join('0' if slot==255 else f'{part}(enemy_pointers+{slot*96})'
                                              for slot in windows[start:start+16])]
    (out/'enemy-window-pointers.inc').write_text('\n'.join(pointer_code)+'\n')
    (out/'enemy-pointers.bin').write_bytes(pointers)
    from graphics_palette import tms_color
    (out/'enemy-foreground-nibbles.bin').write_bytes(bytes(tms_color(n)<<4 for n in range(256)))
    colors = sorted({tms_color(value) for value in list(rom[0xf0f:0xf17])+[0,8]})
    if colors!=[1,6,10,12,13,14]: raise ValueError('normal source enemy palette changed')
    if palette_fast: colors = [1]+colors
    background = 0 if palette_fast else 4
    slots = len(colors)
    top_ids,bottom_ids = bytearray(),bytearray()
    for slot in range(slots):
        for lane in range(4):
            for cache in range(2):
                top = (1+30*slot+3*cache if lane==0 else
                       7+30*slot+6*cache if lane==1 else
                       19+30*slot+6*cache if lane==2 else 1+12*slot+6*cache)
                top_ids.append(top)
                bottom_ids.append(1+6*slot+3*cache if lane==0 else top+3)
    code = ['; Normal enemy colour slots, source-verified TMS palette.',
            f'ENEMY_SLOT_COUNT EQU {slots}',f'ENEMY_SLOT_IDS_BYTES EQU {slots*8}',
            'enemy_top_ids:', '    DB '+','.join(map(str,top_ids)),
            'enemy_bottom_ids:', '    DB '+','.join(map(str,bottom_ids)),
            'enemy_normal_slots:', '    DB '+','.join(str(len(colors)-1-colors[::-1].index(n)) if n in colors else '255' for n in range(16)),
            'enemy_normal_rgba:', '    DB '+','.join(str(n*16+background) for n in colors),
            'hud_enemy_init:']
    for slot,color in enumerate(colors):
        for base,chunks in ((0x2008+slot*96,2),(0x2808+slot*240,5),(0x3008+slot*48,1)):
            code += [f'    LD A,${color*16+background:02X}']
            for chunk in range(chunks):
                code += [f'    LD DE,${base+chunk*48:04X}','    CALL hud_fill48']
    code += ['    RET']
    (out/'enemy-colors.inc').write_text('\n'.join(code)+'\n')
    result = dict(source_windows=len(starts),variants=count,pattern_bytes=48*count,
                  bank_bytes=len(images),padding=len(images)-48*count,
                  sha256=hashlib.sha256(images).hexdigest())
    (out/'enemy-patterns.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return result


if __name__=='__main__': generate()
