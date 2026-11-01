"""Run issue #15's serial matrix against a frozen, already-built cartridge."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/acceptance'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'outputs/video/seaquest-issue14-final.rom')
    parser.add_argument('--delivery',choices=('ascii16','dos','plain32'),default='ascii16')
    parser.add_argument('--disk',type=Path)
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--ntsc-machine',default='C-BIOS_MSX1')
    parser.add_argument('--pal-machine',default='C-BIOS_MSX1_EU')
    parser.add_argument('--output-root',type=Path,default=OUT)
    args = parser.parse_args()
    rom = args.rom.resolve()
    harness_files=('video_check.py','video_check.tcl','full_game.tcl','full_game_reference.py','oxygen_natural.tcl')
    if args.delivery!='ascii16':
        harness_files+=('native_video.py',)
    identity = dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                    symbols_sha256=hashlib.sha256(rom.with_suffix('.sym').read_bytes()).hexdigest(),
                    harness_sha256=hashlib.sha256(b''.join((ROOT/'scripts'/name).read_bytes() for name in harness_files)).hexdigest())
    reports = []
    target_root=args.output_root.resolve()
    target_root.mkdir(exist_ok=True,parents=True)
    for machine,region in ((args.ntsc_machine,'ntsc'),(args.pal_machine,'pal')):
        routes = [(mode,difficulty,'exhaust',5000) for mode in (0,1) for difficulty in (0,64,128,192)]
        routes += [(0,0,'rescue',8000)]
        for mode,difficulty,controller,frames in routes:
            name = f'fullgame-m{mode}-d{difficulty}-{controller}-normal'
            target = target_root/machine/name
            receipt = target/'identity.json'
            result = target/'result.json'
            receipt.unlink(missing_ok=True)
            result.unlink(missing_ok=True)
            print(f'Checking {machine}/{name}',flush=True)
            delivery_args=['--delivery',args.delivery,'--region',region]
            if args.disk:
                delivery_args+=['--disk',str(args.disk.resolve())]
            if args.runtime:
                delivery_args+=['--runtime',str(args.runtime.resolve())]
            subprocess.run([sys.executable,'-B',str(ROOT/'scripts/video_check.py'),
                            '--rom',str(rom),'--machine',machine,'--scenario','fullgame',
                            '--mode',str(mode),'--difficulty',str(difficulty),'--controller',controller,
                            '--frames',str(frames),'--output-root',str(target_root),*delivery_args],cwd=ROOT,check=True)
            receipt.write_text(json.dumps(identity,indent=2)+'\n')
            report = json.loads(result.read_text())
            if report.get('verdict')!='pass' or any(report.get(k)!=identity[k] for k in ('rom_sha256','symbols_sha256')):
                raise ValueError(f'not a passing result for the frozen candidate: {result}')
            reports.append(dict(path=str(result.relative_to(ROOT)),**report))
    summary = dict(verdict='pass',**identity,routes=reports,physical_hardware=False,
                   manual_emulator_visual_audio='pending owner observation')
    (target_root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'Passed {len(reports)} full-game/rescue routes for the exact frozen ROM.',flush=True)


if __name__=='__main__': main()
