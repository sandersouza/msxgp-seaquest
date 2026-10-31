import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from full_game_reference import coverage, RECORD_BYTES


def records(states,difficulty=0):
    result = bytearray()
    for state in states:
        row = bytearray(RECORD_BYTES)
        row[2049] = 63|difficulty
        row[2052:] = state
        result.extend(row)
    return bytes(result)


class FullGameAcceptanceTests(unittest.TestCase):
    def setUp(self):
        active = bytearray(251)
        active[0xbb],active[0xc2] = 3,0
        dying = bytearray(active); dying[0xe9] = 23
        over = bytearray(active); over[0xa3] = 1; over[0xbb],over[0xc2] = 0,0
        self.states = [active,dying,over,active]
        self.timing = [dict(kind='game-start',tick=0)]

    def test_boot_or_death_without_gameover_and_restart_is_rejected(self):
        for end in (1,2,3):
            with self.assertRaisesRegex(ValueError,'incomplete natural full game'):
                coverage(records(self.states[:end]),self.timing,0,0)

    def test_requires_restart_after_gameover(self):
        result = coverage(records(self.states),self.timing,0,0)
        self.assertEqual((result['first_gameover_tick'],result['first_restart_tick']),(2,3))

    def test_missing_or_truncated_or_unconfigured_trace_is_rejected(self):
        for data,timing in ((b'',self.timing),(b'bad',self.timing),(records(self.states),[]),
                            (records(self.states),self.timing*2)):
            with self.assertRaises(ValueError):
                coverage(data,timing,0,0)

    def test_other_mode_or_difficulty_cannot_supply_coverage(self):
        for mode,difficulty in ((1,0),(0,64)):
            with self.assertRaisesRegex(ValueError,'configured mode/difficulty'):
                coverage(records(self.states),self.timing,mode,difficulty)

    def test_two_player_selection_requires_both_players_and_death_swap(self):
        for s in self.states:
            s[0x80] = 1
            if not s[0xa3]: s[0xc2] = 4
        with self.assertRaisesRegex(ValueError,'active-player exhaustion'):
            coverage(records(self.states),self.timing,1,0)

    def test_rescue_route_requires_pickups_rescue_alarm_and_depletion(self):
        with self.assertRaisesRegex(ValueError,'incomplete natural rescue route'):
            coverage(records(self.states),self.timing,0,0,'rescue')


if __name__=='__main__': unittest.main()
