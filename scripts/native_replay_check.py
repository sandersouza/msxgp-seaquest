"""Replay completed natural routes without loading their feedback controller."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

from original_graphics import read_original,extract
from presentation_check import PresentationOracle
from render_bench import check_original_sprites
from video_check import symbols

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    s=symbols(ROOT/'outputs/disk/flat.sym')
    symbol_hash=hashlib.sha256((ROOT/'outputs/disk/flat.sym').read_bytes()).hexdigest()
    rom=read_original()
    assets=extract(rom)
    oracle=PresentationOracle(rom)
    receipts=[]
    for replay in sorted(args.root.resolve().glob('*/*/game.omr')):
        folder=replay.parent
        report=json.loads((folder/'result.json').read_text())
        if report.get('verdict')!='pass':
            raise ValueError('replay source is not a passing natural route')
        if hashlib.sha256(replay.read_bytes()).hexdigest()!=report['replay_sha256']:
            raise ValueError('replay differs from its qualified route identity')
        if report['symbols_sha256']!=symbol_hash:
            raise ValueError('replay runtime symbols differ from the qualified binary')
        script=folder/'independent-replay.tcl'
        capture=folder/'independent-replay.bin'
        states=folder/'independent-replay-states.bin'
        count=report['source_ticks_verified']
        script.write_text(f'''set renderer none
set throttle off
set speed 999
set z80_freq_locked true
reverse loadreplay -goto begin -viewonly {{{replay}}}
set recording 0
set active 0
set count 0
set states [open {{{states}}} wb]
debug set_bp {s['paced_frame_start']} {{!$::recording && [debug read memory 0xC7FD]==83 && [debug read memory 0x100]==243}} {{set ::recording 1}}
debug set_bp {s['core_F5B8']} {{$::recording}} {{set ::active 1}}
debug set_bp {s['core_F00E']} {{$::active}} {{
    puts -nonewline $::states [debug read_block memory 0xC000 251]
    set ::active 0
    incr ::count
    if {{$::count>{count}}} {{puts stderr excess-replay-ticks; exit 1}}
}}
debug set_bp {s['paced_wait']} {{$::recording && $::count=={count}}} {{
    close $::states
    set f [open {{{capture}}} wb]
    puts -nonewline $f [debug read_block memory 0xC000 251]
    puts -nonewline $f [debug read_block VRAM 0 16384]
    puts -nonewline $f [binary format ccc [vdpreg 2] [vdpreg 7] [vdpreg 1]]
    puts -nonewline $f [debug read_block {{PSG regs}} 0 11]
    close $f
    exit
}}
after time 1000 {{puts stderr independent-replay-watchdog; exit 1}}
''')
        with (folder/'independent-replay.log').open('w') as log:
            subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-script',str(script)],
                           env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                           stdout=log,stderr=subprocess.STDOUT,timeout=60,check=True)
        if 'has changed since' in (folder/'independent-replay.log').read_text():
            raise ValueError('replay media differs from the frozen recording')
        data=capture.read_bytes()
        native=(folder/'native.bin').read_bytes()
        expected=b''.join(native[i+2052:i+2303] for i in range(0,len(native),2303))
        if states.read_bytes()!=expected or len(expected)!=count*251:
            raise ValueError(f'independent replay source-update mismatch: {folder.name}')
        if data[:251]!=native[-251:]:
            raise ValueError(f'independent canonical replay mismatch: {folder.name}')
        commits=[json.loads(line) for line in (folder/'timing.jsonl').read_text().splitlines()
                 if '"kind":"commit"' in line]
        tick=commits[-1]['ticks']
        state=native[(tick-1)*2303+2052:tick*2303]
        image=data[251:251+16384]
        page,backdrop,r1=data[251+16384:251+16384+3]
        oracle.check(state,image,page*1024,backdrop&15,bool(r1&64))
        check_original_sprites(state,image,assets,rom,True)
        audio=(folder/'audio-events.bin').read_bytes()
        if audio:
            expected=struct.unpack('<IH6sB11sI',audio[-28:])[4]
            if data[-11:]!=expected:
                raise ValueError(f'independent PSG replay mismatch: {folder.name}')
        receipts.append(dict(path=str(folder.relative_to(args.root.resolve())),
                             replay_sha256=hashlib.sha256(replay.read_bytes()).hexdigest(),
                             capture_sha256=hashlib.sha256(data).hexdigest(),ticks=count,
                             states_sha256=hashlib.sha256(expected).hexdigest(),
                             canonical=True,pixels=True,psg=True))
        print(f'PASS {folder.parent.name}/{folder.name}',flush=True)
    if len(receipts)!=18:
        raise ValueError(f'expected eighteen completed routes, found {len(receipts)}')
    (args.root/'independent-replays.json').write_text(json.dumps(dict(verdict='pass',routes=receipts),indent=2)+'\n')


if __name__=='__main__':
    main()
