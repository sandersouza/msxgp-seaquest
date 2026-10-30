import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from progression_reference import PhaseMemory


class DisplayDependencyTests(unittest.TestCase):
    def test_omitted_input_read_is_detected(self):
        memory = PhaseMemory(bytes(4096),bytes(1024))
        memory[0xbc] = 7
        memory.phase = 'core'
        self.assertEqual(memory[0xbc],7)
        self.assertEqual(memory.dependencies,{0xbc})

    def test_core_overwrite_removes_display_dependency(self):
        memory = PhaseMemory(bytes(4096),bytes(1024))
        memory[0x92] = 80
        memory.phase = 'core'
        memory[0x92] = 3
        self.assertEqual(memory[0x92],3)
        self.assertEqual(memory.dependencies,set())

    def test_rom_fetch_and_preexisting_state_are_not_display_inputs(self):
        memory = PhaseMemory(bytes([169])*4096,bytes(1024))
        memory.phase = 'core'
        self.assertEqual(memory[0xf000],169)
        self.assertEqual(memory[0xbb],0)
        self.assertEqual(memory.dependencies,set())
