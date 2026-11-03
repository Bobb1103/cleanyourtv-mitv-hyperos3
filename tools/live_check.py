#!/usr/bin/env python3
"""批量实测 TVBox / 影视仓 直播源可用性。

判定标准：HTTP 200 + 内容形似播放列表 + 能解析出一定数量的频道/播放链接。
输出：格式（m3u / txt / json）、频道数、样例频道名。
"""
import json
import re
import socket
import ssl
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit

UA = "okhttp/3.14.9"
URL_RE = re.compile(r"https?://\S+")

CANDIDATES = [
    # ===== A. 长期维护的公开 IPTV 列表（无第三方接口依赖）=====
    ("A1 范明明 IPv6", "https://gh-proxy.com/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u"),
    ("A2 范明明 IPv6(直连)", "https://live.fanmingming.com/tv/m3u/ipv6.m3u"),
    ("A3 范明明 Global", "https://live.fanmingming.com/tv/m3u/global.m3u"),
    ("A4 iptv-org 中国", "https://gh-proxy.com/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"),
    ("A5 zbds IPTV4 m3u", "https://live.zbds.top/tv/iptv4.m3u"),
    ("A6 zbds IPTV4 txt", "https://live.zbds.top/tv/iptv4.txt"),
    ("A7 zbds IPTV6 m3u", "https://live.zbds.top/tv/iptv6.m3u"),
    ("A8 zbds IPTV6 txt", "https://live.zbds.top/tv/iptv6.txt"),
    ("A9 iptv365", "https://live.iptv365.org/live.m3u"),
    ("A10 Guovin iptv-api", "https://gh-proxy.com/https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u"),
    ("A11 YueChan IPTV", "https://gh-proxy.com/https://raw.githubusercontent.com/YueChan/live/main/IPTV.m3u"),
    ("A12 vbskycn ipv6", "https://gh-proxy.com/raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv6.m3u"),

    # ===== B. 圈内流传的「直播专用」地址 =====
    ("B1 有魂直播 zb", "https://www.iyouhun.com/tv/zb"),
    ("B2 月光宝盒直播", "https://agit.ai/guot54/ygbh/raw/branch/master/zB/zB.txt"),
    ("B3 华影视直播", "https://download.kstore.space/download/4077/dzbzb.txt"),
    ("B4 时光机直播", "https://www.bestpvp.site/tm/stable/live_stable.txt"),
    ("B5 书源直播", "https://shuyuan.miaogongzi.net/shuyuan/1697578744.txt"),
    ("B6 春盈天下部分", "https://pan.shangui.cc/f/ADNZfy/xmbjmzb.txt"),
    ("B7 春盈天下全部", "https://wds.ecsxs.com/230864.json"),
    ("B8 整挺好直播", "https://s2.pub/ZTHAIPTV21"),
    ("B9 安卓哥ZB", "https://xn--uirr31ao8x.com/ZB"),
    ("B10 盒子迷ZB", "https://xn--v8qt1h6qs7o.top/ZB"),
    ("B11 懒人tv", "http://175.178.251.183:6689/tv.txt"),
    ("B12 zzzzz live", "https://zzzzz.tv/tv/live.txt"),
    ("B13 zzzzz tv.txt", "https://zzzzz.tv/tv/tv.txt"),
    ("B14 tv.iill Live", "https://tv.iill.top/m3u/Live"),
    ("B15 tv.iill Gather", "https://tv.iill.top/m3u/Gather"),

    # ===== C. 多仓 / 单仓接口（内含直播模块）=====
    ("C1 摸鱼多仓", "http://xn--5rtp23ajya.top"),
    ("C2 欧歌多仓", "http://tv.nxog.top/"),
    ("C3 饭太硬", "http://xn--uirs0j23a8yb.top/tv"),
    ("C4 肥猫", "http://xn--sswy7d.com/"),
    ("C5 七星多仓", "http://tvkj.top/DC.txt"),
    ("C6 高天流云 XYQ", "https://ghps.cc/https://raw.githubusercontent.com/gaotianliuyun/gao/master/XYQ.json"),
    ("C7 DDX t4", "https://agit.ai/ddx/TVBox/raw/branch/master/t4.json"),
    ("C8 星河", "https://agit.ai/pinghui/xinghe/raw/branch/master/xinghe.txt"),
    ("C9 吾爱仓库", "https://agit.ai/l/l/raw/branch/master/o.json"),
    ("C10 duomv fast", "https://gitlab.com/duomv/apps/-/raw/main/fast.json"),
    ("C11 duo codered", "https://duo.codered.cloud/duo.json"),
    ("C12 心魔", "https://jihulab.com/yw88075/tvbox/-/raw/main/dr/js.json"),
    ("C13 饭太硬qist", "https://qist.wyfc.qzz.io/fty.json"),
    ("C14 潇洒", "https://qist.wyfc.qzz.io/xiaosa/api.json"),
    ("C15 fmys", "https://fmys.top/fmys.json"),
    ("C16 俊哥", "http://home.jundie.top:81/top98.json"),
    ("C17 小盒子4K", "http://xhztv.top/4k.json"),
    ("C18 欧歌接口", "https://xn--sdds-rp5imh.v.nxog.top/apitv.php?id=3"),
    ("C19 王二小", "https://9280.kstore.vip/newwex.json"),
    ("C20 巧儿", "https://pandown.pro/tvbox/tvbox.json"),
    ("C21 进恩哥", "http://jinenyy.vip/app/tvbox/tvbox.json"),
    ("C22 巧技", "https://cdn.qiaoji8.com/tvbox.json"),
    ("C23 恋影", "https://www.lianyingtv.com/fast/fast"),
    ("C24 小苹果", "https://bitbucket.org/xduo/duoapi/raw/master/xpg.json"),
    ("C25 小米DEMO", "https://mi.mpanso.me/DEMO.json"),
    ("C26 道长", "https://gitlab.com/duomv/dzhipy/-/raw/main/index.json"),
    ("C27 喵影", "https://meowtv.cn/tv"),
    ("C28 骚零", "https://100km.top/0"),
    ("C29 zzzzz z.txt", "https://zzzzz.tv/tv/z.txt"),
    ("C30 PG", "http://www.fish2018.us.kg/p/jsm.json"),
]


def punycode(url: str) -> str:
    """中文域名 → punycode。"""
    p = urlsplit(url)
    if not p.hostname:
        return url
    try:
        p.hostname.encode("ascii")
        return url
    except UnicodeEncodeError:
        pass
    enc = ".".join(lbl.encode("idna").decode() for lbl in p.hostname.split("."))
    netloc = enc
    if p.port:
        netloc += f":{p.port}"
    if p.username:
        auth = p.username + (f":{p.password}" if p.password else "")
        netloc = f"{auth}@{netloc}"
    return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))


def parse(text: str):
    """返回 (格式, 频道数, 样例列表)。"""
    lines = text.splitlines()
    fmt, chans = "?", 0
    if "#EXTM3U" in text or "#EXTINF" in text:
        fmt = "m3u"
        names = []
        for i, l in enumerate(lines):
            if l.strip().startswith("#EXTINF"):
                m = re.search(r",\s*(.+)$", l)
                if m:
                    names.append(m.group(1).strip())
            if not names and i > 200:
                break
        chans = sum(1 for l in lines if URL_RE.match(l.strip()))
        return fmt, chans, names[:5]
    if "#genre#" in text or re.search(r".+,\s*https?://", text):
        fmt = "txt"
        names = []
        for l in lines:
            if "#genre#" in l or not l.strip() or l.strip().startswith("#"):
                continue
            parts = l.split(",", 1)
            if len(parts) == 2 and URL_RE.search(parts[1]):
                names.append(parts[0].strip())
        return fmt, len(names), names[:5]
    if text.strip().startswith("{"):
        fmt = "json"
        try:
            data = json.loads(text)
        except Exception:
            return fmt, 0, []
        keys = [k for k in ("lives", "sites", "parses", "spider") if k in data]
        n = len(data.get("lives", []) or [])
        return fmt, n, [f"字段:{','.join(keys)}"]
    return fmt, 0, []


def probe(item, timeout=14):
    name, url = item
    target = punycode(url)
    req = urllib.request.Request(target, headers={"User-Agent": UA, "Accept": "*/*"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = r.read(4 * 1024 * 1024)
            text = raw.decode("utf-8", "ignore")
            fmt, chans, sample = parse(text)
            ok = (fmt == "m3u" and chans >= 5) or (fmt == "txt" and chans >= 5) or (fmt == "json" and chans > 0)
            return {"name": name, "url": url, "status": r.status, "bytes": len(raw),
                    "ok": ok, "fmt": fmt, "chans": chans, "sample": sample, "err": ""}
    except urllib.error.HTTPError as e:
        return {"name": name, "url": url, "status": e.code, "bytes": 0, "ok": False,
                "fmt": "-", "chans": 0, "sample": [], "err": f"HTTP {e.code}"}
    except Exception as e:
        return {"name": name, "url": url, "status": 0, "bytes": 0, "ok": False,
                "fmt": "-", "chans": 0, "sample": [], "err": type(e).__name__ + " " + str(e)[:60]}


def main():
    socket.setdefaulttimeout(18)
    with ThreadPoolExecutor(max_workers=14) as ex:
        res = list(ex.map(probe, CANDIDATES))
    good = [r for r in res if r["ok"]]
    bad = [r for r in res if not r["ok"]]
    good.sort(key=lambda r: -r["chans"])
    print("=" * 108)
    print("可用源")
    print("=" * 108)
    for r in good:
        print(f"[{r['fmt']:<3}] {r['name']:<16} 频道 {r['chans']:>5}  {r['bytes']:>9}B")
        print(f"      {r['url']}")
        if r["sample"]:
            print(f"      样例: {' / '.join(r['sample'][:5])}")
    print()
    print("=" * 108)
    print("失效源")
    print("=" * 108)
    for r in sorted(bad, key=lambda x: x["name"]):
        print(f"  {r['name']:<16} {r['url']}")
        print(f"      └─ {r['err']}")
    print()
    print(f"合计 {len(res)} 条 → 可用 {len(good)} / 失效 {len(bad)}")


if __name__ == "__main__":
    main()
