import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reference_trace import compare_traces, expand_scenario


class TraceTests(unittest.TestCase):
    def test_first_changed_ram_byte_is_reported(self):
        first = {'identity': {'rom': 'same'}, 'frames': [{'index': 0, 'action': None, 'frame': 0, 'ram': [0] * 128}]}
        second = {'identity': {'rom': 'same'}, 'frames': [{'index': 0, 'action': None, 'frame': 0, 'ram': [0] * 128}]}
        self.assertIsNone(compare_traces(first, second))
        second['frames'][0]['ram'][70] = 1
        self.assertEqual(compare_traces(first, second), {'kind': 'ram', 'index': 0, 'address': 0xc6, 'expected': 0, 'actual': 1})

    def test_identity_and_trace_length_are_not_ignored(self):
        self.assertEqual(compare_traces({'identity': 1, 'frames': []}, {'identity': 2, 'frames': []})['kind'], 'identity')
        trace = {'identity': 1, 'frames': [{'index': 0, 'action': None, 'frame': 0, 'ram': [0] * 128}]}
        self.assertEqual(compare_traces(trace, {'identity': 1, 'frames': []})['kind'], 'length')

    def test_input_frame_alignment_is_not_ignored(self):
        first = {'identity': 1, 'frames': [{'index': 0, 'action': 'LEFT', 'frame': 7, 'ram': [0] * 128}]}
        second = {'identity': 1, 'frames': [{'index': 0, 'action': 'RIGHT', 'frame': 7, 'ram': [0] * 128}]}
        self.assertEqual(compare_traces(first, second)['kind'], 'action')

    def test_scenario_validation_and_expansion(self):
        self.assertEqual(expand_scenario({'steps': [{'action': 'RIGHT', 'frames': 2}]}), ['RIGHT', 'RIGHT'])
        for step in ({'action': 'RESET', 'frames': 1}, {'action': 'UP', 'frames': 0}, {'action': 'UP', 'frames': -1}):
            with self.assertRaises(ValueError):
                expand_scenario({'steps': [step]})


if __name__ == '__main__':
    unittest.main()
