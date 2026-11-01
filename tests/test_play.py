from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import play


class PlayTests(unittest.TestCase):
    def test_rom_launch_forces_normal_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory)/'game.rom'
            rom.write_bytes(b'AB\x10\x40' + bytes(32764))
            with patch.dict(play.BINARIES, rom=rom), patch.object(play.subprocess, 'run') as run:
                play.run_game('rom', 'C-BIOS_MSX1_EU', None)
            self.assertEqual(run.call_args.args[0], ['openmsx', '-machine',
                             'C-BIOS_MSX1_EU', '-cart', str(rom), '-romtype', 'Normal'])

    def test_invalid_rom_cannot_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory)/'game.rom'
            rom.write_bytes(b'AB' + bytes(131070))
            with patch.dict(play.BINARIES, rom=rom), patch.object(play.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, '32768'):
                    play.run_game('rom', 'C-BIOS_MSX1', None)
                run.assert_not_called()

    def test_dos_failure_preserves_original_and_cleans_private_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            com = root/'SEAQUEST.COM'
            com.write_bytes(b'current executable')
            disk = root/'system disk.dsk'
            original = b'owner disk'
            disk.write_bytes(original)
            copies = []

            def launch(command, **kwargs):
                boot = Path(command[command.index('-diska')+1])
                copies.append(boot)
                self.assertNotEqual(boot, disk)
                self.assertEqual(boot.read_bytes(), original)
                self.assertEqual(Path(kwargs['env']['SEAQUEST_RUN_COM']).read_bytes(), com.read_bytes())
                self.assertEqual(Path(kwargs['env']['SEAQUEST_RUN_AUTOEXEC']).read_bytes(), b'SEAQUEST\r\n')
                boot.write_bytes(b'emulator writes')
                raise subprocess.CalledProcessError(1, command)

            with patch.object(play, 'ROOT', root), patch.dict(play.BINARIES, com=com), \
                 patch.object(play.subprocess, 'run', side_effect=launch):
                with self.assertRaises(subprocess.CalledProcessError):
                    play.run_game('com', 'disk-capable-MSX1', str(disk))
            self.assertEqual(disk.read_bytes(), original)
            self.assertFalse(copies[0].exists())

    def test_com_requires_system_disk_and_disk_bios(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory)/'SEAQUEST.COM'
            binary.write_bytes(b'program')
            with patch.dict(play.BINARIES, com=binary), patch.object(play.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'DOS_DISK'):
                    play.run_game('com', 'disk-capable-MSX1', None)
                with self.assertRaisesRegex(ValueError, 'C-BIOS'):
                    play.run_game('com', 'C-BIOS_MSX1', str(binary))
                run.assert_not_called()
