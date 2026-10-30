"""Explicit NTSC TIA hue/luminance adaptation to fixed TMS9918 colors.

This is a display policy, not an RGB-equivalence or collision transformation.
Index 0 is reserved for sprite transparency; opaque black uses index 1.
"""

# TIA hue0 grayscale, then gold/orange/red/purple/blue/cyan/green/yellow.
# Low/high luminance pairs chosen for the original NTSC source revision.
HUES = ((14,15),(10,11),(10,11),(6,9),(6,9),(13,13),(13,13),(4,5),
        (4,5),(4,5),(7,7),(12,3),(12,3),(12,3),(10,11),(10,11))


def tms_color(tia):
    tia &= 254
    if tia == 0: return 1
    if tia == 8: return 14
    if tia == 12: return 14
    return HUES[tia>>4][int((tia&15)>=10)]


def sprite_colors(ram,rom):
    player = (rom[0xcf3+(ram[0xb7]&1)]^ram[0x85])&ram[0x86]
    if ram[0xe9]: player = rom[0xf17+min(ram[0xe9],23)]
    diver = (rom[0xcfa]^ram[0x85])&ram[0x86]
    return [tms_color(player)]*3+[tms_color(diver)]*4+[tms_color(8)]
