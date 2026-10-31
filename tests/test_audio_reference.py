import sys
from pathlib import Path
import unittest
import importlib.util

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audio_reference import AudioModel,tone_period,noise_period,trace


class AudioTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('py65'),'optional original-CPU backend is not installed')
    def test_trace_keeps_transient_overwrites_and_source_frame_boundary(self):
        rom = bytearray(4096)
        program = bytes.fromhex('a9048515 a9038519 e681 a90c8515 4c0ef0')
        rom[0x5b8:0x5b8+len(program)] = program
        ram = bytearray(1024); ram[0x81] = 255
        state,events,_ = trace(rom,ram)
        self.assertEqual([(e['address'],e['value'],e['frame']) for e in events],
                         [(0x15,4,255),(0x19,3,255),(0x15,12,0)])
        self.assertEqual(state[0x15],12)
        self.assertEqual([e['instruction_start_cycles'] for e in events],[2,7,17])

    def test_pure_pitch_matches_chip_clock_ratio_within_half_a_period(self):
        for control,divider in ((4,114),(12,342)):
            for frequency in range(32):
                self.assertLessEqual(abs(tone_period(control,frequency)-divider*(frequency+1)/16),.5)

    def test_noise_clock_sharing_keeps_both_volumes_and_source0_priority(self):
        model = AudioModel([8,8,0,7,0,9],ports=192)
        self.assertEqual(model.psg[6],noise_period(7))
        model.write(0x19,4)
        self.assertEqual(model.psg[6],noise_period(0))
        self.assertEqual(model.psg[8:10],[4,9])
        self.assertEqual(model.psg[7]&192,192)
        model.write(0x19,0)
        self.assertEqual(model.psg[6],noise_period(7))

    def test_dc_does_not_change_inaudible_tone_period_or_force_an_envelope(self):
        model = AudioModel([12,0,31,0,6,0])
        previous = model.psg[:2]
        model.write(0x15,0)
        model.write(0x17,0)
        self.assertEqual(model.psg[:2],previous)
        self.assertEqual(model.psg[8],6)
        model.write(0x15,4)
        self.assertEqual(model.psg[:2],[7,0])
        model.write(0x19,31)
        self.assertEqual(model.psg[8],15)


if __name__=='__main__': unittest.main()
