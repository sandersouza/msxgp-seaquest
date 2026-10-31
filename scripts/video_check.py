"""Differential source, presentation, pacing and RAM checks on private PAL/NTSC processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from original_graphics import ROOT, SHA256, read_original, extract
from oxygen_reference import acquire
from presentation_check import PresentationOracle
from render_bench import check_original_sprites
from audio_natural import setup as audio_setup
from audio_reference import AudioModel, trace
from audio_contract import check_events
from input_contract import replay, device_events

OUT = ROOT/'outputs/video'


def symbols(path):
    return {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',path.read_text(),re.M)}


def build():
    OUT.mkdir(exist_ok=True)
    with (OUT/'build.log').open('w') as log:
        subprocess.run([sys.executable,'-B',str(ROOT/'scripts/render_bench.py'),
                        '--palette','--controls','--build-only'],cwd=ROOT,
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    for suffix in ('rom','sym'):
        shutil.copyfile(ROOT/f'outputs/render/presentation-controls.{suffix}',OUT/f'seaquest-video.{suffix}')
    print('Built private video cartridge and matching symbols under outputs/video/.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=OUT/'seaquest-video.rom')
    parser.add_argument('--machine', choices=('C-BIOS_MSX1','C-BIOS_MSX1_EU'),default='C-BIOS_MSX1_EU')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--frames', type=int, default=525)
    parser.add_argument('--scenario', choices=('attract','burst','dense','cold'), default='attract')
    parser.add_argument('--generation', choices=('normal','wrap','ready'),default='normal')
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--inject-clock-error', action='store_true',help='negative control: disable extra PAL updates')
    parser.add_argument('--inject-canonical-error', action='store_true',help='negative control: mutate a staged source byte')
    args = parser.parse_args()
    if args.build_only:
        build()
        return
    if args.frames<1:
        parser.error('--frames must be positive')
    if (args.inject_clock_error or args.inject_canonical_error) and (args.scenario=='cold' or args.machine!='C-BIOS_MSX1_EU'):
        parser.error('negative controls require a seeded PAL scenario')
    s = symbols(args.rom.with_suffix('.sym'))
    pal = args.machine.endswith('_EU')
    suffix = ('-clock-negative' if args.inject_clock_error else '')+('-state-negative' if args.inject_canonical_error else '')
    target = OUT/args.machine/(args.scenario+'-'+args.generation+('-quick' if args.quick else '')+suffix)
    target.mkdir(parents=True,exist_ok=True)
    rom = read_original()
    # Same real game-over source seed used by issue13; one seed per chain.
    cold = (ROOT/'outputs/input/natural.bin').read_bytes()
    seed_tick = next(t for t in range(1000,len(cold)//2303)
                     if (state:=cold[t*2303+2052:(t+1)*2303])[0xa3]
                     and not any(state[a] for a in (0xe9,0xbb,0xc2)))
    seed = bytearray(1024)
    seed[:251] = cold[seed_tick*2303+2052:(seed_tick+1)*2303]
    configs = [(n,240,1,63,0,255,0) for n in ([199] if args.quick else range(127,256))]
    if not args.quick:
        configs += [(n,240,1,63,action,phase,0) for n in (127,199,215,255)
                    for phase in (254,255,0) for action in (1,2,3)]
        configs += [(n,240,1,55,0,255,0) for n in (127,128,191,199,215,255)]
        configs += [(199,a3,player,63,0,255,0) for a3 in (1,96,104,159,160,255) for player in (0,1)]
    if args.scenario=='burst':
        configs = [(199,240,1,63,3,255,accum) for accum in ([0] if args.quick else range(262))]
    seeds = []
    for counter,a3,player,switches,action,phase,accum in configs:
        state = bytearray(seed)
        state[0x81],state[0xa2],state[0xa3],state[0xb7] = 160,counter,a3,player
        state[0x85],state[0x86] = ((2*counter)&255,7 if switches==55 else 247) if counter>=128 else (0,15 if switches==55 else 255)
        for lane in range(4):
            raw = 8 if state[0xd9+lane]&4 else rom[0xf0f+(state[0xbd]&7)]
            state[0xac+lane] = (raw^state[0x85])&state[0x86]
        state[0x280],state[0x282],state[0x284] = 255,switches,0
        state[12],state[13] = 128,128
        seeds.append(state)
    if args.scenario=='dense':
        names = json.loads((ROOT/'outputs/render/case-index.json').read_text())
        records = (ROOT/'outputs/render/cases.bin').read_bytes()
        costs = list(map(int,(ROOT/'outputs/render/cycles.txt').read_text().splitlines()))
        if len(records)!=len(names)*1034 or len(costs)!=len(names):
            raise ValueError('dense scenario requires presentation renderer records')
        indexes = sorted(range(len(names)),key=costs.__getitem__,reverse=True)
        indexes = [i for i in indexes if records[i*1034+10+0xa3]==0][:1 if args.quick else 32]
        seeds = [records[i*1034+10:(i+1)*1034] for i in indexes]
        configs = [(0,0,0,63,0,0,0) for _ in seeds]
        (target/'case-index.json').write_text(json.dumps([names[i] for i in indexes]))
    if args.scenario=='cold':
        seeds = []
        configs = []
    (target/'configs.json').write_text(json.dumps(configs)+'\n')
    (target/'seeds.bin').write_bytes(b''.join(seeds))
    names = ('rpc_done','core_F00E','core_F5B8','audio_prime_start','acquire_frame_state',
             'paced_frame_start','paced_start','paced_wait','paced_commit','video_after_commit','video_extra_core_start')
    script = ''.join(f'set {n} {s[n]}\n' for n in names)
    script += f'set sample_input_return {s["core_F6A9"]}\nset out {target}\nset frames {args.frames}\nset budget {71364 if pal else 59736}\nset cold {int(args.scenario=="cold")}\nset guard_ready 0\n'
    script += f'set expected_vdp {"TMS9929A" if pal else "TMS9918A"}\n'
    for name,column in (('switches',3),('actions',4),('phases',5),('accumulators',6)):
        script += 'set '+name+' {'+' '.join(str(row[column]) for row in configs)+'}\n'
    script += f'set generation_mode {args.generation}\nset palette_rebase_generations {s["palette_rebase_generations"]}\nset palette_prefetch {s["palette_prefetch"]}\n'
    script += f'set inject_clock_error {int(args.inject_clock_error)}\nset inject_canonical_error {int(args.inject_canonical_error)}\n'
    audio_hooks = audio_setup(s).replace('outputs/presentation/audio-natural-events.bin',str(target/'audio-events.bin'))
    audio_hooks = audio_hooks.replace('$::count','$::tick')
    audio_hooks = audio_hooks.replace('{$::recording}', '{$::recording && $::active_tick}')
    harness = (ROOT/'scripts/video_check.tcl').read_text()
    latency = []
    if args.scenario=='cold':
        # Capture a separate machine snapshot; replay device events carry both
        # joystick ports through the real PSG adapter, rather than RAM mirrors.
        seed_script = target/'replay-seed.tcl'
        seed_script.write_text(f'set renderer none\nset throttle off\nset z80_freq_locked true\nset power true\nplug joyporta msxjoystick1\nplug joyportb msxjoystick2\nreverse start\nafter time 1 {{reverse savereplay {target}/seed.omr; exit}}\n')
        with (target/'seed.log').open('w') as log:
            subprocess.run(['openmsx','-control','stdio','-machine',args.machine,'-cart',str(args.rom),
                            '-romtype','ASCII16','-script',str(seed_script)],cwd=ROOT,
                           env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                           stdout=log,stderr=subprocess.STDOUT,timeout=30,check=True)
        schedule = [(5.75,(0,0,64,0,0)),(6.35,(0,0,0,0,0)),(6.5,(0,0,1,0,0)),
                    (7.,(128,0,1,0,0)),(7.03,(0,0,1,0,0)),(7.2,(0,1,1,0,0)),
                    (7.23,(0,0,1,0,0)),(7.6,(0,0,17,0,0)),(7.8,(0,0,1,8,0)),
                    (8.4,(0,0,0,0,0)),(8.65,(64,0,0,0,0)),(8.72,(32,0,0,0,0)),(8.75,(0,0,0,0,0))]
        for n in range(16):
            time = 12+n*.2137
            left = bool(n&1)
            source = 'keyboard' if n<8 else 'joystick'
            controls = (0,0,16 if left else 128,0,0) if source=='keyboard' else (0,0,0,4 if left else 8,0)
            schedule += [(time,controls),(time+.04,(0,0,0,0,0))]
            latency.append(dict(time=time,source=source,direction=-1 if left else 1))
        events = [event for time,controls in sorted(schedule) for event in device_events(time,controls)]
        replay(target/'seed.omr',events,30,target/'input.omr')
        harness = harness.replace('set power true','set power true\nreverse loadreplay -goto begin -viewonly '+str(target/'input.omr'))
    (target/'start.tcl').write_text(script+audio_hooks+harness)
    (target/'raw.json').unlink(missing_ok=True)
    with (target/'openmsx.log').open('w') as log:
        result = subprocess.run(['openmsx','-control','stdio','-machine',args.machine,
                                '-cart',str(args.rom),'-romtype','ASCII16','-script',str(target/'start.tcl')],
                               cwd=ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                               stdout=log,stderr=subprocess.STDOUT,timeout=240)
    if result.returncode or not (target/'raw.json').exists():
        raise ValueError((target/'openmsx.log').read_text()[-2000:])
    data = (target/'native.bin').read_bytes()
    assets = extract(rom)
    timing = [json.loads(line) for line in (target/'timing.jsonl').read_text().splitlines()]
    ticks = [row for row in timing if row['kind']=='state']
    commits = [row for row in timing if row['kind']=='commit']
    if not ticks or len(data)!=len(ticks)*2303:
        raise ValueError('incomplete native trace')
    previous = None
    previous_chain = -1
    expected_audio = []
    model = None
    for index,offset in enumerate(range(0,len(data),2303)):
        raster = bytearray(data[offset:offset+1024])
        before = bytearray(data[offset+1024:offset+2048])
        expected_contacts = acquire(raster,rom,assets)
        for address in range(251):
            if before[address]!=expected_contacts[address]:
                raise ValueError(f'acquisition/staged source state tick={index} byte={address:02x}')
        before[0x280],before[0x282],before[12],before[13] = data[offset+2048:offset+2052]
        if ticks[index]['chain']!=previous_chain:
            previous = None
            model = AudioModel(before[21:27])
            previous_chain = ticks[index]['chain']
        if previous is not None:
            for address in range(0x80,251):
                if address not in (*range(0xb0,0xb7),0xf8,0xf9) and raster[address]!=previous[address]:
                    raise ValueError(f'reloaded game state tick={index} byte={address:02x}')
        expected,source_events,_ = trace(rom,before)
        for event in source_events:
            event['psg'] = model.write(event['address'],event['value']).hex()
        expected_audio.append(source_events)
        actual = data[offset+2052:offset+2303]
        if actual!=expected:
            byte = next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
            raise ValueError(f'source tick={index} byte={byte:02x}')
        previous = actual
    oracle = PresentationOracle(rom)
    pixels = (target/'pixels.bin').read_bytes()
    states = (target/'pixel-states.bin').read_bytes()
    meta = (target/'pixel-meta.bin').read_bytes()
    if len(meta)%3 or len(states)!=(len(meta)//3)*251 or len(pixels)!=(len(meta)//3)*16384:
        raise ValueError('incomplete pixel trace')
    for index in range(len(meta)//3):
        page,backdrop,r1 = meta[index*3:index*3+3]
        state = states[index*251:(index+1)*251]
        image = pixels[index*16384:(index+1)*16384]
        oracle.check(state,image,page*1024,backdrop&15,bool(r1&64))
        check_original_sprites(state,image,assets,rom,True)
    report = json.loads((target/'raw.json').read_text())
    if report['ticks']!=len(ticks) or report['frames']!=len(commits):
        raise ValueError('inconsistent native/display trace totals')
    if args.generation!='normal' and not report['generation_rebases']:
        raise ValueError('generation wrap was not exercised')
    if args.generation=='ready' and not report['ready_epoch_exposures']:
        raise ValueError('READY1/token240 was not exercised')
    for chain in range(max(1,len(seeds))):
        # The first displayed seed has no preceding queued extra update. Its
        # one-time empty pipeline is not a recurring simulation-clock drift.
        rows = [c for c in commits if c['chain']==chain][1:]
        for left,right in zip(rows,rows[262:]):
            if right['ticks']-left['ticks']!=(313 if pal else 262):
                raise ValueError('source clock drift over262 display frames')
    periods = [round((b['start_time']-a['start_time'])*3579545) for a,b in zip(commits,commits[1:]) if a['chain']==b['chain']]
    report['period_cycles'] = [min(periods),max(periods)]
    mean_period = sum(periods)/len(periods)
    if abs(mean_period-(71364 if pal else 59736))>2:
        raise ValueError('physical display period differs from the selected standard')
    report['measured_display_hz'] = round(3579545/mean_period,7)
    if any(expected_audio):
        report['audio'] = check_events(s,expected_audio,[str(i) for i in range(len(ticks))],target/'audio-events.bin')
    elif (target/'audio-events.bin').read_bytes():
        raise ValueError('unexpected audio stores in silent original chain')
    else:
        report['audio'] = dict(cases=len(ticks),ordered_stores=0)
    for event in latency:
        previous = max((t for t in ticks if t['time']<event['time']),key=lambda t:t['time'])
        updated = next(t for t in ticks if t['time']>=event['time'] and (t['x']-previous['x'])*event['direction']>0)
        mask = 64 if event['direction']<0 else 128
        sampled = next(t for t in timing if t['kind']=='sample' and t['time']>=event['time'] and not t['ports']&mask)
        previous_display = max((c for c in commits if c['time']<event['time']),key=lambda c:c['time'])
        shown = next(c for c in commits if c['time']>=updated['time'] and (c['x']-previous_display['x'])*event['direction']>0)
        event.update(sample_ms=round((sampled['time']-event['time'])*1000,4),
                     state_ms=round((updated['time']-event['time'])*1000,4),
                     sat_commit_ms=round((shown['time']-event['time'])*1000,4))
    if latency:
        report['latency'] = latency
        report['max_latency_ms'] = {k:max(e[k] for e in latency) for k in ('sample_ms','state_ms','sat_commit_ms')}
        period_ms = (71364 if pal else 59736)/3579.545
        if any(e['sample_ms']<0 or e['state_ms']<e['sample_ms'] or
               e['state_ms']>period_ms+5 or e['sat_commit_ms']>2*period_ms+5 for e in latency):
            raise ValueError('input response exceeds measured one/two-display-period allowance')
    report.update(machine=args.machine,rom_sha256=hashlib.sha256(args.rom.read_bytes()).hexdigest(),
                  source_ticks_verified=len(data)//2303,pixel_frames=len(meta)//3,
                  chains=max(1,len(seeds)),chain_frames=args.frames,seed_tick=seed_tick if seeds else None,
                  scenario=args.scenario,ram_reloads_after_chain_start=0)
    report.update(skipped_vdp_frames=0,visible_commits=0,generation_mode=args.generation,
                  initial_accumulators=sorted({row[6] for row in configs}),
                  startup_display_intervals_excluded=1,
                  cadence_windows_verified=sum(max(0,len([c for c in commits if c['chain']==chain])-263)
                                               for chain in range(max(1,len(seeds)))))
    report.update(original_sha256=SHA256,rom_bytes=args.rom.stat().st_size,mapper='ASCII16',
                  symbols_sha256=hashlib.sha256(args.rom.with_suffix('.sym').read_bytes()).hexdigest(),
                  seeds_sha256=hashlib.sha256((target/'seeds.bin').read_bytes()).hexdigest(),
                  cpu_hz=3579545,vdp='TMS9929A' if pal else 'TMS9918A',ram_kib=64,vram_kib=16,
                  display_period_cycles=71364 if pal else 59736,
                  python=platform.python_version(),openmsx=subprocess.check_output(['openmsx','-v'],text=True).strip(),
                  stack_measurement='C-BIOS init_ram C9 reserve, including startup' if args.scenario=='cold' else 'A5 marker after BIOS initialization',
                  physical_hardware=False,host_event_and_scanout_latency_measured=False)
    report['observed_machine'] = json.loads((target/'machine.json').read_text())
    (target/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('latency','audio')}))


if __name__=='__main__': main()
