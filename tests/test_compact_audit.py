import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_audit import occupied_banks, role_factorization, storage_metrics


class CompactAuditTests(unittest.TestCase):
    def test_compression_is_lossless_and_reports_storage_only(self):
        data = bytes(range(256))*128
        result = storage_metrics(data)
        self.assertEqual(result['raw_bytes'], 32768)
        self.assertFalse(result['runtime_fit_proven'])
        self.assertLess(result['zlib9_bytes'], 32768)
        self.assertLess(result['lzma6_xz_bytes'], 32768)

    def test_occupied_extents_count_declared_payload_not_ff_trimming(self):
        banks = occupied_banks(
            {'fixed_bank_end': 0x7ef5, 'palette_base_memo': 0xbdc8},
            {'bank_ends': {'3': 12816, '5': 13053, '6': 16375, '7': 14769},
             'colour_program_bytes': 10545},
            29184)
        self.assertEqual(banks[0], 16117)
        self.assertEqual(banks[1], 15844)
        self.assertEqual(banks[2], 16384)
        self.assertEqual(banks[3], 12816)
        self.assertEqual(banks[4], 10545)

    def test_rejects_unknown_layout_instead_of_extrapolating(self):
        with self.assertRaises(ValueError):
            occupied_banks({'fixed_bank_end': 0x8001, 'palette_base_memo': 0xbdc8},
                           {'bank_ends': {}, 'colour_program_bytes': 0}, 29184)

    def test_roles_reconstruct_variable_and_zero_rgb_nibbles(self):
        records = [bytes([0x21, 0x20, 7, 2, 1]), bytes([0x43, 0x40, 9, 4, 3])]
        result = role_factorization(records, 2, 1, 2)
        self.assertEqual(result['combined_bytes'], 6)
        self.assertFalse(result['generated_decoder_and_runtime_validated'])

    def test_rejects_a_colour_absent_from_every_role(self):
        with self.assertRaises(ValueError):
            role_factorization([bytes([0x25, 7, 2, 1])], 1, 1, 2)


if __name__ == '__main__':
    unittest.main()
