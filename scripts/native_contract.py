#!/usr/bin/env python3
"""Independent original-6502 versus generated-Z80 RAM differential cases."""
import json
import fcntl
import os
import random
import re
import struct
import subprocess
import sys
from pathlib import Path

from core_codegen import ROOT, main as generate


def reference(rom, ram, entry, a=0, x=0, y=0, carry=0):
    from py65.devices.mpu6502 import MPU
    memory = [0] * 65536
    memory[:1024] = ram
    memory[0xf000:] = rom
    memory[0x1ff], memory[0x1fe] = 2, 255
    mpu = MPU(memory=memory, pc=entry)
    mpu.a, mpu.x, mpu.y, mpu.p, mpu.sp = a, x, y, carry, 0xfd
    for steps in range(100000):
        mpu.step()
        if mpu.pc in (0xf00e, 0x300):
            return bytes(memory[:251]), steps + 1
    raise ValueError(f'reference did not terminate: {entry:04X}, PC={mpu.pc:04X}')


def fixtures():
    from reference_trace import capture
    from reference_inventory import ROOT
    base_trace = capture(json.loads((ROOT / 'references/scenarios/input-baseline.json').read_text()), 0)
    frames = base_trace['frames']
    result = []
    for seed in range(256):
        ram = bytearray(1024)
        ram[0x82] = seed
        result.append((f'rng-{seed}', 0xfedb, ram, 0, 0, 0, 0))
    rng = random.Random(2600)
    for n in range(256):
        ram = bytearray(1024)
        ram[0xb8:0xbb] = bytes(rng.choice([0, 0x09, 0x19, 0x99]) for _ in range(3))
        ram[0xbb] = rng.randrange(7)
        value = rng.choice([0, 0x10, 0x20, 0x50, 0x90, 0x99])
        result.append((f'bcd-{n}', 0xfb9d, ram, value, 0, 0, n & 1))
    for n, frame in enumerate(frames):
        ram = bytearray(1024)
        ram[0x80:0x100] = bytes(frame['ram'])
        ram[0xb0:0xb7] = b'\xff' * 7
        ram[0xf8] = 0
        ram[0x280], ram[0x282], ram[0x0c], ram[0x0d] = 0xff, 0x3f, 0xff, 0xff
        result.append((f'tick-{n}', 0xf5b8, ram, 0, 0x82, 0, 0))
        for key in (0xf, 0xe, 0xd, 0xb, 7):
            modified = bytearray(ram)
            modified[0x280] = (key << 4) | 15
            modified[0xc] = 0
            result.append((f'input-{n}-{key}', 0xf5b8, modified, 0, 0x82, 0, 0))
    for frame in (0, 1, 127, 255):
        ram = bytearray(1024)
        ram[0x81], ram[0x82] = frame, 87
        result.append((f'reset-{frame}', 0xfb54, ram, 0, 0, 0, 0))
    template = bytearray(1024)
    template[0x80:0x100] = bytes(frames[150]['ram'])
    template[0xb0:0xb7] = b'\xff' * 7
    template[0xf8] = 0
    template[0x280], template[0x282], template[0xc], template[0xd] = 0xff, 0x3f, 0xff, 0xff
    for player in (0, 1):
        for switches in (0x3f, 0x7f, 0xbf, 0xff, 0x3e, 0x3d):
            for phase in (0, 1, 30, 31, 127, 255):
                ram = bytearray(template)
                ram[0x80], ram[0xb7], ram[0xc2] = 1, player, 3
                ram[0x81], ram[0x282], ram[0xe1], ram[0x280] = phase, switches, 25, 0x77
                ram[0xc], ram[0xd] = 0, 0
                result.append((f'mode-{player}-{switches}-{phase}', 0xf5b8, ram, 0, 0x82, 0, 0))
    for divers in (0, 1, 5, 6):
        for oxygen in (0, 1, 16, 64):
            for state in (0, 1, 6):
                for phase in (0, 1, 15, 16, 31, 127, 255):
                    ram = bytearray(template)
                    ram[0xbe], ram[0xe6], ram[0xe8], ram[0x81] = divers, oxygen, state, phase
                    ram[0xbc], ram[0xbd] = 19, 0
                    result.append((f'surface-{divers}-{oxygen}-{state}-{phase}', 0xf5b8, ram, 0, 0x82, 0, 0))
    for lane in range(4):
        for hit in (0xb4, 0xb5, 0xb6):
            for enemy_type in (0, 4, 8, 12):
                ram = bytearray(template)
                ram[hit], ram[0xd9+lane], ram[0xa4+lane] = lane, enemy_type, 7
                ram[0xc7+lane], ram[0xe7], ram[0xe1] = 76, 80, 50
                result.append((f'collision-{lane}-{hit}-{enemy_type}', 0xf5b8, ram, 0, 0x82, 0, 0))
    # Replay canonical state continuously. Only the environment's named hardware
    # samples/latches are injected after the first reset; game RAM is NOT reloaded.
    rom = (ROOT / 'references/roms/seaquest-atari2600.a26').read_bytes()
    ram = bytearray(template)
    ram[0x81], ram[0x82] = 252, 87
    result.append(('chain-reset', 0xfb54, bytearray(ram), 0, 0, 0, 0))
    previous, _ = reference(rom, list(ram), 0xfb54)
    ram[:251] = previous
    for tick in range(480):
        ram[0xb0:0xb7], ram[0xf8] = b'\xff' * 7, 0
        ram[0xf9] = 15 if ram[0xe1] != 13 and 0 < ram[0xe6] <= 16 and not ram[0xe9] else 0
        nibble = 15 if tick < 150 else (7 if tick < 170 else (11 if tick < 190 else (13 if tick < 240 else 14)))
        ram[0x280], ram[0x282] = (nibble << 4) | nibble, 0x3f
        ram[0xc] = ram[0xd] = 0 if tick >= 190 else 255
        if tick == 250:
            ram[0x282] = 0x3d  # actual original Select path
        if tick == 251:
            ram[0x282] = 0x3e  # actual original Reset path, retain seed/phase
        if tick == 350:
            ram[0xb5] = 0      # hardware collision input, then native death/player swap
        result.append((f'chain-{tick}', 0xf5b8, bytearray(ram), 0, 0x82, 0, 0, 1))
        previous, _ = reference(rom, list(ram), 0xf5b8, 0, 0x82)
        ram[:251] = previous
    return result


def main():
    (ROOT / 'outputs/native').mkdir(parents=True, exist_ok=True)
    lock = (ROOT / 'outputs/native/.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if generate():
        return 1
    out = ROOT / 'outputs/native'
    assembler = ROOT / '.tools/sjasmplus/sjasmplus'
    subprocess.run([str(assembler), '--nologo', '--raw=' + str(out / 'contract.rom'),
                    '--sym=' + str(out / 'contract.sym'), str(ROOT / 'src/core_contract.asm')], check=True)
    symbols = {name: int(address, 16) for name, address in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)', (out / 'contract.sym').read_text(), re.M)}
    rom = (ROOT / 'references/roms/seaquest-atari2600.a26').read_bytes()
    cases = fixtures()
    records, count_steps = [], []
    for case in cases:
        name, entry, ram, a, x, y, carry = case[:7]
        chained = case[7] if len(case) > 7 else 0
        expected, steps = reference(rom, list(ram), entry, a, x, y, carry)
        records.append(struct.pack('<HBBBBBB', symbols[f'core_{entry:04X}'], 0, a, y, x, carry, chained) + ram + expected)
        count_steps.append(steps)
    (out / 'cases.bin').write_bytes(b''.join(records))
    (out / 'case-index.json').write_text(json.dumps([c[0] for c in cases]))
    inject = int(os.environ.get('SEAQUEST_INJECT_CASE', '-1'))
    (out / 'start.tcl').write_text(f'set inject_case {inject}\nset rpc_start {symbols["rpc_start"]}\nset rpc_done {symbols["rpc_done"]}\nsource scripts/native_contract.tcl\n')
    result_file = out / 'result.json'
    result_file.unlink(missing_ok=True)
    env = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}
    with subprocess.Popen(['openmsx', '-control', 'stdio', '-machine', 'C-BIOS_MSX1',
                           '-cart', str(out / 'contract.rom'), '-script', str(out / 'start.tcl')],
                          cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise ValueError('native contract timeout')
        (out / 'openmsx.log').write_bytes(process.stdout.read())
    if not result_file.exists():
        raise ValueError('native contract did not produce a result')
    result = json.loads(result_file.read_text())
    if process.returncode != 0 or (result['passed'] and result['cases'] != len(cases)):
        raise ValueError('native contract ended without completing its own full case set')
    result['total_cases'] = len(cases)
    result['max_reference_instructions'] = max(count_steps)
    if not result['passed']:
        result['failed_case'] = cases[result['cases']][0]
    print(json.dumps(result))
    return int(not result['passed'])


if __name__ == '__main__':
    sys.exit(main())
