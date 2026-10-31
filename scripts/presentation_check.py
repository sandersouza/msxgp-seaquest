"""Source pixels versus actual SCREEN2 colors; never read native HUD buffers."""
from functools import lru_cache
from pathlib import Path
import struct
import zlib
import numpy as np
from graphics_palette import tms_color
from hud_reference import masks


def decode_colors(vram, name_base):
    memory = np.frombuffer(vram, dtype=np.uint8)
    names = memory[name_base:name_base+768].reshape(24,32).astype(np.int32)
    ys = np.arange(192)[:,None]
    pattern = (ys//64)*2048 + names[ys//8,np.arange(32)[None,:]]*8 + ys%8
    pattern = pattern.astype(np.int32)
    bits = ((memory[pattern][:,:,None] >> np.arange(7,-1,-1)) & 1).reshape(192,256)
    colors = memory[8192+pattern]
    return np.where(bits, np.repeat(colors>>4,8,axis=1), np.repeat(colors&15,8,axis=1)).astype(np.uint8)


class PresentationOracle:
    def __init__(self, rom):
        from graphics_reference import Reference
        self.rom = rom
        ref = Reference()
        self.empty = ref.image(bb=0,be=0,e6=0)
        self.empty[:,:8] = self.empty[:,8:9]
        self.gauges = {}
        for blink in range(2):
            for value in range(17 if blink else 65):
                self.gauges[blink,value] = ref.image(e6=value,e1=20 if blink else 13)[169:174].copy()
        self.expansion = np.array([max(0,min(159,(2*(x-8)+1)//3)) for x in range(256)])

    @lru_cache(maxsize=256)
    def background(self, seed):
        source = self.empty.copy()
        rotated = seed
        for y in range(45,55):
            rotated = ((rotated<<1)|(rotated>>7))&255
            source[y,:] = 0x90 ^ (rotated&2)
        result = np.zeros((192,256),dtype=np.uint8)
        for y in range(192):
            raw_y = (32 if y<17 else y+16 if y<29 else 45 if y==29 else
                     y+15 if y<41 else y+17 if y<152 else None)
            row = source[raw_y] if raw_y is not None else np.full(160,6 if y<176 else 0,dtype=np.uint8)
            result[y,:] = row[8]
            for x in range(160): result[y,8+3*x//2:8+3*(x+1)//2] = row[x]
        return result

    @lru_cache(maxsize=512)
    def palette(self, xor, mask):
        return np.array([tms_color((value^xor)&mask) for value in range(256)],dtype=np.uint8)

    def expected(self, ram):
        from render_bench import expected_pixels
        color = self.palette(ram[0x85],ram[0x86])
        result = color[self.background(ram[0x82])].copy()
        objects = np.frombuffer(expected_pixels(ram,self.rom),dtype=np.uint8).reshape(192,256)
        for lane in range(4):
            top = 48+24*(3-lane)
            band = result[top:top+15]
            band[objects[top:top+15]!=0] = tms_color(ram[0xac+lane])
        targets = {'score':0,'lives':8,'divers':160,'logo':176}
        for name,field in masks(self.rom,ram).items():
            top, height = targets[name], len(field['rows'])
            if name=='divers': height=16
            result[top:top+height,96:168] = tms_color(field['background'])
            foreground = tms_color(field['foreground'])
            for y,row in enumerate(field['rows']):
                for x in row: result[top+y,96+3*x//2:96+3*(x+1)//2] = foreground
        oxygen = min(ram[0xe6],64)
        blink = int(ram[0xe1]!=13 and not ram[0xe9] and 0<oxygen<=16 and not ram[0x81]&16)
        gauge = self.gauges[blink,oxygen]
        for x in range(8,160):
            result[152:157,8+3*x//2:8+3*(x+1)//2] = color[gauge[:,x]][:,None]
        return result

    def check(self, ram, vram, name_base):
        actual = decode_colors(vram,name_base)
        # The ninth sprite restores the one-pixel oxygen edge, independently
        # of the eight source actors checked by the existing sprite oracle.
        y,x,pattern,color = vram[0x1b20:0x1b24]
        expected_y = 151 if 0<ram[0xe6]<=4 else 216
        expected_color = tms_color((6^ram[0x85])&ram[0x86])
        if (y,x,pattern,color)!=(expected_y,80,252,expected_color) or vram[0x1b24]!=208:
            raise ValueError('HUD oxygen-edge SAT or terminator mismatch')
        border = bytes([0,128,128,128,128]+[0]*27)
        if vram[0x3fe0:0x4000]!=border: raise ValueError('resident oxygen-edge sprite changed')
        if y==151: actual[153:157,80] = color
        expected = self.expected(ram)
        if not np.array_equal(actual,expected):
            yy,xx = np.where(actual!=expected)
            raise ValueError(f'HUD/scene colors: {len(xx)} differences, first={xx[0]},{yy[0]}, '
                             f'target={actual[yy[0],xx[0]]} source={expected[yy[0],xx[0]]}')
        return actual


def png(path, indices):
    """Debug preview of TMS indices; CRT/analog RGB appearance is not certified."""
    palette = bytes.fromhex('000000 000000 21c842 5edc78 5455ed 7d76fc d4524d '
                            '42ebf5 fc5554 ff7978 d4c154 e6ce80 21b03b c95bba cccccc ffffff')
    height,width = indices.shape
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw = b''.join(b'\x00'+row.tobytes() for row in indices)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,3,0,0,0))+
                          chunk(b'PLTE',palette)+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


if __name__=='__main__':
    import json
    from original_graphics import ROOT,read_original
    out = ROOT/'outputs/presentation'
    ram = (out/'hud-probe-state.bin').read_bytes()[:1024]
    vram = (out/'hud-probe-vram.bin').read_bytes()
    base = json.loads((out/'hud-probe.json').read_text())['name_base']
    oracle = PresentationOracle(read_original())
    actual = oracle.check(ram,vram,base)
    png(out/'hud-probe.png',actual)
    print('original HUD and scene colors match')
