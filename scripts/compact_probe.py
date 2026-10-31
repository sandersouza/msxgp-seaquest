"""Reproduce #35's rejected 8 KiB enemy-cache experiment, not a release build.

First run the complete existing baseline oracle, then replay the same fixtures
against the experiment and compare canonical RAM and complete VRAM bytewise.
Keep all cartridges, dumps and generated wrapper sources under ignored outputs/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/issue35/probe'
BASE = ROOT/'outputs/render'
FLAGS = ('WITH_NATIVE', 'WITH_GRAPHICS', 'WITH_INPUT', 'WITH_COLLISIONS',
         'WITH_STREAM', 'WITH_PACKED_DATA', 'WITH_HUD', 'WITH_AUDIO',
         'WITH_PALETTE', 'WITH_BANKED')


def symbols(path):
    return {n: int(v, 16) for n, v in re.findall(
        r'^(\w+): EQU 0x([0-9A-Fa-f]+)', path.read_text(), re.M)}


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'baseline layout changed; re-audit marker: {old}')
    return source.replace(old, new)


def build():
    source = (ROOT/'src/render_bench.asm').read_text()
    source = replace_once(source, 'INCLUDE "enemy_banked.asm"',
                          f'INCLUDE "{ROOT}/src/experiments/compact_enemy.asm"')
    source = replace_once(source, 'INCBIN "../outputs/presentation/enemy-pointers.bin"',
                          '; unused prepared-transfer pointer table omitted')
    source = replace_once(source, 'INCBIN "../outputs/presentation/enemy-patterns.bin",0,$4000',
                          'INCBIN "../outputs/collision/enemy-cache.bin"\n    DS $C000-$,$FF')
    source = re.sub(r'(INCLUDE|INCBIN) "([^"]+)"', lambda m:
                    f'{m[1]} "{(ROOT/"src"/m[2]).resolve()}"'
                    if not Path(m[2]).is_absolute() else m[0], source)
    asm = OUT/'probe.asm'
    asm.write_text(source)
    with (OUT/'build.log').open('w') as log:
        subprocess.run([str(ROOT/'.tools/sjasmplus/sjasmplus'), '--nologo',
                        '--raw='+str(OUT/'bench.rom'), '--sym='+str(OUT/'bench.sym'),
                        *('-D'+flag for flag in FLAGS), str(asm)], cwd=ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    current, baseline = symbols(OUT/'bench.sym'), symbols(BASE/'bench.sym')
    if any(current.get(n) != v for n, v in baseline.items() if n.startswith('core_')):
        raise ValueError('native entry addresses changed; fixtures need relocation')
    return current


def emulator(script, log_name, timeout=300):
    with (OUT/log_name).open('w') as log:
        result = subprocess.run(['openmsx', '-control', 'stdio', '-machine', 'C-BIOS_MSX1',
                                 '-cart', str(OUT/'bench.rom'), '-romtype', 'ASCII16',
                                 '-script', str(script)], cwd=ROOT,
                                env={**os.environ, 'SDL_VIDEODRIVER': 'dummy',
                                     'SDL_AUDIODRIVER': 'dummy'},
                                stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise ValueError(f'openMSX failed: {OUT/log_name}')


def compare(count):
    # The oracle's first251 bytes are canonical. Remaining RAM is platform state.
    # Full actual VRAM, including both visible and inactive pages, must match.
    for file, size, keep in (('state.bin', 1024, 251), ('vram.bin', 16384, 16384),
                             ('prepared.bin', 16384, 16384), ('baseline.bin', 16384, 16384),
                             ('name-pages.bin', 3, 3), ('registers.bin', 8, 8),
                             ('phase-registers.bin', 4, 4)):
        with (OUT/file).open('rb') as actual, (BASE/file).open('rb') as expected:
            for index in range(count):
                a, b = actual.read(size), expected.read(size)
                if len(a) != size or len(b) != size or a[:keep] != b[:keep]:
                    raise ValueError(f'{file} mismatch in case {index}')
            if actual.read(1) or expected.read(1):
                raise ValueError(f'trailing {file} records')


def run_probe(s):
    for name in ('complete.txt', 'result.json', 'pace.json'):
        (OUT/name).unlink(missing_ok=True)
    shutil.copyfile(BASE/'cases.bin', OUT/'cases.bin')
    script = f'set bench_dir {{{OUT}}}\nset input_mode 1\nset hud_mode 1\nset palette_mode 1\nset inject_pixel -1\n'
    script += f'set prime_entry {s["core_F00E"]}\nset prime_start {s["audio_prime_start"]}\n'
    script += ''.join(f'set {n} {s[n]}\n' for n in ('rpc_start', 'rpc_done'))
    script += f'set commit_pc {s["render_commit"]}\nsource scripts/render_bench.tcl\n'
    start = OUT/'start.tcl'
    start.write_text(script)
    emulator(start, 'openmsx.log')
    names = json.loads((BASE/'case-index.json').read_text())
    count = int((OUT/'complete.txt').read_text())
    if count != len(names):
        raise ValueError('incomplete fixture replay')
    compare(count)
    cycles = [int(v) for v in (OUT/'cycles.txt').read_text().split()]
    if len(cycles) != count:
        raise ValueError('incomplete timing records')
    worst = cycles.index(max(cycles))
    with (OUT/'cases.bin').open('rb') as cases:
        cases.seek(worst*1034)
        case = cases.read(1034)
    if len(case) != 1034:
        raise ValueError('truncated worst-case fixture')
    (OUT/'worst-case.bin').write_bytes(case[10:])
    pace = (ROOT/'scripts/render_pace.tcl').read_text().replace('outputs/render/', str(OUT)+'/')
    (OUT/'pace.tcl').write_text(pace)
    keys = case[6:10]
    controls = ''.join(f'keymatrixdown {r} {m}\n' for r, m in zip((6, 7, 8), keys[:3]))
    controls += f'debug write memory 0xC420 {keys[3]}\n'
    script = ''.join(f'set {n} {s[n]}\n' for n in (
        'paced_commit', 'paced_frame_start', 'paced_start', 'paced_wait',
        'paced_prepared', 'vblank_sample', 'vblank_clear_sample', 'rpc_start', 'rpc_done'))
    script += f'set hud_mode 1\nset prime_entry {s["core_F00E"]}\nset prime_start {s["audio_prime_start"]}\n'
    script += 'set input_setup {'+controls+'}\nsource {'+str(OUT/'pace.tcl')+'}\n'
    start = OUT/'pace-start.tcl'
    start.write_text(script)
    emulator(start, 'pace.log', 30)
    paced = json.loads((OUT/'pace.json').read_text())
    steps = sorted(set(b-a for a, b in zip(paced['frame_counts'], paced['frame_counts'][1:])))
    io = json.loads((OUT/'io.json').read_text())
    passing = (max(cycles) < 59736 and paced['max_busy_cycles'] < 59736 and
               paced['frames'] == 241 and steps == [1] and
               io['min_active_spacing'] >= 29 and io['min_data_spacing'] >= 12 and
               all(not 0 <= y < 192 for y in paced['commit_start_y']+paced['commit_end_y']))
    report = dict(verdict='pass' if passing else 'rejected_timing_or_io',
                  experiment='8 KiB exact enemy LUT; 128 KiB ASCII16 diagnostic only',
                  rom_bytes=(OUT/'bench.rom').stat().st_size,
                  rom_sha256=hashlib.sha256((OUT/'bench.rom').read_bytes()).hexdigest(),
                  baseline_sha256=hashlib.sha256((BASE/'bench.rom').read_bytes()).hexdigest(),
                  probe_source_sha256=hashlib.sha256((ROOT/'src/experiments/compact_enemy.asm').read_bytes()).hexdigest(),
                  cases=count, canonical_state_and_full_vram_equal=True,
                  vdp_registers_and_pages_equal=True,
                  max_cycles=max(cycles), worst_case=names[worst],
                  cpu_margin_cycles=59736-max(cycles), io=io,
                  paced_frames=240, paced_max_busy_cycles=paced['max_busy_cycles'],
                  paced_frame_steps=steps, stack_min=paced['stack_min'],
                  min_period_cycles=min(paced['periods']), max_period_cycles=max(paced['periods']),
                  psg_and_full_game_validated=False, disk_or_plain32_validated=False)
    (OUT/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    return passing


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('result.json', 'complete.txt', 'pace.json'):
        (OUT/name).unlink(missing_ok=True)
    with (OUT/'baseline.log').open('w') as log:
        subprocess.run([sys.executable, '-B', str(ROOT/'scripts/render_bench.py'),
                        '--palette', '--progression'], cwd=ROOT, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    if not run_probe(build()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
