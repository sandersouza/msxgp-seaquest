"""Execute the original omitted HUD block; do not seed F9 from native RAM."""


def alarm(rom, ram):
    from py65.devices.mpu6502 import MPU
    memory = bytearray(65536)
    memory[:len(ram)] = ram
    memory[0xf000:] = rom
    cpu = MPU(memory=memory, pc=0xf44f)
    for _ in range(24):
        if cpu.pc == 0xf473:
            return memory[0xf9]
        cpu.step()
    raise ValueError(f'original alarm block did not terminate: {cpu.pc:04X}')


def acquire(ram, rom, assets):
    from collision_reference import contacts
    sampled = bytearray(ram)
    acquired = contacts(ram, rom, assets)
    sampled[0xb0:0xb7], sampled[0xf8] = acquired[:7], acquired[7]
    sampled[0xf9] = alarm(rom, ram)
    return sampled
