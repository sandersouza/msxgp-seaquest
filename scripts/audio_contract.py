"""Compare ordered original stores, source frame epochs and real PSG registers.

Consumes the renderer's independently seeded records after --audio --progression.
No target cache or generated sound table supplies an expected value.
"""
import bisect
import hashlib
import json
import os
import re
import struct
import subprocess

from audio_reference import AudioModel, OUT, ROOT, trace
from input_contract import hardware
from original_graphics import extract, read_original
from oxygen_reference import acquire


def check_events(symbols,expected,selected,actual_path):
    native = sorted((value,int(name[5:],16)) for name,value in symbols.items() if re.fullmatch('core_[0-9A-F]{4}',name))
    addresses = [v for v,_ in native]
    actual = actual_path.read_bytes()
    event_size = 28
    if len(actual)%event_size: raise ValueError('partial audio event')
    positions = [0]*len(expected)
    delays,sites,controls = [],set(),set()
    representative = []
    for offset in range(0,len(actual),event_size):
        case,ret,shadow,frame,psg,delay = struct.unpack('<IH6sB11sI',actual[offset:offset+event_size])
        event = expected[case][positions[case]]
        pc = native[bisect.bisect_right(addresses,ret-1)-1][1]
        if (pc,shadow.hex(),frame)!=(event['pc'],event['shadow'],event['frame']):
            raise ValueError(f'audio order/epoch mismatch:{selected[case]}:{positions[case]}:{pc:04X}:{event}')
        # Peripheral direction bits belong to BIOS/input hardware, not music.
        masked = bytearray(psg); masked[7] &= 63
        if masked.hex()!=event['psg']:
            raise ValueError(f'PSG mismatch:{selected[case]}:{pc:04X}:actual{masked.hex()} expected{event["psg"]}')
        positions[case] += 1; delays.append(delay); sites.add(pc); controls.update(shadow[:2])
        if selected[case]=='progression-dense-38864': representative.append([f'{pc:04X}',delay])
    if positions!=[len(events) for events in expected]: raise ValueError('missing source audio stores')
    report = dict(cases=len(expected),ordered_stores=len(delays),source_sites=[f'{pc:04X}' for pc in sorted(sites)],
                  controls=sorted(controls),max_hook_cycles=max(delays),min_hook_cycles=min(delays),
                  dense_bonus_hooks=representative,
                  preserved='AF/BC/DE/HL/IX/IY/SP/IFF, PSG7 peripheral bits, PSG15 on every store',
                  oracle='independent py65 original instructions and explicit mathematical PSG policy',
                  limitation='seeded source ticks; oscillator phase and analog timbre are not identical')
    return report


def main():
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',
                                               (OUT/'audio64.sym').read_text(),re.M)}
    names = json.loads((ROOT/'outputs/render/case-index.json').read_text())
    data = (ROOT/'outputs/render/cases.bin').read_bytes()
    if len(data)!=1034*len(names): raise ValueError('audio requires renderer input records')
    rom = read_original()
    assets = extract(rom)
    records,expected,states,selected = [],[],[],[]
    # Retain all transitions in oxygen/progression plus representative dense,
    # collision and normal inputs. Source event-site coverage is reported.
    for index,name in enumerate(names):
        if index!=38863 and index%17 and not any(k in name for k in ('surface-','overlap-','bonus-',
                'death-','game-over-','chain-','group-complete-')): continue
        record = data[index*1034:(index+1)*1034]
        keys = record[6:10]
        ram = acquire(bytearray(record[10:]),rom,assets)
        r6,r7,r8,switches = keys
        ram[0x280],ram[0x282],ram[12],ram[13],_,_ = hardware((r6,r7,r8,0,0),ram[0xb7],switches,0)
        state,events,_ = trace(rom,ram)
        model = AudioModel(ram[0x15:0x1b])
        for event in events: event['psg'] = model.write(event['address'],event['value']).hex()
        records.append(bytes([0])+bytes(keys)+ram)
        expected.append(events); states.append(state); selected.append(name)
    from oxygen_contract import chains
    for name,seed,ticks,keys in chains(rom):
        if not (name.startswith('surface-6-') or name=='depletion-0' or name.startswith('bonus-progression-')): continue
        ram = bytearray(seed)
        model = AudioModel(ram[21:27])
        for tick in range(ticks):
            sampled = acquire(ram,rom,assets)
            sampled[0x280],sampled[0x282],sampled[12],sampled[13],_,_ = hardware((0,0,keys,0,0),sampled[0xb7],63,0)
            state,events,_ = trace(rom,sampled)
            for event in events: event['psg'] = model.write(event['address'],event['value']).hex()
            records.append(bytes([int(tick>0),0,0,keys,63])+sampled)
            expected.append(events); states.append(state); selected.append(f'chain-{name}-{tick}')
            ram[:251] = state
    (OUT/'audio-cases.bin').write_bytes(b''.join(records))
    (OUT/'audio-source-events.json').write_text(json.dumps(expected))
    start = ''.join(f'set {n} {symbols[n]}\n' for n in
                    ('audio_prime_only_start','audio_prime_only_done','audio_event_restored','core_F5B8'))
    start += 'set audio_handlers {'+' '.join(str(symbols[f'audio_event_{a:02X}']) for a in range(21,27))+'}\n'
    start += f'set inject_audio {int(os.environ.get("SEAQUEST_AUDIO_CORRUPT","0"))}\nsource scripts/audio_contract.tcl\n'
    (OUT/'audio-start.tcl').write_text(start)
    (OUT/'audio-complete.txt').unlink(missing_ok=True)
    with (OUT/'audio-contract.log').open('wb') as log:
        subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-cart',str(OUT/'audio64.rom'),
                        '-romtype','ASCII16','-script',str(OUT/'audio-start.tcl')],cwd=ROOT,
                       env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
    if int((OUT/'audio-complete.txt').read_text())!=len(records): raise ValueError('audio incomplete')
    actual_states = (OUT/'audio-states.bin').read_bytes()
    if actual_states!=b''.join(states):
        offset = next(i for i,(a,b) in enumerate(zip(actual_states,b''.join(states))) if a!=b)
        raise ValueError(f'audio source RAM mismatch:{selected[offset//251]}:{offset%251:02X}')
    report = check_events(symbols,expected,selected,OUT/'audio-events.bin')
    report['rom_sha256'] = hashlib.sha256((OUT/'audio64.rom').read_bytes()).hexdigest()
    (OUT/'audio-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__': main()
