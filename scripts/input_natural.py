#!/usr/bin/env python3
"""Cold-boot continuous controls replay and event-to-state/display latency."""
import hashlib
import json
import re
import argparse

from input_contract import OUT, ROOT, device_events, replay, run
from native_contract import reference
from collision_reference import contacts
from original_graphics import extract
from oxygen_reference import alarm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rescue',action='store_true',help='extend device-only replay through natural rescue/death/oxygen cycles')
    parser.add_argument('--progression',action='store_true',help='device-only alternating-player exhaustion, game over and restart')
    parser.add_argument('--audio',action='store_true',help='verify cold original HUD/PSG cartridge and ordered continuous audio')
    args = parser.parse_args()
    rom = ROOT/('outputs/render/presentation-controls.rom' if args.audio else 'outputs/render/controls.rom')
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',rom.with_suffix('.sym').read_text(),re.M)}
    if args.audio:
        seed_script = OUT/'seed.tcl'
        seed_script.write_text('set renderer none\nset throttle off\nset power true\nplug joyporta msxjoystick1\nplug joyportb msxjoystick2\nreverse start\nafter time 1 {reverse savereplay outputs/input/seed.omr; exit}\n')
        run(seed_script,rom,'seed',mapper='ASCII16')
    events = []
    # Real controls only, beginning after cold boot/refill. Two different
    # held-fire settings and facing reversal, then Select/Reset and fresh refill.
    schedule = [(5.75,(0,0,64,0,0)),(6.35,(0,0,0,0,0)),
                (6.5,(0,0,1,0,0)),(7.,(128,0,1,0,0)),(7.03,(0,0,1,0,0)),
                (7.2,(0,1,1,0,0)),(7.23,(0,0,1,0,0)),
                (7.6,(0,0,17,0,0)),(7.8,(0,0,1,8,0)),(8.4,(0,0,0,0,0)),
                (8.65,(64,0,0,0,0)),(8.72,(32,0,0,0,0)),(8.75,(0,0,0,0,0))]
    latency = []
    for n in range(16):
        time = 12+n*.2137
        left = bool(n&1)
        source = 'keyboard' if n<8 else 'joystick'
        direction = 4 if left else 8
        controls = (0,0,16 if left else 128,0,0) if source=='keyboard' else (0,0,0,direction,0)
        schedule += [(time,controls),(time+.04,(0,0,0,0,0))]
        latency.append(dict(time=time,source=source,direction=-1 if left else 1))
    for time,controls in sorted(schedule):
        events += device_events(time,controls)
    extended = args.rescue or args.progression
    replay(OUT/'seed.omr',events,112 if extended else 17,OUT/'natural.omr')
    script = OUT/'natural-start.tcl'
    tcl = (ROOT/'scripts/input_natural.tcl').read_text()
    if extended:
        tcl = tcl.replace('after time 16.5','after time 110').replace(' -viewonly','')
    if args.audio:
        tcl = tcl.replace('[machine_info time] >= 5.5','[machine_info time] >= 0')
        from audio_natural import setup
        tcl = setup(symbols)+tcl
    script.write_text(''.join(f'set {n} {symbols[n]}\n' for n in ('sample_input','paced_core_start','paced_core_done','paced_frame_start','paced_commit','paced_prepared'))+
                      f'set sample_input_return {symbols["core_F6A7"]+3}\n'+
                      ('set oxygen_natural 1\nsource scripts/progression_natural.tcl\n' if args.progression else
                       ('set oxygen_natural 1\nsource scripts/oxygen_natural.tcl\n' if args.rescue else ''))+
                      tcl)
    (OUT/'natural-complete.txt').unlink(missing_ok=True)
    run(script,rom,'natural',mapper='ASCII16' if args.audio else None)
    if not (OUT/'natural-complete.txt').exists():
        raise ValueError('natural replay incomplete')
    original = (ROOT/'outputs/native/original.rom').read_bytes()
    data = (OUT/'natural.bin').read_bytes()
    size = 2048+4+251
    if not data or len(data)%size:
        raise ValueError('truncated natural replay')
    states = []
    assets = extract(original)
    from graphics_reference import Reference
    ale = Reference()
    occupancy_fields = (*range(0x9e,0xa2),*range(0xa4,0xa8),*range(0xc6,0xcb),
                        0xd6,*range(0xd9,0xde),0xe0,0xe1,0xe7,0xe9,0xf6,0xbb,0x82)
    for n,offset in enumerate(range(0,len(data),size)):
        raster = bytearray(data[offset:offset+1024])
        before = bytearray(data[offset+1024:offset+2048])
        acquired = contacts(raster,original,assets)
        if acquired != before[0xb0:0xb7]+before[0xf8:0xf9]:
            raise ValueError(f'natural tick {n}: native acquisition differs from occupancy')
        if before[0xf9] != alarm(original,raster):
            raise ValueError(f'natural tick {n}: omitted HUD alarm differs from original')
        ale.image(**{f'{i:x}':raster[i] for i in occupancy_fields})
        source = bytes(ale.ale.getRAM())
        if acquired != source[0x30:0x37]+source[0x78:0x79]:
            raise ValueError(f'natural tick {n}: native acquisition differs from Atari TIA')
        ports,console,f1,f2 = data[offset+2048:offset+2052]
        before[0x280],before[0x282],before[0xc],before[0xd] = ports,console,f1,f2
        actual = data[offset+2052:offset+size]
        expected,_ = reference(original,list(before),0xf5b8,0,0x82)
        if actual != expected:
            first = next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
            raise ValueError(f'natural tick {n}, byte {first}: {actual[first]} != {expected[first]}')
        continuous = [i for i in range(0x80,251) if i not in (*range(0xb0,0xb7),0xf8,0xf9)]
        if states and any(before[i] != states[-1][i] for i in continuous):
            raise ValueError(f'natural state was reloaded between ticks {n-1}/{n}')
        states.append(actual)
    timing = [json.loads(line) for line in (OUT/'natural-timing.jsonl').read_text().splitlines()]
    frames = [t for t in timing if t['kind']=='state']
    commits = [t for t in timing if t['kind']=='commit']
    busy = [t['cycles'] for t in timing if t['kind']=='busy']
    startup_busy = busy.pop(0) if args.audio else None
    visible_frames = frames[1:] if args.audio else frames
    if max(busy)>=59736 or any(b['vdp_frame']-a['vdp_frame']!=1 for a,b in zip(visible_frames,visible_frames[1:])):
        raise ValueError('natural collision replay exceeded the frame budget or skipped a VDP frame')
    for event in latency:
        # Before press each pulse is neutral, away from boundaries/refill/death.
        previous = max((f for f in frames if f['time']<event['time']),key=lambda f:f['time'])
        updated = next(f for f in frames if f['time']>=event['time'] and (f['x']-previous['x'])*event['direction']>0)
        presented = next(c for c in commits if c['time']>=updated['time'] and c['x']==8+updated['x']*3//2)
        event['state_ms'] = round(1000*(updated['time']-event['time']),4)
        event['sat_commit_ms'] = round(1000*(presented['time']-event['time']),4)
        if not 0 <= event['state_ms'] < 20 or not 0 <= event['sat_commit_ms'] < 36:
            raise ValueError(f'input latency outside two-frame contract: {event}')
    births = [f for i,f in enumerate(frames) if i and not frames[i-1]['shot'] and f['shot']]
    report = dict(passed=True,continuous_ticks=len(states),ram_reloads_after_boot=0,
                  original_tia_acquisition_ticks=len(states),
                  max_busy_cycles=max(busy),skipped_vdp_frames=0,
                  rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),latency=latency,
                  max_state_ms=max(e['state_ms'] for e in latency),
                  max_sat_commit_ms=max(e['sat_commit_ms'] for e in latency),
                  shot_births=births,
                  method='cold boot; keyboard/joystick replay device events; original 6502 comparison every captured update',
                  display_measurement='SAT upload completed; visible scanout and host OS event latency are separate',
                  physical_hardware=False)
    if args.rescue:
        report['natural_events'] = dict(
            alarm_ticks=sum(s[0xf9]!=0 for s in states),
            pickups=sum(b[0xbe]>a[0xbe] for a,b in zip(states,states[1:])),
            partial_rescues=sum(b[0xbe]+1==a[0xbe] and a[0xe1]==13 and not a[0xe9] and b[0xbd]==(a[0xbd]+1)&255 for a,b in zip(states,states[1:])),
            full_rescues=sum(b[0xe8]==6 and a[0xe8]!=6 for a,b in zip(states,states[1:])),
            deaths=sum(not a[0xe9] and bool(b[0xe9]) for a,b in zip(states,states[1:])),
            oxygen_depletions=sum(a[0xe6]==1 and b[0xe6]==0 and b[0xe9]==23 and a[0xe1]==20 for a,b in zip(states,states[1:])),
            refills=sum(a[0xe8]&1 and not b[0xe8]&1 for a,b in zip(states,states[1:])))
        required = ('alarm_ticks','pickups','partial_rescues','deaths','oxygen_depletions','refills')
        if any(not report['natural_events'][event] for event in required):
            raise ValueError(f'incomplete natural rescue/depletion coverage: {report["natural_events"]}')
    if args.progression:
        # The controller begins after the common latency/control segment.
        start = next(i for i,f in enumerate(frames) if f['time']>=17)
        pairs = list(zip(states[start:],states[start+1:]))
        report['progression_events'] = dict(
            player_switches=sum(a[0xb7]!=b[0xb7] for a,b in pairs),
            death_player_switches=sum(a[0xb7]!=b[0xb7] and a[0xe9]==1 and not b[0xe9]
                                     and not a[0xa3] and not b[0xa3] for a,b in pairs),
            attract_player_switches=sum(a[0xb7]!=b[0xb7] and bool(a[0xa3]) and bool(b[0xa3]) for a,b in pairs),
            gameovers=sum(not a[0xa3] and b[0xa3] and not b[0xe9] for a,b in pairs),
            restarts=sum(a[0xa3] and not b[0xa3] and b[0xbb]==3 and b[0xc2]==4 for a,b in pairs),
            deaths=sum(not a[0xe9] and bool(b[0xe9]) for a,b in pairs),
            active_players=sorted({s[0xb7] for s in states[start:]}),
            difficulty_settings=sorted({f['switches']&192 for f in frames}))
        e = report['progression_events']
        if not (e['death_player_switches']>=2 and e['gameovers'] and e['restarts'] and e['active_players']==[0,1]
                and e['difficulty_settings']==[0,64,128,192]):
            raise ValueError(f'incomplete natural progression coverage: {e}')
    if args.audio:
        from audio_natural import verify
        report['audio'] = verify(symbols,rom,data)
        report['startup_prepare_cycles'] = startup_busy
        report['startup_policy'] = 'first cache preparation runs with display disabled; every subsequent visible frame is timed'
    (OUT/'natural-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('latency','shot_births')}))


if __name__=='__main__':
    main()
