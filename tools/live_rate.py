#!/usr/bin/env python3
"""精确统计每个直播源的频道可用率。

过滤掉源里的说明行/占位行（时间戳、关于本源、mp4 宣传片等），
等距抽样更多频道，实测播放地址连通性。
"""
import random
import re
import socket
import ssl
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = "okhttp/3.14.9"
URL_RE = re.compile(r"https?://\S+")
random.seed(11)

SOURCES = [
    ("有魂直播 zb", "https://www.iyouhun.com/tv/zb"),
    ("Guovin iptv-api", "https://gh-proxy.com/https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u"),
    ("zbds IPTV4 txt", "https://live.zbds.top/tv/iptv4.txt"),
    ("zbds IPTV4 m3u", "https://live.zbds.top/tv/iptv4.m3u"),
    ("iptv-org 中国", "https://gh-proxy.com/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"),
    ("范明明 IPv6", "https://live.fanmingming.com/tv/m3u/ipv6.m3u"),
]

SAMPLE_N = 15
# 说明行/非真实频道的特征
JUNK = re.compile(r"关于本源|公众号|每日一首|MovieMusic|音乐欣赏|\.mp4|^\d{8}\s|免责|禁止贩卖|更新时间|本源由")


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read(8 * 1024 * 1024).decode("utf-8", "ignore")


def extract(text):
    lines = [l.strip() for l in text.splitlines()]
    out = []
    if "#EXTM3U" in text or "#EXTINF" in text:
        pending = None
        for l in lines:
            if l.startswith("#EXTINF"):
                m = re.search(r",\s*(.+)$", l)
                pending = m.group(1).strip() if m else "?"
            elif l and URL_RE.match(l):
                out.append((pending or "?", l))
                pending = None
    else:
        for l in lines:
            if not l or l.startswith("#") or "#genre#" in l:
                continue
            p = l.split(",", 1)
            if len(p) == 2 and URL_RE.search(p[1]):
                out.append((p[0].strip(), p[1].strip()))
    return out


def can_play(u, timeout=8):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            ct = (r.headers.get("Content-Type") or "").lower()
            r.read(8192)
            good = r.status == 200 and (
                "mpegurl" in ct or "octet-stream" in ct or "video" in ct or "audio" in ct
                or ct == "" or "text/plain" in ct
            )
            return good, r.status, ct
    except Exception as e:
        return False, 0, type(e).__name__


def main():
    socket.setdefaulttimeout(25)
    rows = []
    for name, url in SOURCES:
        try:
            text = fetch(url)
        except Exception as e:
            print(f"{name}: 源不可达 {type(e).__name__}")
            rows.append((name, url, 0, 0, 0))
            continue
        chans = extract(text)
        real = [(n, u) for n, u in chans if not JUNK.search(n)]
        if not real:
            real = chans
        step = max(1, len(real) // SAMPLE_N)
        picks = real[::step][:SAMPLE_N]
        with ThreadPoolExecutor(max_workers=10) as ex:
            res = list(ex.map(lambda c: can_play(c[1]), picks))
        ok = sum(1 for r in res if r[0])
        rows.append((name, url, len(real), ok, len(picks)))
        print(f"{name:<18} 有效频道 {len(real):>5}  抽样 {len(picks):>2}  可播 {ok:>2}  可用率 {ok*100//len(picks)}%")
        print(f"    {url}")
        fails = [(cn, cu, r) for (cn, cu), r in zip(picks, res) if not r[0]]
        for cn, cu, r in fails[:4]:
            print(f"    X {cn[:20]:<20} {cu[:56]}")
        print()

    print("=" * 92)
    print("推荐排序（按可播率 × 频道规模）")
    print("=" * 92)
    rows.sort(key=lambda r: -(r[3] * r[2] if r[4] else 0))
    for name, url, total, ok, n in rows:
        rate = f"{ok*100//n}%" if n else "-"
        print(f"{name:<18} 频道 {total:>5}  可播率 {rate:>4}    {url}")


if __name__ == "__main__":
    main()
