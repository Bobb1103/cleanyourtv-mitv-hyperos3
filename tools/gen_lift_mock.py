# -*- coding: utf-8 -*-
"""The exercise pose, redrawn as a barbell lift: three candidates on the same 16x26 grid, plus the
running pose they would replace. Output: mock-lift-redesign.png. Nothing here touches the launcher;
PixelBodyView.drawRunning stays as it is until one of these is picked.
"""
from PIL import Image, ImageDraw, ImageFont

PAL = {
    'S': (242, 201, 160),   # skin
    'Y': (217, 169, 78),    # shirt
    'T': (181, 128, 58),    # shirt stripe
    'H': (201, 143, 63),    # cap
    'R': (181, 122, 47),    # cap brim
    'O': (138, 90, 51),     # shorts
    'E': (122, 116, 104),   # shoes
    'K': (240, 237, 224),   # sock
    'W': (255, 255, 255),
    'P': (44, 44, 42),      # pupil
    'M': (138, 74, 58),     # mouth
    'D': (159, 203, 232),   # sweat
    'B': (178, 178, 186),   # NEW: the bar
    'Q': (54, 54, 60),      # NEW: the plates
}
BG = (7, 66, 32)

# --- A: the bar overhead, arms straight ---------------------------------------
A = [
    "QQ............QQ",
    "QQBBBBBBBBBBBBQQ",
    "QQBBBBBBBBBBBBQQ",
    "QQSS........SSQQ",
    "..SS........SS..",
    "..SS........SS..",
    "..SS........SS..",
    "..YY.HHHHHH.YY..",
    "..YYRRRRRRRRYY..",
    "..YY.SSSSSS.YY..",
    "..YY.SPSSPS.YY..",
    "..YY.SSMMSS.YY..",
    "....YYYYYYYY....",
    "....YYYYYYYY...D",
    "....TTTTTTTT....",
    "D...YYYYYYYY....",
    "....YYYYYYYY....",
    "....TTTTTTTT....",
    "....YYYYYYYY....",
    "....OOOOOOOO....",
    "....OOOOOOOO....",
    ".....SS..SS.....",
    ".....SS..SS.....",
    ".....SS..SS.....",
    ".....KK..KK.....",
    "....EEE..EEE....",
]

# --- B: the bar held at the belly, arms straight down (the low half of a rep) --
B = [
    "................",
    "................",
    ".....HHHHHH.....",
    "....RRRRRRRR....",
    ".....SSSSSS.....",
    ".....SPSSPS.....",
    "D....SSSSSS.....",
    ".....SSMMSS.....",
    "...YYYYYYYYYY...",
    "...YYTTTTTTYY...",
    "...YYYYYYYYYY...",
    "QQ.SSYYYYYYSS.QQ",
    "QQ.SSYYYYYYSS.QQ",
    "QQBBBBBBBBBBBBQQ",
    "QQBBBBBBBBBBBBQQ",
    "...YYTTTTTTYY...",
    "....OOOOOOOO....",
    "....OOOOOOOO....",
    ".....SS..SS.....",
    ".....SS..SS.....",
    ".....SS..SS.....",
    ".....SS..SS.....",
    ".....SS..SS.....",
    ".....KK..KK.....",
    "....EEE..EEE....",
    "................",
]

# --- C: the bar across the shoulders, squatting --------------------------------
C = [
    "................",
    ".....HHHHHH.....",
    "....RRRRRRRR....",
    ".....SSSSSS.....",
    ".....SPSSPS.....",
    ".....SSSSSS.....",
    ".....SSMMSS.....",
    "QQBBBBBBBBBBBBQQ",
    "QQBBBBBBBBBBBBQQ",
    "..SS.YYYYYY.SS..",
    "...YYYYYYYYYY...",
    "...YYTTTTTTYY...",
    "...YYYYYYYYYY...",
    "...YYTTTTTTYY...",
    "...YYYYYYYYYY...",
    "....OOOOOOOO....",
    "....OOOOOOOO....",
    "....SS....SS....",
    "...SS......SS...",
    "...SS......SS...",
    "....SS....SS....",
    "....SS....SS....",
    "....SS....SS....",
    "....KK....KK....",
    "....EEE..EEE....",
    "................",
]

CELL = 14
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 30)
SMALL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 21)


def render(rows):
    im = Image.new('RGB', (16 * CELL, 26 * CELL), BG)
    dr = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        assert len(row) == 16, (y, row)
        for x, c in enumerate(row):
            if c == '.':
                continue
            dr.rectangle([x * CELL, y * CELL, (x + 1) * CELL - 1, (y + 1) * CELL - 1], fill=PAL[c])
    return im


now = Image.open('v15-zoom.png').convert('RGB')          # the running pose on the TV today
now = now.resize((224, 224), Image.LANCZOS)
now_card = Image.new('RGB', (224, 364), BG)
now_card.paste(now, (0, 40))

cards = [
    ('现状(跑步)', '需要两帧交替才看得出在跑', now_card),
    ('A 过顶举起', '单帧就认得出，画面填满', render(A)),
    ('B 腹前提起', '同一动作的下位，可作动画第一帧', render(B)),
    ('C 扛肩深蹲', '静态可读，但看不出"举"', render(C)),
]

PAD, LABEL = 26, 96
cw, ch = 224 + PAD * 2, 364 + PAD + LABEL
gap = 26
W = cw * 4 + gap * 3 + PAD * 2
H = ch + 150
out = Image.new('RGB', (W, H), (16, 20, 18))
dr = ImageDraw.Draw(out)
dr.text((PAD, 28), '运动形态重设计：跑步 → 举杠铃（仅效果图，未改代码）', font=FONT, fill=(240, 240, 235))
dr.text((PAD, 74), '推荐 A：静态最好认；若想保留动感，用 B→A 两帧循环 = 一次完整的举起（复用现有 300ms 换帧机制）',
        font=SMALL, fill=(150, 205, 160))

x = PAD
for title, note, img in cards:
    y0 = 116
    dr.rounded_rectangle([x, y0, x + cw, y0 + ch], 14, fill=BG, outline=(60, 90, 65), width=2)
    out.paste(img, (x + PAD, y0 + PAD // 2))
    dr.text((x + PAD, y0 + 364 + PAD + 4), title, font=FONT,
            fill=(239, 159, 39) if title != '现状(跑步)' else (170, 175, 170))
    line, lines = '', []
    for c in note:
        if dr.textlength(line + c, font=SMALL) > cw - PAD * 2:
            lines.append(line); line = c
        else:
            line += c
    lines.append(line)
    for i, ln in enumerate(lines):
        dr.text((x + PAD, y0 + 364 + PAD + 48 + i * 27), ln, font=SMALL, fill=(185, 195, 188))
    x += cw + gap

out.save('mock-lift-redesign.png')
print('saved', out.size)
