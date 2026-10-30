#!/usr/bin/env python3
"""Cold-boot continuous controls replay and event-to-state/display latency."""
import hashlib
import json
import re

from input_contract import OUT, ROOT, device_events, replay, run
from native_contract import reference


def main():
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',(ROOT/'outputs/render/controls.sym').read_text(),re.M)}
    rom = ROOT/'outputs/render/controls.rom'
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
    replay(OUT/'seed.omr',events,17,OUT/'natural.omr')
    script = OUT/'natural-start.tcl'
    script.write_text(''.join(f'set {n} {symbols[n]}\n' for n in ('sample_input','paced_core_start','paced_core_done','paced_frame_start','paced_commit'))+
                      f'set sample_input_return {symbols["core_F6A7"]+3}\n'+
                      'if {[catch {source scripts/input_natural.tcl} detail]} {puts stderr $detail; exit 1}\n')
    (OUT/'natural-complete.txt').unlink(missing_ok=True)
    run(script,rom,'natural')
    if not (OUT/'natural-complete.txt').exists():
        raise ValueError('natural replay incomplete')
    original = (ROOT/'outputs/native/original.rom').read_bytes()
    data = (OUT/'natural.bin').read_bytes()
    size = 1024+4+251
    if not data or len(data)%size:
        raise ValueError('truncated natural replay')
    states = []
    for n,offset in enumerate(range(0,len(data),size)):
        before = bytearray(data[offset:offset+1024])
        ports,console,f1,f2 = data[offset+1024:offset+1028]
        before[0x280],before[0x282],before[0xc],before[0xd] = ports,console,f1,f2
        actual = data[offset+1028:offset+size]
        expected,_ = reference(original,list(before),0xf5b8,0,0x82)
        if actual != expected:
            first = next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
            raise ValueError(f'natural tick {n}, byte {first}: {actual[first]} != {expected[first]}')
        continuous = [i for i in range(0x80,251) if i not in (*range(0xb0,0xb7),0xf8)]
        if states and any(before[i] != states[-1][i] for i in continuous):
            raise ValueError(f'natural state was reloaded between ticks {n-1}/{n}')
        states.append(actual)
    timing = [json.loads(line) for line in (OUT/'natural-timing.jsonl').read_text().splitlines()]
    frames = [t for t in timing if t['kind']=='state']
    commits = [t for t in timing if t['kind']=='commit']
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
                  rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),latency=latency,
                  max_state_ms=max(e['state_ms'] for e in latency),
                  max_sat_commit_ms=max(e['sat_commit_ms'] for e in latency),
                  shot_births=births,
                  method='cold boot; keyboard/joystick replay device events; original 6502 comparison every captured update',
                  display_measurement='SAT upload completed; visible scanout and host OS event latency are separate',
                  physical_hardware=False)
    (OUT/'natural-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('latency','shot_births')}))


if __name__=='__main__':
    main()
