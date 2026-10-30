import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collision_reference import contacts


class CollisionGeometryTests(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(4096)
        self.data[0xeeb:0xef4] = bytes([7]*9)
        self.data[0xef4:0xefc] = bytes([0,0,0,1,0,2,1,3])
        self.ram = bytearray(256)
        self.ram[0xc6],self.ram[0xe1] = 21,45
        self.ram[0x9e:0xa2] = bytes([21]*4)
        self.ram[0xc7:0xcb] = bytes([21]*4)
        self.ram[0xa4:0xa8] = bytes([7]*4)
        self.assets = {'player-0-0':{'rows':[list(range(16)) for _ in range(12)]},
                       'patrol-0':{'rows':[[]]*8},
                       'enemy-0-0':{'rows':[list(range(8)) for _ in range(15)]},
                       'ball-0':{'rows':[list(range(8)) for _ in range(15)]}}

    def sample(self):
        return contacts(self.ram,self.data,self.assets)

    def test_shared_latches_overwrite_in_descending_lane_order(self):
        # Player rows78..89 meet lane3's end and lane2's first raster row.
        result = self.sample()
        self.assertEqual(result[:4],bytes(range(4)))
        self.assertEqual(result[5:7],bytes([2,2]))
        self.assertEqual(result[7],7)

    def test_hmove_video_bar_does_not_remove_collision_pixels(self):
        self.ram[0x9e:0xa2] = bytes([159]*4)
        self.ram[0xc7:0xcb] = bytes(4)
        self.ram[0xa4:0xa8] = bytes([4]*4)
        self.assertEqual(self.sample()[:4],bytes(range(4)))

    def test_zero_repeat_mask_leaves_tia_base_copy_at_zero(self):
        self.ram[0xa4:0xa8] = bytes(4)
        self.ram[0xc7:0xcb] = bytes(4)
        self.ram[0xe1],self.ram[0xe7] = 25,159
        result = self.sample()
        self.assertEqual(result[:4],bytes(range(4)))
        self.assertEqual(result[4],3)
        self.assertEqual(result[5:7],bytes([255,255]))

    def test_display_palette_and_scale_are_not_collision_inputs(self):
        expected = self.sample()
        self.ram[0x85],self.ram[0x86],self.ram[0xb7] = 255,0,1
        self.assertEqual(self.sample(),expected)


if __name__=='__main__': unittest.main()
