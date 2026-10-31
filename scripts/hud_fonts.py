"""MSX pixel-grid HUD lettering, explicitly adapted from the Atari style.

Score cells remain12x8 and oxygen cells8x8. Authored masks avoid the unequal
horizontal strokes introduced by a3:2 expansion of the original glyphs.
"""

SCORE = (
    ('.######.','##....##','##....##','##....##','##....##','##....##','##....##','.######.'),
    ('..####..','...##...','...##...','...##...','...##...','...##...','...##...','.######.'),
    ('.######.','##....##','......##','......##','.######.','##......','##......','########'),
    ('.######.','##....##','......##','....##..','....##..','......##','##....##','.######.'),
    ('....##..','..####..','.##.##..','##..##..','########','....##..','....##..','....##..'),
    ('########','##......','##......','######..','......##','......##','##....##','.######.'),
    ('.######.','##......','##......','######..','##....##','##....##','##....##','.######.'),
    ('########','##....##','......##','.....##.','....##..','...##...','...##...','...##...'),
    ('.######.','##....##','##....##','.######.','.######.','##....##','##....##','.######.'),
    ('.######.','##....##','##....##','##....##','..######','......##','......##','.######.'),
)

OXYGEN = (
    ('.####.','##..##','##..##','##..##','##..##','##..##','.####.'),
    ('##..##','##..##','.####.','..##..','.####.','##..##','##..##'),
    ('##..##','##..##','.####.','..##..','..##..','..##..','..##..'),
    ('.#####','##....','##....','##.###','##..##','##..##','.####.'),
    ('######','##....','##....','#####.','##....','##....','######'),
    ('##..##','###.##','###.##','######','##.###','##.###','##..##'),
)


def score_rows(digits):
    """Digits/None/source blank codeA in12-pixel cells; no resampling."""
    return [[12*column+1+x for column,digit in enumerate(digits) if digit not in (None,10)
             for x,pixel in enumerate(SCORE[digit][y]) if pixel=='#'] for y in range(8)]


def displayed_score(ram):
    digits = [(value>>shift)&15 for value in ram[0xb8:0xbb] for shift in (4,0)]
    significant = False
    for index,digit in enumerate(digits):
        significant |= digit!=0 or index==5
        if not significant: digits[index] = None
    return score_rows(digits)


def oxygen_rows():
    return [[8*column+1+x for column,glyph in enumerate(OXYGEN)
             for x,pixel in enumerate(glyph[y]) if pixel=='#'] for y in range(7)]+[[]]
