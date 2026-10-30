#!/usr/bin/env python3
"""Run real-ROM deterministic/phase probes without claiming full #6 acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import sys

from reference_inventory import ROOT, main as verify_inputs
from reference_trace import capture, compare_traces


def main():
    try:
        if verify_inputs([]):
            return 1
        scenario = json.loads((ROOT / 'references/scenarios/input-baseline.json').read_text())
        first, second = capture(scenario, 0), capture(scenario, 0)
        difference = compare_traces(first, second)
        if difference:
            raise ValueError(f'independent replay mismatch: {difference}')
        frames = first['frames']
        if not all((b['ram'][1] - a['ram'][1]) % 256 == 1 for a, b in zip(frames, frames[1:])):
            raise ValueError('ROM frame counter did not advance once per capture')
        checkpoints = {0: (76, 13, 0), 150: (76, 13, 64), 170: (96, 13, 64),
                       190: (76, 13, 64), 195: (76, 18, 64), 208: (76, 13, 64)}
        for index, expected in checkpoints.items():
            ram = frames[index]['ram']
            if (ram[0xc6-0x80], ram[0xe1-0x80], ram[0xe6-0x80]) != expected:
                raise ValueError(f'position/oxygen probe failed at {index}')
        hard = capture(scenario, 1)
        if frames[203]['ram'][103] != 44 or hard['frames'][203]['ram'][103] != 60:
            raise ValueError('B/A leftward firing displacement probe failed')
        mutated = copy.deepcopy(first)
        mutated['frames'][170]['ram'][70] ^= 1
        detected = compare_traces(first, mutated)
        if detected != {'kind': 'ram', 'index': 170, 'address': 0xc6, 'expected': 96, 'actual': 97}:
            raise ValueError(f'injected mismatch not detected correctly: {detected}')
        out = ROOT / 'outputs/traces'
        out.mkdir(parents=True, exist_ok=True)
        for name, trace in (('baseline-b', first), ('baseline-b-repeat', second), ('baseline-left-a', hard)):
            (out / f'{name}.json').write_text(json.dumps(trace, separators=(',', ':')) + '\n')
        summary = {'schema_version': 1, 'identity': first['identity'], 'snapshots_per_run': len(frames),
                   'independent_replays_match': True, 'frame_counter_step': 1,
                   'initial_frame_phase': frames[0]['ram'][1], 'initial_rom_seed': frames[0]['ram'][2],
                   'initial_ram_sha256': hashlib.sha256(bytes(frames[0]['ram'])).hexdigest(),
                   'input_and_refill_probes_passed': True, 'firing_b_x_after_8': 44, 'firing_a_x_after_8': 60,
                   'injected_difference': detected,
                   'acceptance': 'initial solo post-frame capture only; full #6 remains open'}
        (out / 'probe-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary))
        return 0
    except (OSError, ValueError, KeyError, ImportError, RuntimeError) as error:
        print(f'Reference trace probe failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
