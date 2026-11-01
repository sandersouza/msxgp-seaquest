import struct
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native_video import disk_com_bytes,launch_arguments


class NativeVideoTests(unittest.TestCase):
    def floppy(self):
        image=bytearray(720*1024)
        struct.pack_into('<H',image,11,512)
        image[13]=2
        struct.pack_into('<H',image,14,1)
        image[16]=2
        struct.pack_into('<H',image,17,112)
        struct.pack_into('<H',image,22,3)
        root=7*512
        image[root:root+11]=b'SEAQUESTCOM'
        image[root+11]=32
        struct.pack_into('<H',image,root+26,2)
        struct.pack_into('<I',image,root+28,1500)
        # Two clusters, deliberately noncontiguous: 2 -> 5 -> EOF.
        image[515:517]=b'\x05\x00'
        image[519:521]=b'\xf0\xff'
        data=bytes(i%251 for i in range(1500))
        image[14*512:16*512]=data[:1024]
        image[20*512:20*512+476]=data[1024:]
        return image,data

    def test_reads_actual_noncontiguous_file_and_ignores_padding(self):
        image,data=self.floppy()
        self.assertEqual(disk_com_bytes(image),data)

    def test_rejects_cycle_before_end_of_file(self):
        image,_=self.floppy()
        image[515]=2
        with self.assertRaises(ValueError):
            disk_com_bytes(image)

    def test_requires_the_executable_filename(self):
        image,_=self.floppy()
        image[7*512]=0
        with self.assertRaises(ValueError):
            disk_com_bytes(image)

    def test_dos_launch_rejects_a_different_executable_identity(self):
        image,data=self.floppy()
        with tempfile.TemporaryDirectory() as directory:
            disk=Path(directory)/'private.dsk'
            binary=Path(directory)/'SEAQUEST.COM'
            disk.write_bytes(image)
            binary.write_bytes(data)
            self.assertEqual(launch_arguments('dos',binary,disk),['-diska',str(disk)])
            binary.write_bytes(bytes([data[0]^1])+data[1:])
            with self.assertRaises(ValueError):
                launch_arguments('dos',binary,disk)

    def test_plain32_cannot_relabel_a_banked_image(self):
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'candidate.rom'
            binary.write_bytes(bytes(131072))
            with self.assertRaises(ValueError):
                launch_arguments('plain32',binary,None)
            binary.write_bytes(bytes(32768))
            self.assertEqual(launch_arguments('plain32',binary,None)[-1],'Normal')
