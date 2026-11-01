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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
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
        script=folder/'independent-replay.tcl'
        capture=folder/'independent-replay.bin'
        script.write_text(f'''set renderer none
set throttle off
set speed 999
reverse loadreplay -goto savetime -viewonly {{{replay}}}
set f [open {{{capture}}} wb]
puts -nonewline $f [debug read_block memory 0xC000 251]
puts -nonewline $f [debug read_block VRAM 0 16384]
puts -nonewline $f [binary format ccc [vdpreg 2] [vdpreg 7] [vdpreg 1]]
puts -nonewline $f [debug read_block {{PSG regs}} 0 11]
close $f
exit
''')
        with (folder/'independent-replay.log').open('w') as log:
            subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-script',str(script)],
                           env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                           stdout=log,stderr=subprocess.STDOUT,timeout=60,check=True)
        if 'has changed since' in (folder/'independent-replay.log').read_text():
            raise ValueError('replay media differs from the frozen recording')
        data=capture.read_bytes()
        native=(folder/'native.bin').read_bytes()
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
                             capture_sha256=hashlib.sha256(data).hexdigest(),canonical=True,pixels=True,psg=True))
        print(f'PASS {folder.parent.name}/{folder.name}',flush=True)
    if len(receipts)!=18:
        raise ValueError(f'expected eighteen completed routes, found {len(receipts)}')
    (args.root/'independent-replays.json').write_text(json.dumps(dict(verdict='pass',routes=receipts),indent=2)+'\n')


if __name__=='__main__':
    main()
