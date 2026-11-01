"""Boot-critical linker contracts, independent of private original-game inputs."""
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_disk import verify_layout, verify_writer_map, verify_no_mapper


class DiskLayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout=dict(native_static_start=0x100,native_static_end=0xbf59,
                         native_cold_start=0xf000,native_cold_end=0xf2dc,
                         native_high_start=0xf400,native_high_end=0xfff4)

    def test_original_64k_layout_fits(self):
        verify_layout(self.layout)

    def test_static_data_cannot_enter_workspace(self):
        self.layout['native_static_end']=0xc001
        with self.assertRaises(ValueError):
            verify_layout(self.layout)

    def test_cold_code_cannot_enter_stack(self):
        self.layout['native_cold_end']=0xf301
        with self.assertRaises(ValueError):
            verify_layout(self.layout)

    def test_high_data_cannot_reach_secondary_slot_register(self):
        self.layout['native_high_end']=0x10000
        with self.assertRaises(ValueError):
            verify_layout(self.layout)

    def test_every_numeric_writer_must_match_linker(self):
        verify_writer_map({'colour_writer_0':0x3be0,'unrelated':1},
                          {'colour_writer_0':0x3be0,'unrelated':2})
        with self.assertRaises(ValueError):
            verify_writer_map({'colour_writer_0':0x3be0},{'colour_writer_0':0x4000})

    def test_missing_or_empty_writer_map_is_rejected(self):
        for actual,expected in (({},{}),({'colour_writer_0':1},{})):
            with self.assertRaises(ValueError):
                verify_writer_map(actual,expected)

    def test_mapper_scan_follows_generated_nested_includes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/'root.asm').write_text('    INCLUDE "generated.inc"\n')
            (folder/'generated.inc').write_text('    LD ($7000),A\n')
            with self.assertRaises(ValueError):
                verify_no_mapper(folder/'root.asm')
            (folder/'generated.inc').write_text('    LD ($C6D0),A\n')
            verify_no_mapper(folder/'root.asm')


if __name__=='__main__':
    unittest.main()
