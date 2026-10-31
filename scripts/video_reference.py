"""Measure the verified NTSC4K's raster length and update counter in ALE/Stella."""
import json
import struct
from original_graphics import ROOT, SHA256, read_original


def raster_lines(serialized):
    # ALE0.12.1 TIA::save writes eight little-endian ints after its device tag.
    # The sixth is myScanlineCountForLastFrame (not the cropped screen height).
    tag = b'\x03\x00\x00\x00TIA'
    if serialized.count(tag) != 1:
        raise ValueError('unsupported ALE TIA serialization')
    return struct.unpack_from('<8i', serialized, serialized.index(tag)+len(tag))[5]


def main():
    import ale_py
    read_original()
    if ale_py.__version__ != '0.12.1':
        raise ValueError('serialization probe requires ALE0.12.1')
    ale = ale_py.ALEInterface()
    ale.setInt('frame_skip', 1)
    ale.setInt('random_seed', 0)
    ale.setFloat('repeat_action_probability', 0.0)
    ale.loadROM(str(ROOT/'references/roms/seaquest-atari2600.a26'))
    observations = []
    for action, count in ((ale_py.Action.NOOP, 600), (ale_py.Action.FIRE, 1800),
                          (ale_py.Action.RIGHTFIRE, 1800), (ale_py.Action.LEFTFIRE, 1800)):
        lines, deltas = set(), set()
        for _ in range(count):
            before = int(ale.getRAM()[1])
            ale.act(action)
            lines.add(raster_lines(ale.cloneSystemState().serialize()))
            deltas.add((int(ale.getRAM()[1])-before)&255)
        if lines != {262} or deltas != {1}:
            raise ValueError(f'changed reference cadence: {lines}, {deltas}')
        observations.append(dict(action=str(action), frames=count,
                                 raster_lines=sorted(lines), update_counter_delta=sorted(deltas)))
    report = dict(original_sha256=SHA256, ale=ale_py.__version__, frame_skip=1,
                  random_seed=0, repeat_action_probability=0, observations=observations,
                  cpu_cycles_per_line=76, cpu_cycles_per_update=262*76,
                  source_updates_per_frame=1,
                  serialization_source='https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/v0.12.1/src/ale/emucore/TIA.cxx#L293-L307',
                  limitation='observed idle/fire/directional scenarios; measured NTSC4K only')
    out = ROOT/'outputs/video'
    out.mkdir(exist_ok=True)
    (out/'reference.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
