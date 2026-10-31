import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from hud_tables import compress, decompress
from hud_reference import logo_top


class HudTests(unittest.TestCase):
    def test_startup_codec_handles_literals_overlapping_matches_and_high_bytes(self):
        for data in (b'', bytes(range(256)), bytes(range(256))*4,
                     b'A'*400, b'AB'*257, bytes(range(256))+b'XYZ'*200):
            self.assertEqual(decompress(compress(data)), data)

    def test_original_logo_counter_windows_and_wrap_boundaries(self):
        self.assertEqual([logo_top(n) for n in (0, 95, 96, 103, 104, 159, 160, 255)],
                         [7, 7, 8, 8, 9, 15, 15, 15])


if __name__ == '__main__': unittest.main()
