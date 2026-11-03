# -*- coding: utf-8 -*-
"""Decode a PNG without third-party libraries and report where the dock band and its tiles sit."""
import sys, zlib, struct

def decode(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, w, h, bd, ct = 8, b'', 0, 0, 0, 0
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos+4])[0]
        typ = d[pos+4:pos+8]
        data = d[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
        elif typ == b'IDAT':
            idat += data
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i-ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                b = prev[i]
                c = prev[i-ch] if i >= ch else 0
                pa, pb, pc = abs(b-c), abs(a-c), abs(a+b-2*c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y*stride:(y+1)*stride] = line
        prev = line
    return w, h, ch, bytes(out)

def bright_rows(w, h, ch, px):
    counts = []
    for y in range(h):
        n = 0
        base = y * w * ch
        for x in range(0, w, 2):
            i = base + x * ch
            if px[i] + px[i+1] + px[i+2] > 330:
                n += 1
        counts.append(n)
    return counts

def runs(w, ch, px, y, thr=330):
    res, start = [], None
    for x in range(w):
        i = y * w * ch + x * ch
        b = px[i] + px[i+1] + px[i+2] > thr
        if b and start is None:
            start = x
        elif not b and start is not None:
            if x - start > 40: res.append((start, x))
            start = None
    if start is not None and w - start > 40:
        res.append((start, w))
    return res

path = sys.argv[1] if len(sys.argv) > 1 else r'C:/Users/12638/Downloads/cleanyourtv-main/cur.png'
w, h, ch, px = decode(path)
print('image', w, h, 'channels', ch)
counts = bright_rows(w, h, ch, px)
# the dock: a long run of rows with many bright pixels
band = [y for y, n in enumerate(counts) if n > 250]
if band:
    print('bright band rows', band[0], '-', band[-1], ' (dp: %.0f - %.0f)' % (band[0]/2, band[-1]/2))
    mid = (band[0] + band[-1]) // 2
    print('tile runs at row', mid, runs(w, ch, px, mid))
    print('tile runs at row', band[0] + 8, runs(w, ch, px, band[0] + 8))
else:
    print('no bright band; top counts:', max(counts), 'at row', counts.index(max(counts)))
