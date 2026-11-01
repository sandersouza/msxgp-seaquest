#!/usr/bin/env python3
"""Build and launch the complete game as a normal ROM or an MSX-DOS COM."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BINARIES = {'rom': ROOT/'outputs/disk/SEAQUEST32.ROM',
            'com': ROOT/'outputs/disk/SEAQUEST.COM'}


def run_game(fmt, machine, disk):
    binary = BINARIES[fmt]
    if not binary.is_file():
        raise ValueError(f'build the game first: make build FORMAT={fmt}')
    if fmt == 'rom':
        from rom import validate_rom
        errors = validate_rom(binary.read_bytes())
        if errors:
            raise ValueError('; '.join(errors))
        subprocess.run(['openmsx', '-machine', machine, '-cart', str(binary),
                        '-romtype', 'Normal'], cwd=ROOT, check=True)
        return
    if not disk or not Path(disk).is_file():
        raise ValueError('COM launch needs DOS_DISK=/path/to/bootable-dos1.dsk '
                         'and MACHINE=<64-KiB MSX1 with a disk interface>')
    if machine.startswith('C-BIOS'):
        raise ValueError('C-BIOS cannot boot MSX-DOS; set MACHINE to a '
                         '64-KiB MSX1 with a disk interface and your own BIOS')
    # Keep the owner's system disk untouched, even if DOS writes to its disk.
    run_root = ROOT/'outputs/run'
    run_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='dos-', dir=run_root) as directory:
        target = Path(directory)
        boot = target/'boot.dsk'
        shutil.copyfile(Path(disk).resolve(), boot)
        autoexec = target/'AUTOEXEC.BAT'
        autoexec.write_bytes(b'SEAQUEST\r\n')
        env = {**os.environ, 'SEAQUEST_RUN_COM': str(binary),
               'SEAQUEST_RUN_AUTOEXEC': str(autoexec)}
        subprocess.run(['openmsx', '-machine', machine, '-diska', str(boot),
                        '-script', str(ROOT/'scripts/run_com.tcl')],
                       cwd=ROOT, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'run'))
    parser.add_argument('--format', choices=BINARIES, default='rom')
    parser.add_argument('--machine', default='C-BIOS_MSX1')
    parser.add_argument('--disk')
    args = parser.parse_args()
    try:
        if args.action == 'build':
            subprocess.run([sys.executable, '-B', str(ROOT/'scripts/build_disk.py')],
                           cwd=ROOT, check=True)
            print(f'Game: {BINARIES[args.format].relative_to(ROOT)} '
                  f'({"Normal, 32 KiB" if args.format == "rom" else "MSX-DOS 1"})')
        else:
            run_game(args.format, args.machine, args.disk)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Game operation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
