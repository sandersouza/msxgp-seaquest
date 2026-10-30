#!/usr/bin/env python3
"""Local original-coordinate occupancy oracle; source-derived masks stay ignored."""
from original_graphics import bitmap, extract, read_original
from pathlib import Path


def contacts(ram, data=None, assets=None):
    data = read_original() if data is None else data
    assets = extract(data) if assets is None else assets
    frame = ram[0xe0]
    death = ram[0xe9]
    reflect = int(bool(ram[0xd6] & 8))
    name = (f'explosion-{max(death,10)}-{reflect}' if 0 < death < 15
            else f'player-{frame}-{reflect}')
    player_top = ram[0xe1]+33
    player = {(player_top+y,(ram[0xc6]+x)%160)
              for y,row in enumerate(assets[name]['rows']) for x in row
              if not 53 <= player_top+y <= 56}
    missile = {(ram[0xe1]+40,(ram[0xe7]+x)%160) for x in range(8)}
    result = [255]*7
    patrol_rows = (bitmap(data,0xfd00+data[0xcfb+frame]+4,8,True) if 0<death<10
                   else assets[f'patrol-{frame}']['rows'])
    patrol = {(45+y,((ram[0xf6] if ram[0xf6]<160 else 0)+x)%160)
              for y,row in enumerate(patrol_rows) for x in row}
    surface = 7 | (128 if player & patrol else 0)
    for lane in reversed(range(4)):
        base = ram[0x9e+lane]
        mask = ram[0xa4+lane] & data[0xeeb+((base-128)//16 if base>=128 else 8)]
        x = 0 if not mask else (base+data[0xf51+mask]) & 255
        if x>=160: x-=96
        mode = data[0xef4+mask]
        copies = {0:(0,),1:(0,16),2:(0,32),3:(0,16,32)}[mode]
        kind = ram[0xd9+lane]&15
        animation = ram[0xdd] if kind&7<4 else 0
        rows = assets[f'enemy-{kind}-{animation}']['rows']
        top = 65+24*(3-lane)
        enemy = {(top+y,(x+copy+dx)%160) for y,row in enumerate(rows)
                 for dx in row for copy in copies}
        bx = ram[0xc7+lane] if ram[0xc7+lane]<160 else 0
        ball = {(top+y,(bx+dx)%160) for y,row in enumerate(assets[f'ball-{kind}']['rows']) for dx in row}
        if player & ball: result[6] = lane
        if missile & enemy: result[4] = lane
        if enemy & ball: result[lane] = lane
        if player & enemy: result[5] = lane
    return bytes(result)+bytes([surface])


def generate(data=None):
    data = read_original() if data is None else data
    assets = extract(data)
    out = Path(__file__).resolve().parents[1]/'outputs/collision'
    out.mkdir(parents=True,exist_ok=True)
    names = [f'player-{f}-{r}' for f in range(3) for r in range(2)]
    names += [f'explosion-{d}-{r}' for d in range(10,15) for r in range(2)]
    if any(assets[name]['rows'][11] for name in names):
        raise ValueError('collision kernel requires verified zero player row11')
    sequences, indices = [], []
    for name in names:
        for dx in range(-7,17):
            row = bytes(sum(128>>x for x in range(8) if x+dx in pixels)
                        for pixels in assets[name]['rows'])
            if row not in sequences: sequences.append(row)
            indices.append(sequences.index(row))
    lines = ['; Local original-derived collision data. Do not publish.', 'collision_projections:']
    lines += ['    DW collision_rows+%d' % (i*12) for i in indices]
    lines += ['collision_rows:']
    for row in sequences: lines += ['    DB '+','.join(str(v) for v in row)]
    lines += ['collision_balls:']
    for kind in range(16):
        lines += ['    DB '+','.join(str(sum(128>>x for x in row)) for row in reversed(assets[f'ball-{kind}']['rows']))]
    lines += ['collision_enemy_ball:']
    for kind in range(16):
        for animation in range(8):
            if kind&7 in (3,7):
                bits = 0  # Unreachable source animation indices.
            else:
                enemy = assets[f'enemy-{kind}-{animation if kind&7<4 else 0}']['rows']
                ball = assets[f'ball-{kind}']['rows']
                bits = sum(1<<(dx+7) for dx in range(-7,8)
                           if any(set(erow) & {x+dx for x in brow} for erow,brow in zip(enemy,ball)))
            lines += ['    DW '+str(bits)]
    lines += ['collision_player_heights:',
              '    DB '+','.join(str((assets[f'explosion-{max(n,10)}-0']['bounds'] or [0,0,0,-1])[3]+1) if n else '0' for n in range(15)),
              'collision_normal_heights:',
              '    DB '+','.join(str((assets[f'player-{n}-0']['bounds'] or [0,0,0,-1])[3]+1) for n in range(3))]
    (out/'masks.inc').write_text('\n'.join(lines)+'\n')
    # Every reachable enemy pointer lies in FDA4..FDF8. A full85-row,
    # three-column cache fits in255 bytes per parity/phase/reflection page.
    # This avoids per-row lookup and reflection during the active display.
    from render_tables import shifted_row
    cache = bytearray()
    for reflect in range(2):
        for parity in range(2):
            for phase in range(8):
                rows = data[0xda4:0xdf9]
                if reflect: rows = bytes(int(f'{v:08b}'[::-1],2) for v in rows)
                cache += bytes(shifted_row(v,phase,parity)[column] for column in range(3) for v in rows)
                cache.append(0)
    (out/'enemy-cache.bin').write_bytes(cache)
    (out/'clip-masks.bin').write_bytes(bytes(data[0xeeb+(8 if x<128 else (x-128)//16)] for x in range(256)))
    return assets


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic',action='store_true')
    args = parser.parse_args()
    generate(bytes(4096) if args.synthetic else None)
