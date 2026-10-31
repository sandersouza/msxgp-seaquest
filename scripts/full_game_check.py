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
    args = parser.parse_args()
    rom = args.rom.resolve()
    identity = dict(rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                    symbols_sha256=hashlib.sha256(rom.with_suffix('.sym').read_bytes()).hexdigest(),
                    harness_sha256=hashlib.sha256(b''.join((ROOT/'scripts'/name).read_bytes() for name in
                        ('video_check.py','video_check.tcl','full_game.tcl','full_game_reference.py','oxygen_natural.tcl'))).hexdigest())
    reports = []
    OUT.mkdir(exist_ok=True)
    for machine in ('C-BIOS_MSX1','C-BIOS_MSX1_EU'):
        routes = [(mode,difficulty,'exhaust',5000) for mode in (0,1) for difficulty in (0,64,128,192)]
        routes += [(0,0,'rescue',8000)]
        for mode,difficulty,controller,frames in routes:
            name = f'fullgame-m{mode}-d{difficulty}-{controller}-normal'
            target = OUT/machine/name
            receipt = target/'identity.json'
            result = target/'result.json'
            receipt.unlink(missing_ok=True)
            result.unlink(missing_ok=True)
            print(f'Checking {machine}/{name}',flush=True)
            subprocess.run([sys.executable,'-B',str(ROOT/'scripts/video_check.py'),
                            '--rom',str(rom),'--machine',machine,'--scenario','fullgame',
                            '--mode',str(mode),'--difficulty',str(difficulty),'--controller',controller,
                            '--frames',str(frames),'--output-root',str(OUT)],cwd=ROOT,check=True)
            receipt.write_text(json.dumps(identity,indent=2)+'\n')
            report = json.loads(result.read_text())
            if report.get('verdict')!='pass' or any(report.get(k)!=identity[k] for k in ('rom_sha256','symbols_sha256')):
                raise ValueError(f'not a passing result for the frozen candidate: {result}')
            reports.append(dict(path=str(result.relative_to(ROOT)),**report))
    summary = dict(verdict='pass',**identity,routes=reports,physical_hardware=False,
                   manual_emulator_visual_audio='pending owner observation')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'Passed {len(reports)} full-game/rescue routes for the exact frozen ROM.',flush=True)


if __name__=='__main__': main()
