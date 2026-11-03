#!/usr/bin/env python3
"""第二层验证：从直播源里抽样频道，实测播放地址是否真能连上。

只下载 + 测 HTTP 连通性，不解码、不长时间占用带宽。
"""
import json
import random
import re
import socket
import ssl
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit

UA = "okhttp/3.14.9"
URL_RE = re.compile(r"https?://\S+")
random.seed(7)

SOURCES = [
    ("有魂直播 zb", "https://www.iyouhun.com/tv/zb"),
    ("Guovin iptv-api", "https://gh-proxy.com/https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u"),
    ("zbds IPTV4 txt", "https://live.zbds.top/tv/iptv4.txt"),
    ("iptv-org 中国", "https://gh-proxy.com/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"),
    ("zbds IPTV4 m3u", "https://live.zbds.top/tv/iptv4.m3u"),
    ("范明明 IPv6", "https://live.fanmingming.com/tv/m3u/ipv6.m3u"),
    ("潇洒(多仓)", "https://qist.wyfc.qzz.io/xiaosa/api.json"),
    ("iptv365", "https://live.iptv365.org/live.m3u"),
    ("俊哥(多仓)", "http://home.jundie.top:81/top98.json"),
    ("王二小(多仓)", "https://9280.kstore.vip/newwex.json"),
]

SAMPLE_N = 8


def punycode(url):
    from urllib.parse import urlsplit as _s, urlunsplit as _u
    p = _s(url)
    if not p.hostname:
        return url
    try:
        p.hostname.encode("ascii")
        return url
    except UnicodeEncodeError:
        pass
    enc = ".".join(lbl.encode("idna").decode() for lbl in p.hostname.split("."))
    netloc = enc + (f":{p.port}" if p.port else "")
    return _u((p.scheme, netloc, p.path, p.query, p.fragment))


def fetch(url, timeout=20):
    req = urllib.request.Request(punycode(url), headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read(8 * 1024 * 1024).decode("utf-8", "ignore")


def extract(text):
    """返回 [(频道名, 播放地址)]，兼容 m3u / txt。"""
    lines = [l.strip() for l in text.splitlines()]
    out = []
    if "#EXTM3U" in text or "#EXTINF" in text:
        pending = None
        for l in lines:
            if l.startswith("#EXTINF"):
                m = re.search(r",\s*(.+)$", l)
                pending = m.group(1).strip() if m else "?"
            elif l and URL_RE.match(l):
                out.append((pending or l, l))
                pending = None
    else:
        for l in lines:
            if "#genre#" in l or l.startswith("#") or not l:
                continue
            parts = l.split(",", 1)
            if len(parts) == 2 and URL_RE.search(parts[1]):
                out.append((parts[0].strip(), parts[1].strip()))
    return out


def head(u, timeout=8):
    try:
        req = urllib.request.Request(punycode(u), headers={"User-Agent": UA})
        req.get_method = lambda: "GET"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            ct = r.headers.get("Content-Type", "")
            r.read(4096)
            return True, r.status, ct
    except Exception as e:
        return False, 0, type(e).__name__ + " " + str(e)[:40]


def main():
    socket.setdefaulttimeout(20)
    print("第二层验证：抽查每个源的频道播放地址\n")
    summary = []
    for name, url in SOURCES:
        try:
            text = fetch(url)
        except Exception as e:
            print(f"[源不可达] {name}  {url}  ({type(e).__name__})")
            summary.append((name, url, 0, 0, 0))
            continue
        chans = extract(text)
        if not chans:
            print(f"[无频道]   {name}  {url}")
            summary.append((name, url, 0, 0, 0))
            continue
        step = max(1, len(chans) // SAMPLE_N)
        picks = chans[::step][:SAMPLE_N]
        with ThreadPoolExecutor(max_workers=8) as ex:
            res = list(ex.map(lambda c: head(c[1]), picks))
        ok = sum(1 for r in res if r[0])
        print(f"[{'通过' if ok >= len(picks) // 2 else '偏差'}] {name}  总频道 {len(chans):>5}  抽样 {len(picks)}  连通 {ok}")
        print(f"       {url}")
        for (cn, cu), r in zip(picks, res):
            mark = "OK " if r[0] else "X  "
            print(f"       {mark}{cn[:22]:<24}{cu[:62]}")
        print()
        summary.append((name, url, len(chans), ok, len(picks)))

    print("=" * 96)
    print("汇总（按抽样连通率排序）")
    print("=" * 96)
    print(f"{'名称':<18}{'总频道':>8}{'连通/抽样':>12}   地址")
    for name, url, total, ok, n in sorted(summary, key=lambda s: (-(s[3] / s[4] if s[4] else 0), -s[2])):
        rate = f"{ok}/{n}" if n else "-"
        print(f"{name:<18}{total:>8}{rate:>12}   {url}")


if __name__ == "__main__":
    main()
