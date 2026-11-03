# -*- coding: utf-8 -*-
"""The fainted figure, redesigned: three candidates on the same 16x26 grid and palette the code
uses, plus the current one for comparison. Output: mock-faint-redesign.png. Nothing here touches
the launcher; PixelBodyView.drawFainted stays as it is until one of these is picked.
"""
from PIL import Image, ImageDraw, ImageFont

PAL = {
    'S': (242, 201, 160),   # skin
    'Y': (217, 169, 78),    # shirt
    'T': (181, 128, 58),    # shirt stripe
    'H': (201, 143, 63),    # cap
    'R': (181, 122, 47),    # cap brim
    'O': (138, 90, 51),     # shorts / knees
    'E': (122, 116, 104),   # shoes
    'K': (240, 237, 224),   # sock / tongue
    'W': (255, 255, 255),
    'P': (44, 44, 42),      # pupil / dizzy marks
    'M': (138, 74, 58),     # mouth
    'X': (239, 159, 39),    # the spinning stars
    'D': (159, 203, 232),   # sweat / belly rumbles
}
BG = (7, 66, 32)
SHADOW = (6, 50, 26)

# --- A: lying on the side, one arm along the top, tongue out -------------------
A = ["................"] * 11 + [
    "...X............",
    "..XXX...........",
    "...X.......X....",
    "..........XXX...",
    "...........X....",
    ".HHHHH..........",
    "RRRRRRR.SSS.....",
    ".SSSSSS.YTYTY...",
    ".SPSPSSYTYTY....",
    ".PSSSPSYTYTY....",
    ".SSMMSSYTYTY....",
    "...KK.SS.....EE.",
    ".GGGGGGGGGGGGGG.",
] + ["................"] * 1

# --- B: flat on the back, one leg kicked straight up ---------------------------
B = ["................"] * 5 + [
    "............X...",
    "...........XXX..",
    "............X...",
    "................",
    "...X............",
    "..XXX......EEE..",
    "...X.......EEE..",
    "............SS..",
    "............SS..",
    ".HHHHHH....SS...",
    "RRRRRRRR...SS...",
    ".SPSPSSYYYYYOOSS",
    ".PSSSSPTTTTTOOSS",
    ".SSMMSSYYYYYOOSS",
    ".SSKKSSTTTTTOOEE",
    ".......SSS......",
    ".GGGGGGGGGGGGGG.",
] + ["................"] * 5

# --- C: sitting, knees up, the belly rumbling ----------------------------------
C = ["................"] * 4 + [
    "....X...........",
    "...XXX.....X....",
    "....X.....XXX...",
    "...........X....",
    "....HHHHHH......",
    "...RRRRRRRR.....",
    "....SSSSSS......",
    "....SPSSPS......",
    "....SSMMSS......",
    "...OYYYYYYO.....",
    "...OTTTTTTO.....",
    "...OYYYYYYO.D...",
    "...OYYYYYYO..D..",
    "...OTTTTTTO.....",
    "...SEE..EES.....",
    "..GGGGGGGGGGGG..",
] + ["................"] * 6

CELL = 14
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 30)
SMALL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)


def render(rows):
    w, h = 16 * CELL, 26 * CELL
    im = Image.new('RGB', (w, h), BG)
    dr = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        assert len(row) == 16, (y, row)
        for x, c in enumerate(row):
            if c == '.':
                continue
            if c == 'G':
                dr.rectangle([x * CELL, y * CELL, (x + 1) * CELL - 1, (y + 1) * CELL - 1], fill=SHADOW)
            else:
                dr.rectangle([x * CELL, y * CELL, (x + 1) * CELL - 1, (y + 1) * CELL - 1], fill=PAL[c])
    return im


# cards: (title, note, image)
current = Image.open('faint-now.png').convert('RGB').crop((640, 250, 950, 560))
current = current.resize((224, 224), Image.LANCZOS)
cur_card = Image.new('RGB', (224, 364), BG)
cur_card.paste(current, (0, 40))

cards = [
    ('现状', '星星贴着帽子像鹿角，躯干是一整块', cur_card),
    ('A 侧躺', '身体放平贴地，舌头吐出，星星离开头部', render(A)),
    ('B 仰面', '一脚朝天，一眼就懂"倒下了"', render(B)),
    ('C 抱膝坐', '肚子咕咕叫，饿到发晕，最贴"饿死了"', render(C)),
]

PAD, LABEL = 26, 92
cw = 224 + PAD * 2
ch = 364 + PAD + LABEL
gap = 26
W = cw * 4 + gap * 3 + PAD * 2
H = ch + 110
out = Image.new('RGB', (W, H), (16, 20, 18))
dr = ImageDraw.Draw(out)
dr.text((PAD, 30), '打卡页小人 · "饿死了"姿态重设计（仅效果图，未改代码）', font=FONT, fill=(240, 240, 235))

x = PAD
for title, note, img in cards:
    y0 = 110
    dr.rounded_rectangle([x, y0, x + cw, y0 + ch], 14, fill=BG, outline=(60, 90, 65), width=2)
    out.paste(img, (x + PAD, y0 + PAD // 2))
    dr.text((x + PAD, y0 + 364 + PAD + 6), title, font=FONT,
            fill=(239, 159, 39) if title != '现状' else (170, 175, 170))
    # wrap the note
    line, lines = '', []
    for chx in note:
        if dr.textlength(line + chx, font=SMALL) > cw - PAD * 2:
            lines.append(line); line = chx
        else:
            line += chx
    lines.append(line)
    for i, ln in enumerate(lines):
        dr.text((x + PAD, y0 + 364 + PAD + 48 + i * 28), ln, font=SMALL, fill=(185, 195, 188))
    x += cw + gap

out.save('mock-faint-redesign.png')
print('saved', out.size)
