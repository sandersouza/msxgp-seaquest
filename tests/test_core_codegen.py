import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from core_codegen import decode, reachable


class CodegenTests(unittest.TestCase):
    def test_relative_target_wraps_as_6502_address(self):
        rom = bytearray(4096)
        rom[0:4] = bytes([0xa9, 0, 0xd0, 0xfc])
        item = decode(rom, 0xf002)
        self.assertEqual(item['target'], 0xf000)

    def test_reachable_does_not_decode_embedded_data(self):
        rom = bytearray(4096)
        rom[:7] = bytes([0x4c, 0x06, 0xf0, 0, 0, 0, 0x60])
        self.assertEqual(set(reachable(rom, [0xf000], set())), {0xf000, 0xf006})

    def test_unsupported_or_external_flow_fails_closed(self):
        with self.assertRaises(ValueError):
            reachable(bytes(4096), [0xf000], set())
        rom = bytearray(4096)
        rom[:3] = bytes([0x4c, 0, 0x20])
        with self.assertRaises(ValueError):
            reachable(rom, [0xf000], set())


if __name__ == '__main__':
    unittest.main()
