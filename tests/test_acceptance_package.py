import copy
import hashlib
import gzip
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from acceptance_package import validate
from acceptance_replay import relocate_replay


class PackageIdentityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.rom = Path(self.directory.name)/'candidate.rom'
        self.rom.write_bytes(bytes(131072))
        self.rom.with_suffix('.sym').write_bytes(b'symbols')
        base = dict(verdict='pass',rom_sha256=hashlib.sha256(self.rom.read_bytes()).hexdigest(),
                    symbols_sha256=hashlib.sha256(b'symbols').hexdigest(),mapper='ASCII16',
                    ram_kib=64,vram_kib=16,cpu_hz=3579545,skipped_vdp_frames=0,
                    visible_commits=0,ram_reloads_after_chain_start=0)
        routes = []
        for machine in ('C-BIOS_MSX1','C-BIOS_MSX1_EU'):
            for mode,difficulty,controller in [(m,d,'exhaust') for m in (0,1) for d in (0,64,128,192)]+[(0,0,'rescue')]:
                routes.append(dict(base,machine=machine,full_game=dict(mode=mode,difficulty=difficulty,controller=controller)))
        self.summary = dict(verdict='pass',rom_sha256=base['rom_sha256'],symbols_sha256=base['symbols_sha256'],routes=routes)

    def test_complete_matrix_and_exact_candidate(self):
        validate(self.summary,self.rom)

    def test_diagnostic_or_modified_cartridge_is_rejected(self):
        for size in (32768,131072):
            self.rom.write_bytes(b'x'*size)
            with self.assertRaisesRegex(ValueError,'cartridge differs'):
                validate(self.summary,self.rom)

    def test_stale_symbols_are_rejected(self):
        self.rom.with_suffix('.sym').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'symbols differ'):
            validate(self.summary,self.rom)

    def test_duplicate_missing_or_mixed_route_is_rejected(self):
        for change in ('duplicate','missing','mixed','frame-skip'):
            summary = copy.deepcopy(self.summary)
            if change=='duplicate': summary['routes'][-1] = summary['routes'][0]
            if change=='missing': summary['routes'].pop()
            if change=='mixed': summary['routes'][0]['rom_sha256'] = 'wrong'
            if change=='frame-skip': summary['routes'][0]['skipped_vdp_frames'] = 1
            with self.assertRaises(ValueError): validate(summary,self.rom)

    def test_packaged_replay_relocates_only_candidate_and_keeps_events(self):
        sha1 = hashlib.sha1(self.rom.read_bytes()).hexdigest()
        xml = f'<root><rom><filename>old.rom</filename><resolvedFilename>/old.rom</resolvedFilename><resolvedSha1>{sha1}</resolvedSha1></rom><rom><filename>bios.rom</filename><resolvedSha1>other</resolvedSha1></rom><events>device inputs</events></root>'
        source = Path(self.directory.name)/'source.omr'
        target = Path(self.directory.name)/'relocated.omr'
        source.write_bytes(gzip.compress(xml.encode()))
        relocate_replay(source,target,self.rom,relative=True)
        root = ET.fromstring(gzip.decompress(target.read_bytes()))
        self.assertEqual([n.text for n in root.iter('filename')],['seaquest.rom','bios.rom'])
        self.assertEqual(root.findtext('rom/resolvedSha1'),sha1)
        self.assertEqual(root.findtext('events'),'device inputs')

    def test_replay_for_another_cartridge_cannot_be_relocated(self):
        source = Path(self.directory.name)/'other.omr'
        source.write_bytes(gzip.compress(b'<root><rom><resolvedSha1>other</resolvedSha1></rom></root>'))
        with self.assertRaisesRegex(ValueError,'no matching candidate'):
            relocate_replay(source,Path(self.directory.name)/'new.omr',self.rom)


if __name__=='__main__': unittest.main()
