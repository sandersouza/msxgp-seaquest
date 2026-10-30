import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from original_graphics import bitmap, ball, early_patrol, scale_rows, sprite_bytes, sprite_bank, extract
from graphics_palette import tms_color


class OriginalGraphicsTests(unittest.TestCase):
    def test_patrol_carry_includes_low_reserve_and_death_overrides(self):
        clear_reserves = {0:{0,1},1:set(range(7)),9:set(range(7)),10:set(),14:set(),15:set(),23:set()}
        state = bytearray(256)
        for death,expected in clear_reserves.items():
            for reserve in range(7):
                state[0xe9],state[0xbb] = death,reserve
                self.assertEqual(early_patrol(state),reserve in expected)

    def test_source_order_reflection_and_double_width(self):
        source = bytes([0b10000001,0b01000000])
        self.assertEqual(bitmap(source,0xf000,2),[[1],[0,7]])
        self.assertEqual(bitmap(source,0xf000,2,True,2),[[12,13],[0,1,14,15]])

    def test_extract_covers_all_reachable_shark_offsets(self):
        assets = extract(bytes(4096))
        enemies = [name for name in assets if name.startswith('enemy-')]
        self.assertEqual(len(enemies),54)
        self.assertIn('enemy-10-7',assets)
        self.assertNotIn('enemy-3-0',assets)

    def test_surface_view_cannot_mutate_canonical_mask(self):
        assets = extract(bytes(4096))
        assets['surface-player-0-0-13']['rows'][0].append(99)
        self.assertEqual(assets['player-0-0']['rows'][0],[])

    def test_ball_sign_extension_width_and_disabled_rows(self):
        source = bytearray(4096)
        source[0xf7e],source[0xf92] = 0,32
        source[0xd0e] = 0xf0  # -1 movement means +1 position, from anchor +2.
        source[0xd2e] = 0x12  # enabled, width 2.
        rows,_ = ball(source,0)
        self.assertEqual(rows[0],[3,4])
        self.assertTrue(all(not row for row in rows[1:]))

    def test_floor_mapping_keeps_parity_and_clips_before_scaling(self):
        shape = [[-1,0,1,7]]
        self.assertEqual(scale_rows(shape,0),[[8,9,10,18,19]])
        self.assertEqual(scale_rows([[0,1]],1),[[9,10,11]])
        self.assertEqual(scale_rows([[0,1]],159),[[246,247]])
        self.assertEqual(shape,[[-1,0,1,7]])

    def test_sprite_layout_and_rejection_of_overflow(self):
        data = sprite_bytes([[0,7,8,15],[1]])
        self.assertEqual(len(data),32)
        self.assertEqual([data[0],data[1],data[16]],[129,64,129])
        with self.assertRaises(ValueError): sprite_bytes([[16]])
        with self.assertRaises(ValueError): sprite_bytes([[]]*17)

    def test_catalog_distinguishes_resident_and_edge_images(self):
        assets = {'torpedo':dict(rows=[list(range(8))])}
        bank,lookup,resident = sprite_bank(assets)
        self.assertLessEqual((resident+16)*32,2048)
        for x in range(160):
            index = lookup[f'torpedo@{x}']['patterns'][0]
            self.assertEqual(bank[index*32:index*32+32],
                             sprite_bytes(scale_rows(assets['torpedo']['rows'],x),8+x*3//2))

    def test_opaque_palette_never_uses_transparency(self):
        self.assertEqual(tms_color(0),1)
        self.assertEqual(tms_color(0x18),10)
        self.assertEqual(tms_color(0x90),4)
        self.assertTrue(all(1<=tms_color(n)<=15 for n in range(256)))
        self.assertTrue(all(tms_color(n)==tms_color(n|1) for n in range(0,256,2)))


if __name__=='__main__': unittest.main()
