"""Independent original audio-store traces and explicit TIA-to-PSG policy.

The source still owns all timers, event priority and ordered writes. Pure4/12
pitch is rounded to the nearest PSG period. POLY9/POLY5 timbres are approximate;
the shared AY noise clock belongs to active source0 before active source1.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/presentation'
CONTROLS = {0,4,8,12,15}
MIX = [9,9,9,9,8,8,8,8,1,1,1,1,8,8,8,0]


def tone_period(control, frequency):
    if control not in CONTROLS: raise ValueError(f'unsupported source audio control{control}')
    if control in (0,8): return None
    # Type15's irregular POLY5/DIV3 output uses a square carrier plus AY noise.
    # Twice the divided-by-three carrier is an explicit timbre approximation.
    numerator = {4:114,12:342,15:684}[control]*(1+(frequency&31))
    return (numerator+8)//16


def noise_period(frequency):
    return min(31,max(1,(114*(1+(frequency&31))+16)//32))


class AudioModel:
    def __init__(self, shadow=None, ports=0):
        self.shadow = bytearray(6) if shadow is None else bytearray(shadow)
        self.ports = ports&192
        self.psg = [7,0,7,0,0,0,1,self.ports|63,0,0,0,0,0,0,0,0]
        for channel in range(2): self.period(channel)
        self.mixer()
        self.psg[8],self.psg[9] = self.shadow[4]&15,self.shadow[5]&15
        self.noise()

    def period(self, channel):
        period = tone_period(self.shadow[channel]&15,self.shadow[channel+2])
        if period is not None:
            self.psg[channel*2],self.psg[channel*2+1] = period&255,period>>8

    def mixer(self):
        controls = [self.shadow[channel]&15 for channel in range(2)]
        if any(control not in CONTROLS for control in controls):
            raise ValueError(f'source audio control outside audited set:{controls}')
        self.psg[7] = self.ports|36|MIX[controls[0]]|(MIX[controls[1]]<<1)

    def noise(self):
        for channel in range(2):
            if self.shadow[channel]&15 in (8,15) and self.shadow[channel+4]&15:
                self.psg[6] = noise_period(self.shadow[channel+2])
                break

    def write(self, address, value):
        index = address-0x15
        if not 0<=index<6: raise ValueError('not a TIA audio register')
        self.shadow[index] = value
        if index<2:
            self.period(index)
            self.mixer()
        elif index<4:
            self.period(index-2)
        else:
            self.psg[index+4] = value&15
        self.noise()
        return bytes(self.psg[:11])


def trace(rom, ram, entry=0xf5b8, a=0, x=0x82, y=0, carry=0):
    from py65.devices.mpu6502 import MPU

    class Memory(list):
        def __setitem__(self, address, value):
            super().__setitem__(address,value)
            if getattr(self,'record',False) and isinstance(address,int) and 0x15<=address<=0x1a:
                events.append(dict(pc=self.pc,address=address,value=value,
                                   frame=self[0x81],instruction_start_cycles=self.cycles,
                                   shadow=bytes(self[0x15:0x1b]).hex()))

    memory = Memory([0]*65536)
    memory[:len(ram)] = ram
    memory[0xf000:] = rom
    memory[0x1ff],memory[0x1fe] = 2,255
    cpu = MPU(memory=memory,pc=entry)
    cpu.a,cpu.x,cpu.y,cpu.p,cpu.sp = a,x,y,carry,0xfd
    events = []
    memory.record = True
    for steps in range(100000):
        memory.pc,memory.cycles = cpu.pc,cpu.processorCycles
        cpu.step()
        if cpu.pc in (0xf00e,0x300):
            return bytes(memory[:251]),events,steps+1
    raise ValueError(f'original audio trace did not finish:{cpu.pc:04X}')


def generate():
    data = bytearray()
    for control in (4,12,15):
        for frequency in range(32): data.extend(tone_period(control,frequency).to_bytes(2,'little'))
    data.extend(noise_period(frequency) for frequency in range(32))
    # Low bits0/3 are mixer disables; bits6/7 select the tone table; bit5
    # marks DC/noise-only. The runtime stores this on a control change.
    data.extend(MIX[c] | (32 if c in (0,8) else 64 if c==12 else 128 if c==15 else 0)
                for c in range(16))
    data.extend([7,0,7,0,0,0,1,63,0,0,0])
    if len(data)!=251: raise ValueError('audio data page size changed')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'audio-tables.bin').write_bytes(data)
    (OUT/'audio-tables.inc').write_text('    ALIGN 256\naudio_periods:\n'+
        '    INCBIN "audio-tables.bin"\n'+
        'audio_noise_periods EQU audio_periods+192\n'+
        'audio_mixer_parts EQU audio_periods+224\n'+
        'audio_defaults EQU audio_periods+240\n')
    print(json.dumps(dict(bytes=len(data),pure_periods=64,poly_carriers=32,noise_periods=32,
                          source_controls=sorted(CONTROLS))))


if __name__=='__main__': generate()
