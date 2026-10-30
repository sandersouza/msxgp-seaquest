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


def translate(item, nz_live=True, carry_relation=None):
    op, mode, address = item['mnemonic'], item['mode'], item['address']
    target = f"core_{item['target']:04X}"
    if mode in ('zpg', 'abs') and op in ('INC', 'DEC'):
        return [f"ld hl,{mapped(item['value'])}", f'{op.lower()} (hl)']
    if mode in ('zpg', 'abs') and op in ('STX', 'STY'):
        return [f"ld hl,{mapped(item['value'])}", f"ld (hl),{'b' if op=='STX' else 'c'}"]
    # Direct accumulator accesses need no address-building scratch registers.
    # OR restores the 6502 N/Z flags; its carry lives independently in E.
    if mode in ('zpg', 'abs') and op == 'LDA':
        return [f"ld a,({mapped(item['value'])})"] + (['or a'] if nz_live else [])
    if mode in ('zpg', 'abs') and op == 'STA':
        return [f"ld ({mapped(item['value'])}),a"]
    if op == 'LDA':
        if mode == 'imm':
            return [f"ld a,${item['value']:02X}"] + (['or a'] if nz_live else [])
        return pointer(item) + ['ld a,(hl)'] + (['or a'] if nz_live else [])
    if mode in ('imm', 'zpg', 'abs') and op in ('LDX', 'LDY', 'CPX', 'CPY'):
        register = 'b' if op in ('LDX', 'CPX') else 'c'
        value = f"${item['value']:02X}"
        lines = ['ld d,a']
        if op in ('LDX', 'LDY'):
            if not nz_live:
                return [f'ld {register},{value}'] if mode=='imm' else [f"ld hl,{mapped(item['value'])}",f'ld {register},(hl)']
            lines += ([f'ld a,{value}'] if mode == 'imm' else [f"ld a,({mapped(item['value'])})"])
            return lines + [f'ld {register},a', 'or a', 'ld a,d']
        lines += [f'ld a,{register}']
        if mode != 'imm':
            lines += [f"ld hl,{mapped(item['value'])}"]
            value = '(hl)'
        return lines + [f'cp {value}'] + capture_c(inverted=True) + ['ld a,d']
    if mode in ('imm', 'zpg', 'abs') and op in ('AND', 'ORA', 'EOR', 'CMP', 'ADC', 'SBC'):
        lines = [] if mode == 'imm' else [f"ld hl,{mapped(item['value'])}"]
        value = f"${item['value']:02X}" if mode == 'imm' else '(hl)'
        if op in ('ADC', 'SBC'):
            lines += ['srl e']
            if op == 'SBC':
                lines += ['ccf']
            lines += [f'{op.lower()} a,{value}']
            lines += capture_c(inverted=(op == 'SBC'))
        elif op == 'CMP':
            lines += [f'cp {value}'] + capture_c(inverted=True)
        else:
            lines += [f"{dict(AND='and', ORA='or', EOR='xor')[op]} {value}"]
        return lines
    if op == 'JMP':
        return [f'jp {target}']
    if op == 'JSR':
        return [f'call {target}']
    if op == 'RTS':
        return ['ret']
    if op in ('BEQ', 'BNE', 'BMI', 'BPL'):
        return [f"jp {dict(BEQ='z', BNE='nz', BMI='m', BPL='p')[op]},{target}"]
    if op in ('BCC', 'BCS'):
        if carry_relation is not None:
            condition = 'c' if (op=='BCS') == carry_relation else 'nc'
            return [f'jp {condition},{target}']
        # RRCA preserves S/Z; E retains the 6502 carry independently of Z80 F.
        return ['ld d,a', 'ld a,e', 'rrca', 'ld a,d', f"jp {'c' if op == 'BCS' else 'nc'},{target}"]
    if op in ('CLC', 'SEC'):
        return [f"ld e,{int(op == 'SEC')}"]
    if op in ('SED', 'CLD', 'SEI', 'CLI', 'NOP'):
        # The sole SED/CLD score block is specialized by generate().
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
    for a,item in instructions.items():
        if item['mnemonic'] in BRANCHES|{'JMP','JSR'} and 0xfb9d<item['target']<=0xfbca and not 0xfb9d<=a<=0xfbca:
            raise ValueError('external entry into specialized score routine')
    addresses = sorted(instructions)
    carry_defs = {'ADC','SBC','ASL','LSR','ROL','ROR','CMP','CPX','CPY','CLC','SEC'}
    nz_defs = {'LDA','LDX','LDY','TAX','TAY','TXA','TYA','INX','DEX','INY','DEY',
               'INC','DEC','ADC','SBC','AND','ORA','EOR','ASL','LSR','ROL','ROR','CMP','CPX','CPY','BIT'}
    targets = set(ROOTS) | {i['target'] for i in instructions.values() if i['mnemonic'] in BRANCHES|{'JMP','JSR'}}
    relations = {}
    for n,address in enumerate(addresses):
        if not n or address in targets or instructions[address]['mnemonic'] not in ('BCC','BCS'):
            continue
        previous = instructions[addresses[n-1]]
        if previous['address']+previous['size']!=address:
            continue
        if previous['mnemonic'] in ('CMP','CPX','CPY','SBC'):
            relations[address] = False
        elif previous['mnemonic'] in ('ASL','LSR','ROL','ROR','ADC') and not (0xfb9d<=previous['address']<0xfbc9):
            relations[address] = True
    def live_after(defs, uses, native_uses=frozenset()):
        incoming = {a:False for a in addresses}
        outgoing = dict(incoming)
        changed = True
        while changed:
            changed = False
            for a in reversed(addresses):
                item = instructions[a]
                op = item['mnemonic']
                following = a+item['size']
                successors = ([item['target']] if op=='JMP' else
                              [following,item['target']] if op in BRANCHES else [following])
                # Calls/returns are conservative flag barriers. No assumptions
                # about callee writes or callers' use of a returned status.
                out = op in ('JSR','RTS') or any(incoming.get(s,True) for s in successors)
                value = (op in uses and a not in native_uses) or op in ('JSR','RTS') or (out and op not in defs)
                if value != incoming[a] or out != outgoing[a]:
                    incoming[a],outgoing[a],changed = value,out,True
        return outgoing
    carry_out = live_after(carry_defs,{'ADC','SBC','ROL','ROR','BCC','BCS'},set(relations))
    nz_out = live_after(nz_defs,{'BEQ','BNE','BMI','BPL'})
    lines = ['; Generated locally from the verified original. Do not commit this file.',
             'CORE_RAM EQU $C000', 'core_F00E:', '    ret']
    for n, address in enumerate(addresses):
        if 0xfb9d<address<=0xfbca:
            continue  # Folded into the verified score block at its sole entry.
        item = instructions[address]
        lines += [f'core_{address:04X}: ; {item["mnemonic"]} {item["mode"]}']
        if address == 0xfb9d:
            # Guarded terminal-score specialization. With valid nonzero BCD A
            # and all three score bytes99, every original ADC overflows, score
            # stores end at99, B9 is nonzero so no reserve can be added, and A3
            # increments once. No code observes the intermediate score stores
            # (DI; no calls/I/O in this path). Retain each call/event and return
            # the original A/X/Y/C/N/Z; use the regular BCD path otherwise.
            lines += [
                '    ld d,a', '    or a', '    jr z,.score_regular',
                '    ld a,(CORE_RAM+$0BA)', '    cp $99', '    jr nz,.score_restore',
                '    ld a,(CORE_RAM+$0B9)', '    cp $99', '    jr nz,.score_restore',
                '    ld a,(CORE_RAM+$0B8)', '    cp $99', '    jr nz,.score_restore',
                '    ld hl,CORE_RAM+$0A3', '    inc (hl)',
                '    ld a,$99', '    or a', '    ld e,1', '    ret',
                '.score_restore:', '    ld a,d', '.score_regular:']
            # Same low/middle/high BCD additions and ordered observable writes.
            # Source NZ is dead on both carry paths. A no-carry low return gets
            # NMOS NZ from adjusted A. If middle addition does not carry, the
            # high add/store is an identity and B9!=0, so no life check can fire.
            # No calls, I/O or interrupts can observe the omitted identity stores.
            lines += [
                '    ld hl,CORE_RAM+$0BA', '    add a,(hl)', '    daa', '    ld (hl),a',
                '    jr c,.score_middle', '    ld e,0', '    or a', '    ret',
                '.score_middle:', '    ld hl,CORE_RAM+$0B9', '    ld a,(hl)',
                '    adc a,0', '    daa', '    ld (hl),a', '    jr c,.score_high',
                '    ld e,0', '    or a', '    ret',
                '.score_high:', '    ld hl,CORE_RAM+$0B8', '    ld a,(hl)',
                '    adc a,0', '    daa', '    jr nc,.score_high_store',
                '    ld a,$99', '    ld (CORE_RAM+$0B9),a', '    ld (CORE_RAM+$0BA),a',
                '    ld hl,CORE_RAM+$0A3', '    inc (hl)', '    ld (CORE_RAM+$0B8),a',
                '    ld e,1', '    or a', '    ret',
                '.score_high_store:', '    ld (hl),a',
                '    ld hl,CORE_RAM+$0BB', '    ld a,(hl)', '    cp 6',
                '    ld e,1', '    ret nc', '    ld e,0', '    inc (hl)', '    ret']
            continue
        if address == 0xf6a7:
            lines += ['    IFDEF WITH_INPUT', '    call sample_input', '    ENDIF']
        emitted = translate(item,nz_out[address],relations.get(address))
        # Capturing E is unnecessary when every following path replaces the
        # source carry before reading it. Keep instruction order unchanged.
        if item['mnemonic'] in carry_defs and not carry_out[address]:
            if item['mnemonic'] in ('CLC','SEC'):
                emitted = []
            else:
                capture = capture_c(inverted=item['mnemonic'] in ('SBC','CMP','CPX','CPY'))
                for offset in range(len(emitted)-len(capture)+1):
                    if emitted[offset:offset+len(capture)] == capture:
                        emitted = emitted[:offset]+emitted[offset+len(capture):]
                        break
        lines += ['    ' + s for s in emitted]
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
