#!/usr/bin/env python3
"""Bounded isolated openMSX diagnostic; requires a fresh explicit pass record."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'outputs/smoke-result.json'


def main():
    from rom import ROM, validate_rom
    try:
        data = ROM.read_bytes()
        if validate_rom(data):
            raise ValueError('build a valid diagnostic ROM before running smoke')
        RESULT.unlink(missing_ok=True)
        command = ['openmsx', '-control', 'stdio', '-machine', 'C-BIOS_MSX1',
                   '-cart', str(ROM), '-script', 'scripts/smoke.tcl']
        env = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}
        with subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise ValueError('diagnostic timed out; no boot acceptance claimed')
            log = process.stdout.read().decode(errors='replace')
            (ROOT / 'outputs/smoke.log').write_text(log)
            if process.returncode or not RESULT.exists():
                raise ValueError(f'no fresh successful diagnostic result; see outputs/smoke.log ({process.returncode})')
        result = json.loads(RESULT.read_text())
        if result.get('passed') is not True:
            raise ValueError('diagnostic did not pass')
        result.update({'machine': 'C-BIOS_MSX1', 'ram_kib': 64, 'vram_kib': 16,
                       'vdp': 'TMS9918A', 'video_hz': 60, 'rom_sha256': hashlib.sha256(data).hexdigest(),
                       'emulator': subprocess.check_output(['openmsx', '--version'], text=True).strip(),
                       'acceptance': 'diagnostic boot only; no gameplay/hardware validation'})
        RESULT.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Smoke failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
