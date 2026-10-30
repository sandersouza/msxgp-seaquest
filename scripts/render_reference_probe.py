#!/usr/bin/env python3
"""Local reference-only measurement of patrol raster bounds (no exported art)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    import ale_py
    import numpy as np
    path = ROOT/'references/roms/seaquest-atari2600.a26'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != 'fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43':
        raise ValueError('unverified reference revision')
    ale = ale_py.ALEInterface()
    ale.setInt('frame_skip',1)
    ale.setInt('random_seed',0)
    ale.setFloat('repeat_action_probability',0.0)
    ale.loadROM(str(path))
    for _ in range(150): ale.act(ale_py.Action.NOOP)
    base = list(map(int,ale.getRAM()))

    def image(frame,patrol):
        ram = base[:]
        fixed = {0x81:1,0x82:1,0xa2:0,0xa3:0,0xc6:64,0xe1:0,0xe0:frame,
                 0xe9:0,0xe8:0,0xe6:64,0xf6:patrol,0xcf:0,0xd0:0,0xd1:0}
        for lane in range(4): fixed.update({0x9e+lane:168,0xa4+lane:0,0xc7+lane:0,0xd9+lane:0,0xf1+lane:255})
        for address,value in fixed.items(): ram[address-128] = value
        for _ in range(3):
            for index,value in enumerate(ram): ale.setRAM(index,value)
            ale.act(ale_py.Action.NOOP)
        return ale.getScreen().copy()

    rows = []
    for frame in range(3):
        blank = image(frame,0)
        patrol = image(frame,64)
        yy,xx = np.where(patrol!=blank)
        box = [int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
        if box != [64,46,71,52]: raise ValueError(f'unexpected patrol bounds: {box}')
        rows.append({'player_animation':frame,'raw_nonzero_bounds':box})
    report = {'original_sha256':digest,'ale':ale_py.__version__,'phase':1,'patrol_x':64,
              'frames':rows,'display_y_translation':-15,'sprite_box_y':[22,37],
              'first_lane_sprite_box_y':[49,64],'verdict':'patrol box ends before first diver lane'}
    out = ROOT/'outputs/render/patrol-geometry.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
