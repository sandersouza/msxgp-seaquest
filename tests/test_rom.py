import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from rom import validate_rom


class RomTests(unittest.TestCase):
    def test_header_and_entry_must_be_valid(self):
        valid = b'AB\x10\x40' + bytes(32764)
        self.assertEqual(validate_rom(valid), [])
        self.assertTrue(validate_rom(b'XX' + valid[2:]))
        self.assertTrue(validate_rom(b'AB\x00\x30' + valid[4:]))
        self.assertTrue(validate_rom(valid[:-1]))


if __name__ == '__main__':
    unittest.main()
