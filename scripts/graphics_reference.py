#!/usr/bin/env python3
"""Local ALE pixel oracle for extracted TIA shapes (no exported art in Git)."""
import json
import os
import platform
import ale_py
import numpy as np
from original_graphics import OUT, ROOT, SHA256, extract, read_original


class Reference:
    def __init__(self):
        read_original()
        self.ale = ale_py.ALEInterface()
        self.ale.setInt('frame_skip',1)
        self.ale.setInt('random_seed',0)
        self.ale.setFloat('repeat_action_probability',0.0)
        self.ale.loadROM(str(ROOT/'references/roms/seaquest-atari2600.a26'))
        for _ in range(150): self.ale.act(ale_py.Action.NOOP)
        self.base = list(map(int,self.ale.getRAM()))

    def image(self, **changes):
        # Logo selection deliberately uses a terminal attract counter. ALE's
        # terminal flag is sticky even after RAM injection; reset it explicitly.
        if self.ale.game_over():
            self.ale.reset_game()
            for _ in range(150): self.ale.act(ale_py.Action.NOOP)
        ram = self.base[:]
        fixed = {0x81:2,0x82:1,0x85:0,0x86:255,0xa2:0,0xa3:0,0xc6:64,
                 0xe1:0,0xe0:0,0xe9:0,0xe8:2,0xe6:64,0xf6:0,0xe7:0,
                 0xcf:0,0xd0:0,0xd1:0,0xd6:0,0xdd:0}
        for lane in range(4):
            fixed.update({0x9e+lane:168,0xa4+lane:0,0xc7+lane:0,0xd9+lane:0,0xf1+lane:255})
        fixed.update({int(k,16):v for k,v in changes.items()})
        for address,value in fixed.items(): ram[address-128] = value
        for _ in range(3):
            for index,value in enumerate(ram): self.ale.setRAM(index,value)
            self.ale.act(ale_py.Action.NOOP)
        return self.ale.getScreen().copy()


def mask(rows, x, y, shape):
    result = np.zeros(shape,dtype=bool)
    for dy,row in enumerate(rows):
        for dx in row:
            if 0 <= y+dy < shape[0] and 0 <= x+dx < shape[1]:
                result[y+dy,x+dx] = True
    return result


def main():
    assets = extract(read_original())
    corrupt = os.environ.get('SEAQUEST_GRAPHICS_INJECT_ASSET')
    if corrupt:
        assets[corrupt]['rows'][0] = [0]
    ref = Reference()
    blank = ref.image()
    checks = []
    for name,asset in assets.items():
        changes = {}
        if name.startswith('player-'):
            _,frame,reflect = name.split('-')
            changes = {'e1':50,'e0':int(frame),'d6':int(reflect)*8}
            x,y = 64,83
        elif name.startswith('explosion-'):
            _,death,reflect = name.split('-')
            changes = {'e1':50,'e9':int(death),'d6':int(reflect)*8}
            x,y = 64,83
        elif name.startswith('patrol-'):
            changes = {'e0':int(name.split('-')[1]),'f6':64}
            x,y = 64,45
        elif name.startswith('early-patrol-'):
            changes = {'e0':int(name.split('-')[-1]),'f6':64,'e9':1}
            x,y = 64,45
        elif name.startswith('ball-'):
            changes = {'c7':64,'d9':int(name.split('-')[1])}
            x,y = 64,137
        elif name.startswith('enemy-'):
            _,selection,animation = name.split('-')
            changes = {'9e':64,'a4':4,'d9':int(selection),'dd':int(animation)}
            x,y = 64,137
        elif name == 'torpedo':
            changes = {'e1':50,'e7':100}
            x,y = 100,90
        elif name.startswith('surface-'):
            base_name = asset['display_variant_of']
            _,number,reflect = base_name.split('-')
            changes = {'e1':asset['player_y'],'d6':int(reflect)*8}
            changes['e0' if base_name.startswith('player-') else 'e9'] = int(number)
            x,y = 64,asset['player_y']+33
        else:
            continue
        baseline = ref.image(e1=50) if name=='torpedo' else blank
        actual = ref.image(**changes) != baseline
        # Exclude HUD/state alterations and the inactive ball positioned at X0.
        roi = np.zeros(actual.shape,dtype=bool)
        roi[max(0,y-2):y+len(asset['rows'])+2,40:128] = True
        actual &= roi
        expected = mask(asset['rows'],x,y,actual.shape) & roi
        if not np.array_equal(actual,expected):
            yy,xx = np.where(actual != expected)
            print(name,'mismatches',len(xx),'first',list(zip(xx[:8].tolist(),yy[:8].tolist())))
            checks.append(dict(asset=name,passed=False,differences=len(xx)))
        else:
            checks.append(dict(asset=name,passed=True,pixels=int(actual.sum())))
    for name in [f'digit-{n}' for n in range(10)]+['blank-digit','life','rescued-diver','seaquest','activision']:
        asset = assets[name]
        if name.startswith('digit-'):
            digit = int(name.split('-')[1])
            image = ref.image(b8=17,b9=17,ba=16+digit)
            x,y,width,color = 98,9,8,26
        elif name == 'blank-digit':
            image = ref.image(b8=0,b9=0,ba=1)
            x,y,width,color = 58,9,8,26
        elif name == 'life':
            image = ref.image(bb=1)
            x,y,width,color = 58,22,8,26
        elif name == 'rescued-diver':
            image = ref.image(be=1)
            x,y,width,color = 58,178,8,130
        else:
            image = ref.image(a3=160 if name=='activision' else 0)
            x,y,width,color = 58,190,48,134
        actual = image[y:y+len(asset['rows']),x:x+width] == color
        expected = mask(asset['rows'],0,0,actual.shape)
        if not np.array_equal(actual,expected):
            raise ValueError(f'{name}: lettering/HUD differs from original raster')
        checks.append(dict(asset=name,passed=True,pixels=int(actual.sum())))
    edge_checks = 0
    for name,asset in assets.items():
        if name.startswith(('ball-','patrol-','early-patrol-')) or name=='torpedo':
            for x in (1,7,8,9,150,153,154,155,156,157,158,159,160):
                if name.startswith('ball-'):
                    changes = {'c7':x,'d9':int(name.split('-')[1])}
                    y = 137
                elif name.startswith('patrol-'):
                    changes = {'f6':x,'e0':int(name.split('-')[1])}
                    y = 45
                elif name.startswith('early-patrol-'):
                    changes = {'f6':x,'e0':int(name.split('-')[-1]),'e9':1}
                    y = 45
                else:
                    changes = {'e7':x,'e1':50}
                    y = 90
                baseline = ref.image(e1=50) if name=='torpedo' else blank
                actual = ref.image(**changes) != baseline
                roi = np.zeros(actual.shape,dtype=bool)
                roi[y-2:y+len(asset['rows'])+2,:] = True
                actual &= roi
                expected = mask(asset['rows'],x,y,actual.shape) if x<160 else np.zeros(actual.shape,dtype=bool)
                # The original's HMOVE bar suppresses video in X0..7. It is
                # a source display artifact, not a change to canonical masks.
                expected[:,:8] = False
                expected &= roi
                if not np.array_equal(actual,expected):
                    raise ValueError(f'{name}@{x}: reference edge clipping differs')
                edge_checks += 1
    for death in range(1,10):
        for reflect in range(2):
            for player_y in [50]+list(range(13,24)):
                name = (f'explosion-10-{reflect}' if player_y==50 else
                        f'surface-explosion-10-{reflect}-{player_y}')
                # Early death color90 equals the normal water90. Use the
                # original attract XOR for contrast, without changing masks.
                baseline = ref.image(a2=160)
                actual = ref.image(e1=player_y,e9=death,d6=reflect*8,a2=160) != baseline
                expected = mask(assets[name]['rows'],64,player_y+33,actual.shape)
                roi = np.zeros(actual.shape,dtype=bool)
                roi[player_y+31:player_y+47,40:128] = True
                if not np.array_equal(actual&roi,expected&roi):
                    raise ValueError(f'early explosion {death}, reflection{reflect}, Y{player_y}')
                checks.append(dict(asset=name,death_counter=death,passed=True))
    OUT.mkdir(parents=True,exist_ok=True)
    report = dict(original_sha256=SHA256,ale=ale_py.__version__,python=platform.python_version(),
                  scenarios=checks,edge_cases=edge_checks,passed=all(c['passed'] for c in checks))
    (OUT/'reference-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ALE shapes:',sum(c['passed'] for c in checks),'/',len(checks))
    if not report['passed']: raise ValueError('extracted shape differs from original raster')


if __name__ == '__main__': main()
