import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from video_reference import raster_lines


class VideoSerializationTests(unittest.TestCase):
    def test_reads_full_raster_instead_of_cropped_screen_or_current_scanline(self):
        state = b'prefix\x03\x00\x00\x00TIA'+struct.pack('<8i',0,36,246,59736,228,262,3,0)
        self.assertEqual(raster_lines(state),262)

    def test_rejects_missing_or_ambiguous_layout(self):
        for state in (b'TIA',b'\x03\x00\x00\x00TIA'*2):
            with self.assertRaises(ValueError):
                raster_lines(state)

    def test_rejects_truncated_tia_record(self):
        with self.assertRaises(struct.error):
            raster_lines(b'\x03\x00\x00\x00TIA'+b'\0'*20)
