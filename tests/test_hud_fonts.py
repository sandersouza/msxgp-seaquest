import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from hud_fonts import SCORE, OXYGEN, score_rows, displayed_score, oxygen_rows


class HudFontTests(unittest.TestCase):
    def test_digits_keep_even_stems_and_round_digit_symmetry(self):
        self.assertEqual(len(SCORE),10)
        self.assertTrue(all(len(glyph)==8 and all(len(row)==8 for row in glyph) for glyph in SCORE))
        for digit in (0,1,8):
            self.assertTrue(all(row==row[::-1] for row in SCORE[digit]))
        for digit in (0,8):
            self.assertEqual(SCORE[digit][1],'##....##')
            self.assertEqual(SCORE[digit][-1],'.######.')

    def test_equal_cell_spacing_without_fractional_pixel_scaling(self):
        for digit in range(10):
            rows = score_rows((digit,digit))
            for row in rows:
                self.assertEqual([x+12 for x in row if x<12],[x for x in row if x>=12])

    def test_zero_retains_five_leading_blanks_and_source_bcd(self):
        ram = bytearray(251)
        self.assertEqual(displayed_score(ram),score_rows((None,None,None,None,None,0)))
        ram[0xb8:0xbb] = bytes((0x01,0x23,0x45))
        self.assertEqual(displayed_score(ram),score_rows((None,1,2,3,4,5)))
        ram[0xb8:0xbb] = bytes((0,0,0x0a))
        self.assertEqual(displayed_score(ram),[[] for _ in range(8)])

    def test_oxygen_has_closed_bottoms_and_fits_existing_six_tiles(self):
        self.assertEqual(OXYGEN[0][-1],'.####.')
        self.assertEqual(OXYGEN[3][-1],'.####.')
        self.assertEqual(OXYGEN[4][-1],'######')
        rows = oxygen_rows()
        self.assertEqual(len(rows),8)
        self.assertEqual(rows[-1],[])
        self.assertTrue(all(0<=x<48 for row in rows for x in row))
        self.assertEqual([x for x in rows[6] if x<8],[2,3,4,5])


if __name__=='__main__': unittest.main()
