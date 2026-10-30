import hashlib
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts/reference_inventory.py'
spec = importlib.util.spec_from_file_location('reference_inventory', MODULE)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class ReferenceInventoryTests(unittest.TestCase):
    def test_inclusive_xex_segment_and_run_address(self):
        data = bytes.fromhex('ffff00200220aabbccffffe002e1020020')
        result = inventory.inspect_xex(data)
        self.assertEqual(result['segments'][0], {'start': 8192, 'end': 8194, 'size': 3})
        self.assertEqual(result['run_address'], 8192)

    def test_truncated_xex_header_or_payload_fails(self):
        for data in (b'', b'\xff\xff\x00', bytes.fromhex('ffff00200220aa')):
            with self.subTest(data=data), self.assertRaises(ValueError):
                inventory.inspect_xex(data)

    def test_reversed_segment_fails(self):
        with self.assertRaises(ValueError):
            inventory.inspect_xex(bytes.fromhex('ffff02200020'))

    def test_non_xex_input_fails(self):
        with self.assertRaises(ValueError):
            inventory.inspect_xex(b'not an XEX')

    def test_partial_run_vector_is_not_invented(self):
        self.assertIsNone(inventory.inspect_xex(bytes.fromhex('ffffe002e00200'))['run_address'])

    def test_modified_reference_is_rejected(self):
        expected = {'size': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()}
        self.assertEqual(inventory.check_digest(b'abc', expected), [])
        self.assertTrue(inventory.check_digest(b'abd', expected))
        self.assertTrue(inventory.check_digest(b'ab', expected))


if __name__ == '__main__':
    unittest.main()
