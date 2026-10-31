"""Original-coordinate HUD masks, independently checked against Atari TIA pixels.

This module consumes canonical state at F00E. It never consumes target VRAM or
native presentation buffers. Generated original-derived pixels remain ignored.
"""
from original_graphics import bitmap, extract
from functools import lru_cache


@lru_cache(maxsize=1)
def source_assets(rom):
    return extract(rom)


def logo_top(counter):
    value = counter >> 3
    return 15 if value >= 20 else value - 4 if value >= 12 else 7


def masks(rom, ram):
    assets = source_assets(bytes(rom))
    digits = [(value >> shift) & 15 for value in ram[0xb8:0xbb]
              for shift in (4, 0)]
    significant = False
    score = [[] for _ in range(8)]
    for column, digit in enumerate(digits):
        significant |= digit != 0 or column == 5
        # Normal source scores contain BCD digits. Preserve the blank leading
        # positions, including five blanks when the complete score is zero.
        rows = bitmap(rom, 0xfe00 + digit*8, 8) if significant else [[]]*8
        for y, row in enumerate(rows):
            score[y].extend(8*column + x for x in row)

    def repeated(name, count):
        return [[8*copy + x for copy in range(min(count, 6)) for x in row]
                for row in assets[name]['rows']]

    divers = repeated('rescued-diver', ram[0xbe])
    if ram[0xbe] == 6 and ram[0xe1] != 13 and not ram[0x81] & 8:
        diver_color = (6 ^ ram[0x85]) & ram[0x86]
    else:
        diver_color = (0x82 ^ ram[0x85]) & ram[0x86]
    top = logo_top(ram[0xa3])
    logo = [[] for _ in range(8)]
    for column in range(6):
        for y, row in enumerate(bitmap(rom, 0xfe5b + column*16 + top - 7, 8)):
            logo[y].extend(8*column + x for x in row)
    diver_color &= 254          # TIA color registers ignore bit0
    main = [(value ^ ram[0x85]) & ram[0x86] & 254 for value in rom[0xcf0:0xcfb]]
    return {
        'score': dict(x=58, y=9, rows=score, foreground=main[ram[0xb7]], background=main[5]),
        'lives': dict(x=58, y=22, rows=repeated('life', ram[0xbb]),
                      foreground=main[ram[0xb7]], background=main[5]),
        'divers': dict(x=58, y=178, rows=divers, foreground=diver_color, background=main[8]),
        'logo': dict(x=58, y=190, rows=logo, foreground=main[10], background=main[6]),
    }


def check_tia():
    """Freeze through the source bonus early exit, retaining source preparation."""
    import itertools
    import json
    import numpy as np
    from graphics_reference import Reference, mask
    from original_graphics import ROOT, read_original, SHA256
    rom = read_original()
    ref = Reference()
    cases = []
    for score in (0, 1, 10, 101, 1000, 10001, 100010, 101010, 909090, 999999):
        digits = f'{score:06d}'
        cases.append(dict(b8=int(digits[:2], 16), b9=int(digits[2:4], 16), ba=int(digits[4:], 16)))
    for value in range(7):
        cases.append(dict(bb=value, be=value))
    for counter in range(256):
        cases.append(dict(a3=counter))
    for phase, player, inactivity in itertools.product((0, 7, 8, 15, 16, 255), range(2), (0, 128, 160, 255)):
        cases.append(dict(be=6, e1=20, **{'81':phase, 'b7':player, 'a2':inactivity}))
    checked = 0
    for changes in cases:
        image = ref.image(**changes)
        # ALE returns after source processing. This captures source RAM only;
        # no state is taken from the MSX oracle or renderer.
        ram = bytearray(1024)
        ram[128:256] = bytes(ref.ale.getRAM())
        for name, field in masks(rom, ram).items():
            x, y, rows = field['x'], field['y'], field['rows']
            expected = np.full((len(rows), 48), field['background'], dtype=np.uint8)
            expected[mask(rows, 0, 0, expected.shape)] = field['foreground']
            actual = image[y:y+len(rows), x:x+48]
            if not np.array_equal(actual, expected):
                yy, xx = np.where(actual != expected)
                raise ValueError(f'{name} {changes}: {len(xx)} differences, first={xx[0]},{yy[0]}, '
                                 f'source={actual[yy[0],xx[0]]} model={expected[yy[0],xx[0]]}, '
                                 f'phase={ram[0x81]} counter={ram[0xa3]}')
            checked += 1
    out = ROOT/'outputs/presentation'
    out.mkdir(parents=True, exist_ok=True)
    result = dict(cases=len(cases), field_comparisons=checked, original_sha256=SHA256,
                  authority='ALE/Stella original ROM pixels; model consumes original canonical RAM',
                  scope='six-digit score and blanking, reserves, diver count/flash, all256 logo counter values')
    (out/'hud-tia.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    check_tia()
