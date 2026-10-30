"""Read-before-write audit of the omitted source display phase.

This is CPU dependency evidence, not a TIA geometry oracle. Real TIA acquisition
is checked separately by collision-contract and the continuous natural replay.
"""
import itertools


def score_reference(rom,ram,amount,carry):
    """Return source RAM plus A/X/Y/C/N/Z, including NMOS decimal flags."""
    from py65.devices.mpu6502 import MPU
    memory = [0]*65536
    memory[:len(ram)],memory[0xf000:] = ram,rom
    memory[0x1ff],memory[0x1fe] = 2,255
    cpu = MPU(memory=memory,pc=0xfb9d)
    cpu.a,cpu.x,cpu.y,cpu.p,cpu.sp = amount,0,0,carry,0xfd
    for _ in range(100):
        cpu.step()
        if cpu.pc==0x300:
            return bytes(memory[:251]),bytes([cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p&0x82])
    raise ValueError('original score subroutine did not return')


class PhaseMemory(list):
    def __init__(self,rom,ram):
        super().__init__([0]*65536)
        self[:len(ram)] = ram
        self[0xf000:] = rom
        self.phase = 'display'
        self.display_writes = set()
        self.core_writes = set()
        self.dependencies = set()

    def __getitem__(self,address):
        if isinstance(address,int) and self.phase=='core':
            if address in self.display_writes and address not in self.core_writes:
                self.dependencies.add(address)
        return super().__getitem__(address)

    def __setitem__(self,address,value):
        if isinstance(address,int) and 0x80<=address<=0xfa:
            if getattr(self,'phase',None)=='display': self.display_writes.add(address)
            if getattr(self,'phase',None)=='core': self.core_writes.add(address)
        super().__setitem__(address,value)


def audit(rom,base,extra_states=()):
    from py65.devices.mpu6502 import MPU
    from collision_reference import contacts
    from original_graphics import extract
    dependencies,writes = set(),set()
    count,states = 0,[]
    assets = extract(rom)
    for special,death,oxygen,phase,player in itertools.product(
            (0,1,6),(0,1,10,23),(0,16,64),(0,15,255),range(2)):
        ram = bytearray(base)
        ram[0xe8],ram[0xe9],ram[0xe6],ram[0x81],ram[0xb7] = special,death,oxygen,phase,player
        states.append(ram)
    for ram in itertools.chain(states,extra_states):
        memory = PhaseMemory(rom,ram)
        cpu = MPU(memory=memory,pc=0xf00e)
        for _ in range(20000):
            if cpu.pc==0xf5b8: break
            cpu.step()
        else: raise ValueError(f'display audit stuck at {cpu.pc:04x}')
        # Exercise source collision branches as well as neutral paths. Occupancy
        # remains a separate, Atari-verified hardware oracle; never copy native
        # latch RAM into this dependency audit.
        acquired = contacts(ram,rom,assets)
        for a,value in zip((*range(0xb0,0xb7),0xf8),acquired): memory[a] = value
        writes.update(memory.display_writes)
        memory.phase = 'core'
        # Source hardware reads: neutral devices, zero timer. Collision latch
        # values here are CPU-only; the separate TIA oracle checks their geometry.
        memory[0x280],memory[0x282],memory[12],memory[13],memory[0x284] = 255,63,128,128,0
        for _ in range(20000):
            cpu.step()
            if cpu.pc==0xf00e: break
        else: raise ValueError(f'core audit stuck at {cpu.pc:04x}')
        dependencies.update(memory.dependencies)
        count += 1
    allowed = {*range(0xb0,0xb7),0xf8,0xf9}
    if not dependencies<=allowed:
        raise ValueError(f'omitted source inputs: {sorted(dependencies-allowed)}')
    return dict(cases=count,display_writes=[f'{i:02x}' for i in sorted(writes)],
                core_reads_before_overwrite=[f'{i:02x}' for i in sorted(dependencies)],
                method='original F00E..F5B8 then F5B8..F00E; tracked source memory reads/writes',
                limitation='dynamic branch coverage; source hardware occupancy certified separately')
