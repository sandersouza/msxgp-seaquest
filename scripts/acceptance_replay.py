"""Replay recorded devices without the feedback controller; compare every state."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/acceptance'


def relocate_replay(source,destination,rom,relative=False):
    """Relocate cartridge filenames only; keep snapshots, hashes and events."""
    root = ET.fromstring(gzip.decompress(source.read_bytes()))
    sha1 = hashlib.sha1(rom.read_bytes()).hexdigest()
    changes = 0
    for node in root.iter('rom'):
        if node.findtext('resolvedSha1')==sha1:
            for tag in ('filename','resolvedFilename'):
                node.find(tag).text = 'seaquest.rom' if relative else str(rom.resolve())
            changes += 1
    if not changes: raise ValueError('no matching candidate cartridge in replay')
    xml = ET.tostring(root,encoding='utf-8').replace(b'\0',b'\xc0\x80')
    # Preserve openMSX modified UTF-8/control-character string encoding.
    for byte in range(1,32):
        if byte not in (9,10,13): xml = xml.replace(bytes([byte]),f'&#x{byte:02X};'.encode())
    destination.write_bytes(gzip.compress(b'<?xml version="1.0"?>\n<!DOCTYPE serial SYSTEM "openmsx-serialize.dtd">\n'+xml,mtime=0))


def verify(target,rom):
    from video_check import symbols
    report = json.loads((target/'result.json').read_text())
    if hashlib.sha256(rom.read_bytes()).hexdigest()!=report['rom_sha256']:
        raise ValueError('replay cartridge identity mismatch')
    s = symbols(rom.with_suffix('.sym'))
    capture = target/'replayed-states.bin'
    script = target/'replay-check.tcl'
    count = report['source_ticks_verified']
    has_raw_trace = (target/'native.bin').exists()
    if has_raw_trace:
        relocated = target/'replay-check.omr'
        relocate_replay(target/'game.omr',relocated,rom)
    else:
        # Exercise the actual packaged relative-path OMR from the package root.
        relocated = target/'game.omr'
    script.write_text(f'''set renderer none
set throttle off
set z80_freq_locked true
set power true
reverse loadreplay -goto begin -viewonly {relocated}
set recording 0
set active 0
set count 0
set output [open {capture} wb]
debug set_bp {s['paced_frame_start']} {{!$::recording && [debug read memory 0xC7FD]==83}} {{set ::recording 1}}
debug set_bp {s['core_F5B8']} {{$::recording}} {{set ::active 1}}
debug set_bp {s['core_F00E']} {{$::active}} {{
    puts -nonewline $::output [debug read_block memory 0xC000 251]
    set ::active 0
    incr ::count
    if {{$::count=={count}}} {{close $::output; exit}}
}}
after time 1000 {{puts stderr replay-watchdog; exit 1}}
''')
    capture.unlink(missing_ok=True)
    with (target/'replay-check.log').open('w') as log:
        subprocess.run(['openmsx','-control','stdio','-machine',report['machine'],
                        '-cart',str(rom),'-romtype','ASCII16','-script',str(script)],cwd=ROOT if has_raw_trace else rom.parent,
                       env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    actual = capture.read_bytes()
    if has_raw_trace:
        data = (target/'native.bin').read_bytes()
        expected = b''.join(data[i+2052:i+2303] for i in range(0,len(data),2303))
        if actual!=expected:
            first = next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected)))
            raise ValueError(f'replay state mismatch at tick {first//251}, byte {first%251:02x}; lengths {len(actual)}/{len(expected)}')
    else:
        expected_hash = json.loads((target/'replay-result.json').read_text())['state_sha256']
        if len(actual)!=count*251 or hashlib.sha256(actual).hexdigest()!=expected_hash:
            raise ValueError('packaged replay source states differ from verified trace')
    result = dict(verdict='pass',ticks=count,state_sha256=hashlib.sha256(actual).hexdigest(),
                  replay_sha256=hashlib.sha256((target/'game.omr').read_bytes()).hexdigest(),
                  method='viewonly device replay; no feedback controller; all 251 canonical bytes on every source update')
    (target/'replay-result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'outputs/video/seaquest-issue14-final.rom')
    parser.add_argument('--target',type=Path)
    args = parser.parse_args()
    if args.target:
        print(json.dumps(verify(args.target.resolve(),args.rom.resolve())))
    else:
        summary = json.loads((OUT/'summary.json').read_text())
        reports = [dict(path=row['path'],**verify((ROOT/row['path']).parent,args.rom.resolve())) for row in summary['routes']]
        (OUT/'replay-summary.json').write_text(json.dumps(dict(verdict='pass',routes=reports),indent=2)+'\n')
        print(f'Replayed all {len(reports)} routes without feedback; every captured source state matched.')


if __name__=='__main__': main()
