#!/usr/bin/env python3
"""Initial post-frame Atari reference captures; does not certify native alignment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from reference_inventory import ROOT, main as verify_inputs

ACTIONS = {'NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN', 'UPRIGHT', 'UPLEFT',
           'DOWNRIGHT', 'DOWNLEFT', 'UPFIRE', 'RIGHTFIRE', 'LEFTFIRE', 'DOWNFIRE',
           'UPRIGHTFIRE', 'UPLEFTFIRE', 'DOWNRIGHTFIRE', 'DOWNLEFTFIRE'}


def expand_scenario(scenario):
    result = []
    for step in scenario['steps']:
        count = step['frames']
        if step['action'] not in ACTIONS or type(count) is not int or not 1 <= count <= 10000:
            raise ValueError('scenario requires supported joystick actions and frame counts 1..10000')
        result.extend([step['action']] * count)
        if len(result) > 100000:
            raise ValueError('scenario exceeds 100000 frames')
    if not result:
        raise ValueError('empty scenario')
    return result


def compare_traces(expected, actual):
    if expected['identity'] != actual['identity']:
        return {'kind': 'identity', 'expected': expected['identity'], 'actual': actual['identity']}
    for index, (left, right) in enumerate(zip(expected['frames'], actual['frames'])):
        for key in ('index', 'action', 'frame'):
            if left[key] != right[key]:
                return {'kind': key, 'index': index, 'expected': left[key], 'actual': right[key]}
        if len(left['ram']) != 128 or len(right['ram']) != 128:
            raise ValueError('snapshots must contain all 128 RAM bytes')
        for address, (a, b) in enumerate(zip(left['ram'], right['ram'])):
            if a != b:
                return {'kind': 'ram', 'index': index, 'address': address + 0x80, 'expected': a, 'actual': b}
    if len(expected['frames']) != len(actual['frames']):
        return {'kind': 'length', 'expected': len(expected['frames']), 'actual': len(actual['frames'])}
    return None


def capture(scenario, difficulty):
    import ale_py
    import numpy
    if ale_py.__version__ != '0.12.1':
        raise ValueError('reference backend must be ale-py 0.12.1')
    actions = expand_scenario(scenario)
    ale = ale_py.ALEInterface()
    ale.setInt('random_seed', 0)
    ale.setInt('frame_skip', 1)
    ale.setFloat('repeat_action_probability', 0.0)
    ale.setBool('display_screen', False)
    ale.setBool('sound', False)
    rom = ROOT / 'references/roms/seaquest-atari2600.a26'
    ale.loadROM(str(rom))
    ale.setMode(0)
    ale.setDifficulty(difficulty)
    ale.reset_game()
    identity = {
        'schema_version': 1, 'backend': 'ale-py', 'backend_version': ale_py.__version__,
        'numpy_version': numpy.__version__, 'rom_sha256': hashlib.sha256(rom.read_bytes()).hexdigest(),
        'frame_skip': 1, 'sticky_action_probability': 0.0, 'random_seed': 0,
        'mode': 0, 'left_difficulty': 'A' if difficulty else 'B', 'right_difficulty': 'B',
        'reset_policy': 'loadROM; setMode(0); setDifficulty; reset_game (ALE warmup and soft resets)',
        'boundary': 'RAM after ALE act completes one frame; not an arbitrary PC/cycle boundary',
        'scenario_sha256': hashlib.sha256(json.dumps(scenario, sort_keys=True).encode()).hexdigest(),
    }
    frames = []
    def snapshot(action):
        frames.append({'index': len(frames), 'action': action, 'frame': ale.getFrameNumber(),
                       'ram': [int(value) for value in ale.getRAM()]})
    snapshot(None)
    for action in actions:
        ale.act(getattr(ale_py.Action, action))
        snapshot(action)
    return {'identity': identity, 'frames': frames}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture_args = sub.add_parser('capture')
    capture_args.add_argument('--scenario', type=Path, default=ROOT / 'references/scenarios/input-baseline.json')
    capture_args.add_argument('--difficulty', choices=(0, 1), type=int, default=0)
    capture_args.add_argument('--output', type=Path, default=ROOT / 'outputs/traces/input-baseline.json')
    compare_args = sub.add_parser('compare')
    compare_args.add_argument('expected', type=Path)
    compare_args.add_argument('actual', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'capture':
            if verify_inputs([]):
                return 1
            scenario = json.loads(args.scenario.read_text())
            trace = capture(scenario, args.difficulty)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(trace, separators=(',', ':')) + '\n')
            print(f"Captured {len(trace['frames'])} snapshots to {args.output}; initial ROM frame={trace['frames'][0]['ram'][1]}")
            return 0
        difference = compare_traces(json.loads(args.expected.read_text()), json.loads(args.actual.read_text()))
        print(json.dumps(difference or {'match': True}))
        return int(difference is not None)
    except (OSError, ValueError, KeyError, ImportError, RuntimeError) as error:
        print(f'Reference trace failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
