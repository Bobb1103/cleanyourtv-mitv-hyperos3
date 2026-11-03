# -*- coding: utf-8 -*-
"""The lifting pose, two frames: B (the bar held at the belly) and A (the bar overhead), which loop
to make one rep. This mirrors what PixelBodyView.drawLifting does - same numbers, same order - so the
layout can be checked here in a second instead of after a two minute build. Nothing is written to the
launcher; keep the two in step by hand."""
from PIL import Image, ImageDraw

PAL = {
    'S': (242, 201, 160),   # skin
    'Y': (217, 169, 78),    # shirt
    'T': (181, 128, 58),    # shirt stripe
    'H': (201, 143, 63),    # cap
    'R': (181, 122, 47),    # cap brim
    'O': (138, 90, 51),     # shorts
    'E': (122, 116, 104),   # shoes
    'K': (240, 237, 224),   # collar
    'W': (255, 255, 255),   # eye white
    'P': (44, 44, 42),      # pupil
    'M': (138, 74, 58),     # mouth
    'D': (159, 203, 232),   # sweat
    'B': (178, 178, 186),   # the bar
    'Q': (16, 18, 22),      # the plates: near black, so they read heavy
    'L': (118, 124, 136),   # the rim of the outer plate, catching the light
}
BG = (6, 65, 32)
GRID_W, GRID_H = 16, 26
LEVELS = [(10, 3, 8), (9, 3, 8), (8, 2, 7), (7, 2, 6), (6, 1, 6)]

CELL = 13


class Grid:
    """The 16x26 board the figure is drawn on, with '.' left to whatever is behind it."""

    def __init__(self):
        self.cells = [['.'] * GRID_W for _ in range(GRID_H)]

    def px(self, x, y, w, h, ch):
        """Skia's rule for these rects: a square is filled when its middle falls inside, which is
        what leaves a column of face between the two eyes."""
        if w <= 0 or h <= 0:
            return
        for row in range(GRID_H):
            if not (y <= row + 0.5 < y + h):
                continue
            for col in range(GRID_W):
                if x <= col + 0.5 < x + w:
                    self.cells[row][col] = ch

    def rows(self):
        return [''.join(r) for r in self.cells]


def geom(level):
    """Torso width, leg gap, face width, torso left, head left, left sleeve, right sleeve, legs."""
    tw, lg, fw = LEVELS[level]
    return (tw, lg, fw, (GRID_W - tw) / 2, (GRID_W - fw) / 2,
            (GRID_W - tw) / 2 - 2, (GRID_W - tw) / 2 + tw,
            (12 - lg) / 2, (12 - lg) / 2 + 2 + lg)


def head(g, fx, top, fw):
    g.px(fx, top, fw, 2, 'H')
    g.px(fx - 1, top + 2, fw + 2, 1, 'R')
    g.px(fx, top + 3, fw, 4, 'S')
    ew = 3 if fw >= 8 else 2
    g.px(fx + 0.5, top + 4, ew, 2, 'W')
    g.px(fx + fw - 0.5 - ew, top + 4, ew, 2, 'W')
    g.px(fx + 1.5, top + 5, 1, 1, 'P')
    g.px(fx + fw - 2.5, top + 5, 1, 1, 'P')


def barbell(g, top):
    """Two rows of bar with a pair of plates either end, the plates sitting square on the bar's
    middle line - one row above it for one row below."""
    g.px(2, top, 12, 2, 'B')
    for x in (1, 14):
        g.px(x, top - 1, 1, 4, 'Q')            # the inner plate
        g.px(x - 1 if x == 1 else x + 1, top - 1, 1, 4, 'L')   # the outer plate's lit rim


def draw(level, overhead):
    g = Grid()
    tw, lg, fw, tx, fx, ax, bx, lx, rx = geom(level)
    if overhead:                                # arms straight up beside the head
        g.px(fx - 2, 5, 2, 9, 'Y')
        g.px(fx + fw, 5, 2, 9, 'Y')
    head(g, fx, 5, fw)
    g.px(7, 12, 2, 1, 'M')
    cw = max(2, fw - 4)
    g.px(8 - cw / 2, 13, cw, 1, 'K')
    for r in range(6):                          # torso, row by row so the brown bands run through
        g.px(tx, 14 + r, tw, 1, 'T' if r in (2, 4) else 'Y')
    g.px(tx, 20, tw, 3, 'O')
    g.px(lx, 23, 2, 2, 'S')
    g.px(rx, 23, 2, 2, 'S')
    g.px(lx - 0.5, 25, 3, 1, 'E')
    g.px(rx - 0.5, 25, 3, 1, 'E')
    if overhead:
        barbell(g, 1)
        g.px(fx - 2, 3, 2, 2, 'S')              # hands closing over the bar
        g.px(fx + fw, 3, 2, 2, 'S')
        g.px(0, 7, 1, 1, 'D')
        g.px(15, 9, 1, 1, 'D')
    else:
        barbell(g, 18)
        g.px(tx, 17, 2, 4, 'S')                 # hands inside the body's own outline
        g.px(tx + tw - 2, 17, 2, 4, 'S')
        g.px(0, 5, 1, 1, 'D')
        g.px(15, 7, 1, 1, 'D')
    return g.rows()


def render(rows, scale=CELL):
    im = Image.new('RGB', (GRID_W * scale, GRID_H * scale), BG)
    dr = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == '.':
                continue
            dr.rectangle([x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1],
                         fill=PAL[c])
    return im


frames = [('B - round body', draw(0, False)), ('A - round body', draw(0, True)),
          ('B - lean body', draw(4, False)), ('A - lean body', draw(4, True))]
for name, rows in frames:
    print('---', name)
    for i, r in enumerate(rows):
        print('%2d %s' % (i, r))

PAD, GAP = 22, 18
n = len(frames)
W = (GRID_W * CELL) * n + PAD * 2 + GAP * (n - 1)
H = GRID_H * CELL + PAD * 2
out = Image.new('RGB', (W, H), (6, 65, 32))
x = PAD
for name, rows in frames:
    out.paste(render(rows), (x, PAD))
    x += GRID_W * CELL + GAP
out = out.resize((int(out.width * 1.6), int(out.height * 1.6)), Image.NEAREST)
out.save('preview-lift.png')
print('saved', out.size)
