#!/usr/bin/env python3
"""Statically translate the original gameplay CFG; no CPU interpreter ships."""
import json
from pathlib import Path
from mos6502_isa import OPCODES
from reference_inventory import ROOT

SIZES = {'imp': 1, 'acc': 1, 'imm': 2, 'zpg': 2, 'zpx': 2, 'zpy': 2,
         'rel': 2, 'abs': 3, 'abx': 3, 'aby': 3, 'ind': 3, 'inx': 2, 'iny': 2}
BRANCHES = {'BCC', 'BCS', 'BEQ', 'BNE', 'BMI', 'BPL'}
ROOTS = [0xf5b8, 0xfb54, 0xfb56, 0xfb9d, 0xfedb, 0xffda, 0xffb4]
STOPS = {0xf00e}


def decode(rom, address):
    if not 0xf000 <= address <= 0xffff:
        raise ValueError(f'flow outside original ROM: {address:04X}')
    offset = address - 0xf000
    op = rom[offset]
    if op not in OPCODES:
        raise ValueError(f'unknown opcode {op:02X} at {address:04X}')
    mnemonic, mode = OPCODES[op]
    size = SIZES[mode]
    raw = rom[offset:offset + size]
    if len(raw) != size:
        raise ValueError('truncated instruction')
    value = int.from_bytes(raw[1:], 'little')
    target = ((address + 2 + (value if value < 128 else value - 256)) & 65535) if mode == 'rel' else value
    return {'address': address, 'mnemonic': mnemonic, 'mode': mode, 'size': size,
            'value': value, 'target': target}


def reachable(rom, roots=ROOTS, stops=STOPS):
    pending, result = list(roots), {}
    while pending:
        address = pending.pop()
        if address in stops or address in result:
            continue
        item = decode(rom, address)
        op, mode = item['mnemonic'], item['mode']
        if op in ('BRK', 'RTI', 'PHP', 'PLP', 'PHA', 'PLA', 'BVC', 'BVS', 'TXS', 'TSX', 'CLV') or mode in ('ind', 'inx', 'iny'):
            raise ValueError(f'unsupported gameplay instruction: {item}')
        result[address] = item
        if op in BRANCHES or op in ('JMP', 'JSR'):
            pending.append(item['target'])
        if op not in ('JMP', 'RTS'):
            pending.append((address + item['size']) & 65535)
    return result


def mapped(address):
    if address >= 0xf000:
        return f'original_rom+${address-0xf000:03X}'
    if address < 0x400:
        return f'CORE_RAM+${address:03X}'
    raise ValueError(f'unsupported memory address {address:04X}')


def pointer(item):
    mode, value = item['mode'], item['value']
    lines = [f'ld hl,{mapped(value)}']
    if mode in ('zpx', 'zpy', 'abx', 'aby'):
        index = 'b' if mode in ('zpx', 'abx') else 'c'
        lines += ['ld a,l', f'add a,{index}', 'ld l,a']
        if mode in ('abx', 'aby'):
            lines += ['jr nc,$+3', 'inc h']
    elif mode not in ('zpg', 'abs'):
        raise ValueError(f'unsupported pointer mode: {item}')
    return lines


def operand(item):
    lines = ['ld d,a']
    if item['mode'] == 'imm':
        lines += [f"ld h,${item['value']:02X}"]
    else:
        lines += pointer(item) + ['ld h,(hl)', 'ld a,d']
    return lines


def capture_c(inverted=False):
    return ['ld e,0', f"jr {'c' if inverted else 'nc'},$+4", 'ld e,1']


def translate(item):
    op, mode, address = item['mnemonic'], item['mode'], item['address']
    target = f"core_{item['target']:04X}"
    if op == 'JMP':
        return [f'jp {target}']
    if op == 'JSR':
        return [f'call {target}']
    if op == 'RTS':
        return ['ret']
    if op in ('BEQ', 'BNE', 'BMI', 'BPL'):
        return [f"jp {dict(BEQ='z', BNE='nz', BMI='m', BPL='p')[op]},{target}"]
    if op in ('BCC', 'BCS'):
        # RRCA preserves S/Z; E retains the 6502 carry independently of Z80 F.
        return ['ld d,a', 'ld a,e', 'rrca', 'ld a,d', f"jp {'c' if op == 'BCS' else 'nc'},{target}"]
    if op in ('CLC', 'SEC'):
        return [f"ld e,{int(op == 'SEC')}"]
    if op in ('SED', 'CLD', 'SEI', 'CLI', 'NOP'):
        # Decimal ADC is emitted only inside the original SED/CLD score block.
        return ['nop']
    if op in ('INX', 'DEX', 'INY', 'DEY'):
        return [f"{'inc' if op.startswith('IN') else 'dec'} {'b' if op.endswith('X') else 'c'}"]
    if op in ('TAX', 'TAY'):
        return [f"ld {'b' if op == 'TAX' else 'c'},a", 'or a']
    if op in ('TXA', 'TYA'):
        return [f"ld a,{'b' if op == 'TXA' else 'c'}", 'or a']
    if op in ('STA', 'STX', 'STY'):
        return ["ex af,af'"] + pointer(item) + ["ex af,af'", f"ld (hl),{dict(STA='a', STX='b', STY='c')[op]}"]
    if op in ('INC', 'DEC'):
        return ['ld d,a'] + pointer(item) + [f'{op.lower()} (hl)', 'ld a,d']
    if op in ('ASL', 'LSR', 'ROL', 'ROR'):
        lines = [] if mode == 'acc' else ['ld d,a'] + pointer(item) + ['ld a,(hl)']
        if op in ('ROL', 'ROR'):
            lines += ['srl e']
        lines += [dict(ASL='add a,a', LSR='srl a', ROL='rl a', ROR='rr a')[op]] + capture_c()
        if mode != 'acc':
            lines += ['ld (hl),a', 'ld a,d']
        return lines
    lines = operand(item)
    if op == 'LDA':
        return lines + ['ld a,h', 'or a']
    if op in ('LDX', 'LDY'):
        register = 'b' if op == 'LDX' else 'c'
        return lines + [f'ld {register},h', f'ld a,{register}', 'or a', 'ld a,d']
    if op in ('AND', 'ORA', 'EOR'):
        return lines + [f"{dict(AND='and', ORA='or', EOR='xor')[op]} h"]
    if op in ('CMP', 'CPX', 'CPY'):
        if op != 'CMP':
            lines += [f"ld a,{'b' if op == 'CPX' else 'c'}"]
        lines += ['cp h'] + capture_c(inverted=True)
        return lines + (['ld a,d'] if op != 'CMP' else [])
    if op in ('ADC', 'SBC'):
        lines += ['srl e']
        if op == 'SBC':
            lines += ['ccf']
        lines += [f'{op.lower()} a,h']
        if 0xfb9d <= address < 0xfbc9 and op == 'ADC':
            # NMOS decimal ADC gets N/Z from binary result, C from BCD result.
            lines += ['push af', 'daa'] + capture_c() + ['ld d,a', 'pop af', 'ld a,d']
        else:
            lines += capture_c(inverted=(op == 'SBC'))
        return lines
    if op == 'BIT':
        # Preserve A/C. N comes from memory; Z from A & memory. V is not used
        # by the accepted CFG (BVC/BVS/PHP/PLP are rejected above).
        return lines + ['and h', 'push af', 'rlc h', 'pop hl', 'res 7,l',
                        'jr nc,$+4', 'set 7,l', 'push hl', 'pop af', 'ld a,d']
    raise ValueError(f'unsupported translation: {item}')


def generate(rom):
    instructions = reachable(rom)
    addresses = sorted(instructions)
    lines = ['; Generated locally from the verified original. Do not commit this file.',
             'CORE_RAM EQU $C000', 'core_F00E:', '    ret']
    for n, address in enumerate(addresses):
        item = instructions[address]
        lines += [f'core_{address:04X}: ; {item["mnemonic"]} {item["mode"]}']
        lines += ['    ' + s for s in translate(item)]
        following = address + item['size']
        if item['mnemonic'] not in ('RTS', 'JMP') and (n + 1 == len(addresses) or addresses[n + 1] != following):
            lines += [f'    jp core_{following:04X}']
    return '\n'.join(lines) + '\n', instructions


def main():
    from reference_inventory import main as verify
    if verify([]):
        return 1
    rom = (ROOT / 'references/roms/seaquest-atari2600.a26').read_bytes()
    source, instructions = generate(rom)
    out = ROOT / 'outputs/native'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'core.inc').write_text(source)
    (out / 'original.rom').write_bytes(rom)
    (out / 'cfg.json').write_text(json.dumps(list(instructions.values()), indent=2) + '\n')
    print(f'Generated {len(instructions)} native instruction blocks.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
