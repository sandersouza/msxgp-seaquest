#!/usr/bin/env python3
"""Synthetic SCREEN 2 expansion tables; no original game inputs required."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def shifted_row(value, phase, parity):
    bits = 0
    origin = parity * 3 // 2
    for x in range(8):
        if value & (128 >> x):
            for dest in range((parity+x)*3//2-origin, (parity+x+1)*3//2-origin):
                bits |= 1 << (23-phase-dest)
    return bits.to_bytes(3, 'big')


def sprite_peak(ys):
    return max(sum(y <= line < y+16 for y in ys if y != 216) for line in range(192))


def generate():
    out = ROOT / 'outputs/render'
    out.mkdir(parents=True, exist_ok=True)
    lut = bytearray()
    for parity in range(2):
        for phase in range(8):
            for column in range(3):
                lut.extend(shifted_row(value, phase, parity)[column] for value in range(256))
    (out / 'expand.bin').write_bytes(lut)
    reverse = bytes(int(f'{v:08b}'[::-1], 2) for v in range(256))
    (out / 'reverse.bin').write_bytes(reverse)
    print(f'Generated {len(lut)}-byte phase/parity expansion LUT.')


if __name__ == '__main__': generate()
