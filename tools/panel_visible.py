"""Is the habit panel on screen? Counts the green "day kept" pixels inside the panel's patch of
screen. The panel is the only thing there that is that green, so a handful means it is showing and
none means it has faded out behind the apps."""
import struct
import sys
import zlib


def read_png(path):
    d = open(path, 'rb').read()
    pos = 8
    w = h = ct = bd = None
    idat = b''
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos + 4])[0]
        typ = d[pos + 4:pos + 8]
        data = d[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
        elif typ == b'IDAT':
            idat += data
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bpp = ch * (bd // 8)
    stride = w * bpp
    out = bytearray()
    prev = bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line
        prev = line
    return w, h, ch, out


def count_green(path, box):
    """box in device pixels: (x0, y0, x1, y1)."""
    w, h, ch, px = read_png(path)
    x0, y0, x1, y1 = box
    n = 0
    for y in range(max(0, y0), min(h, y1)):
        base = y * w * ch
        for x in range(max(0, x0), min(w, x1)):
            o = base + x * ch
            r, g, b = px[o], px[o + 1], px[o + 2]
            if 120 < r < 190 and 155 < g < 225 and 45 < b < 130:
                n += 1
    return n


if __name__ == '__main__':
    # The panel's patch of screen on this TV: 120,228 to 932,642 device pixels.
    box = (120, 228, 932, 642)
    for path in sys.argv[1:]:
        print(f'{path}: green pixels in panel = {count_green(path, box)}')
