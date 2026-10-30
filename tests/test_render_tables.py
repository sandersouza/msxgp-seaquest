import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from render_tables import shifted_row, sprite_peak, repeat_masks
from render_bench import visible_signature


class RenderTableTests(unittest.TestCase):
    def test_edge_masks_admit_exactly_visible_unsigned_copies(self):
        masks = repeat_masks()
        for x in range(256):
            allowed = masks[8 if x<128 else (x-128)//16]
            for source_mask in range(8):
                admitted = source_mask & allowed
                for copy in range(3):
                    self.assertEqual(bool(admitted & (4>>copy)),
                                     bool(source_mask & (4>>copy)) and ((x+16*copy)&255)<160)

    def test_scale_keeps_twelve_pixels_and_handles_tile_edges(self):
        for parity in (0, 1):
            for phase in range(8):
                row = shifted_row(255, phase, parity)
                bits = ''.join(f'{b:08b}' for b in row)
                self.assertEqual(bits, '0'*phase + '1'*12 + '0'*(12-phase))
        self.assertEqual(sum(x.bit_count() for x in shifted_row(0x80, 0, 0)), 1)
        self.assertEqual(sum(x.bit_count() for x in shifted_row(0x80, 0, 1)), 2)

    def test_bottom_aligned_patrol_fits_hardware_budget(self):
        divers = [49 + 24*n for n in range(4)]
        for player in range(30, 126):
            self.assertLessEqual(sprite_peak([player, player, player+5] + divers + [22]), 4)
        self.assertEqual(sprite_peak([42,42,42] + divers + [39]), 5)
        self.assertGreater(sprite_peak([49]*3 + [49]*3 + [49]),4)

    def test_original_geometry_respects_scanline_slots(self):
        for player_y in range(13,109):
            ys = [player_y+17]*2 + [48+24*n for n in range(4)] + [22]
            if player_y>=17: ys.append(player_y+24)
            self.assertLessEqual(sprite_peak(ys),4)

    def test_visible_signature_ignores_only_unreferenced_patterns(self):
        before = bytearray(16384)
        after = bytearray(before)
        after[96*8] = 255
        self.assertEqual(visible_signature(before),visible_signature(after))
        after[0x1800] = 96
        self.assertNotEqual(visible_signature(before),visible_signature(after))

    def test_visible_signature_tracks_sprite_patterns_beyond_first_eight(self):
        before = bytearray(16384)
        before[0x1b02] = 47*4
        after = bytearray(before)
        after[0x3800+55*32] = 128
        self.assertEqual(visible_signature(before),visible_signature(after))
        after[0x3800+47*32] = 128
        self.assertNotEqual(visible_signature(before),visible_signature(after))


if __name__ == '__main__': unittest.main()
