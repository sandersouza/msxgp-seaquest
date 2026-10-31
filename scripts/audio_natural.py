"""Ordered PSG evidence from every cold-boot native update; no game-RAM reloads."""
import hashlib
import json
from audio_contract import check_events
from audio_reference import AudioModel,OUT,ROOT,trace
from original_graphics import read_original


def setup(symbols):
    # Share the before/after hook observations used by the seeded audio check.
    source = (ROOT/'scripts/audio_contract.tcl').read_text()
    hooks = source[source.index('    foreach address $::audio_handlers'):source.index('    debug set_bp $::audio_prime_only_done')]
    prefix = 'set audio_events [open outputs/presentation/audio-natural-events.bin wb]\nset inject_audio 0\n'
    prefix += ''.join(f'set {n} {symbols[n]}\n' for n in ('audio_event_restored',))
    prefix += 'set audio_handlers {'+' '.join(str(symbols[f'audio_event_{a:02X}']) for a in range(21,27))+'}\n'
    prefix += source[source.index('proc audio_fail'):source.index('proc audio_next')]
    return prefix+hooks.replace('$::events','$::audio_events')+'\n'


def verify(symbols,cartridge,data):
    size = 2048+4+251
    rom = read_original()
    expected,names = [],[]
    model = AudioModel()
    for index,offset in enumerate(range(0,len(data),size)):
        before = bytearray(data[offset+1024:offset+2048])
        if bytes(model.shadow)!=before[21:27]: raise ValueError(f'continuous source audio state discontinuity:{index}')
        before[0x280],before[0x282],before[12],before[13] = data[offset+2048:offset+2052]
        _,events,_ = trace(rom,before)
        for event in events: event['psg'] = model.write(event['address'],event['value']).hex()
        expected.append(events); names.append(f'natural-{index}')
    report = check_events(symbols,expected,names,OUT/'audio-natural-events.bin')
    report.update(rom_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                  limitation='all cold source updates recorded; waveform phase and analog timbre remain approximate')
    (OUT/'audio-natural-result.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
