from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from source_identity import fingerprint,verify


class SourceIdentityTests(unittest.TestCase):
    def test_committed_or_uncommitted_source_edits_invalidate_old_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'src').mkdir()
            source=root/'src/game.asm'
            source.write_text('RET\n')
            identity=fingerprint(root)
            verify(root,identity)
            source.write_text('JP game\n')
            with self.assertRaises(ValueError):
                verify(root,identity)

    def test_new_generator_is_part_of_source_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'scripts').mkdir()
            identity=fingerprint(root)
            (root/'scripts/new.py').write_text('print(1)\n')
            with self.assertRaises(ValueError):
                verify(root,identity)
