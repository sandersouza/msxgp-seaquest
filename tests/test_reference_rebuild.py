import importlib.util
from pathlib import Path
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

spec = importlib.util.spec_from_file_location('reference_rebuild', Path(__file__).resolve().parents[1] / 'scripts/reference_rebuild.py')
rebuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuild)


class RebuildTests(unittest.TestCase):
    def test_listing_map_retains_inclusive_data_extent(self):
        listing = ('    1 f000       78       START SEI\n'
                   '    2 f001       aa bb cc dd*TABLE .byte.b $AA,$BB,$CC,$DD,$EE\n'
                   '    3 f006       60       RTS\n')
        self.assertEqual(rebuild.listing_map(listing, 0xf007), [
            {'start': 0xf000, 'end': 0xf000, 'kind': 'code'},
            {'start': 0xf001, 'end': 0xf005, 'kind': 'data'},
            {'start': 0xf006, 'end': 0xf006, 'kind': 'code'}])

    def test_listing_map_does_not_invent_missing_prefix(self):
        with self.assertRaises(ValueError):
            rebuild.listing_map('1 f001 60 RTS\n', 0xf002)

    def test_assembly_identity_is_strict(self):
        self.assertTrue(rebuild.binary_identity(b'abc', b'abc')['byte_identical'])
        result = rebuild.binary_identity(b'abc', b'abd')
        self.assertFalse(result['byte_identical'])
        self.assertEqual(result['first_difference'], 2)
        self.assertEqual(rebuild.binary_identity(b'abc', b'ab')['first_difference'], 2)


if __name__ == '__main__':
    unittest.main()
