# 影视仓 / TVBox 直播源实测清单

> 实测时间：2026-10-25 11:20（本机网络出口，与电视同局域网）
> 检测方法：① 抓取源文件内容并判断是否为合法播放列表 → ② 每个源等距抽样 15 个频道，实测播放地址连通性
> 结论口径：**可播率 = 抽样频道中能连上的比例**，比"源地址能不能打开"更贴近真实体验

---

## 一、推荐（已实测可用）

### 🥇 首选：`zbds IPTV4`（综合最优）

| 格式 | 地址 | 频道数 | 可播率 |
|---|---|---|---|
| TXT（影视仓用这个） | `https://live.zbds.top/tv/iptv4.txt` | 633 | **86%** |
| M3U（TiviMate/PotPlayer 用） | `https://live.zbds.top/tv/iptv4.m3u` | 508 | 73% |

实测可播样例：CCTV3、浙江少儿、嘉兴新闻综合、武义新闻综合、烟台新闻综合、雅安新闻综合
→ 央视 + 各省卫视 + 大量地方台，稳定性最好，**优先填它**

### 🥈 备仓：`有魂直播`（频道量最大）

```
https://www.iyouhun.com/tv/zb
```
- 频道数 **7136**（海量，含影视轮播、音乐、地方台）
- 可播率 40%（量大但死链较多，当备用仓）

### 🥉 补充：`Guovin iptv-api`（自动测速仓库）

```
https://gh-proxy.com/https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u
```
- 频道数 1616，可播率 33%
- 该仓库每日自动测速筛选，但实际国内访问依赖 gh-proxy 加速

---

## 二、实测已失效（不要浪费时间）

| 名称 | 地址 | 失败原因 |
|---|---|---|
| 七星多仓 | `http://tvkj.top/DC.txt` | 403 |
| duomv fast | `https://gitlab.com/duomv/apps/-/raw/main/fast.json` | 403 |
| 高天流云 XYQ | `https://raw.githubusercontent.com/gaotianliuyun/...` | 403 |
| 华影视直播 | `https://download.kstore.space/download/4077/dzbzb.txt` | 401 |
| 进恩哥 | `http://jinenyy.vip/app/tvbox/tvbox.json` | 503 |
| 摸鱼多仓 | `http://我不是.摸鱼儿.top` | 502 |
| 饭太硬 | `http://饭太硬.top/tv` | 502 |
| 肥猫 | `http://肥猫.com` | 502 |
| 懒人 tv | `http://175.178.251.183:6689/tv.txt` | 502 |
| 小苹果 | `https://bitbucket.org/xduo/duoapi/raw/master/xpg.json` | 404 |
| 道长 | `https://gitlab.com/duomv/dzhipy/-/raw/main/index.json` | 404 |
| 书源直播 | `https://shuyuan.miaogongzi.net/...` | 404 |
| zzzzz 系列 | `https://zzzzz.tv/tv/*.txt` | 404 |
| 欧歌多仓 | `http://tv.nxog.top/` | 超时 |
| 安卓哥 / 盒子迷 ZB | 中文域名 | TLS 握手失败 |

> 网上流传的"2026 最新接口"文章里 80% 以上是旧列表转载，实测近半已 502/403。

---

## 三、影视仓填写方法

### 方式 A：只填直播（最省事）
1. 打开影视仓 → 右上角**设置**图标
2. 找到**直播地址**（部分版本叫"直播"）
3. 粘贴：`https://live.zbds.top/tv/iptv4.txt`
4. 确定 → 返回首页，进入"直播"板块即可

### 方式 B：本地导入（已帮你放到电视里）
我已把 4 个源推送到电视 **`/sdcard/Download/`**：

| 文件 | 说明 |
|---|---|
| `live-zbds-iptv4.txt` | zbds TXT 版（首选） |
| `live-zbds-iptv4.m3u` | zbds M3U 版 |
| `live-iyouhun-zb.txt` | 有魂 7136 频道 |
| `live-guovin.m3u` | Guovin 1616 频道 |

在影视仓设置里选**本地导入 / 文件**，到 Download 目录选对应文件即可。

### 方式 C：影视 + 直播一起（多仓接口）
把下面这段存成 json 上传到任意可直连的静态空间（GitHub Pages / Gitee Pages / 对象存储），
再把 URL 填进「**配置地址**」：

```json
{
  "lives": [
    {"name": "直播-主", "type": 0, "url": "https://live.zbds.top/tv/iptv4.txt"},
    {"name": "直播-备", "type": 0, "url": "https://www.iyouhun.com/tv/zb"}
  ]
}
```

---

## 四、注意事项

1. **时效性极强**：直播源随时失效，今天 86% 一周后可能大幅下降，建议隔段时间重跑检测脚本复检。
2. **脚本可复用**：`python tools/live_check.py`（批量连通性）和 `python tools/live_rate.py`（频道可播率），
   改脚本顶部 `CANDIDATES` / `SOURCES` 列表即可随时复检新地址。
3. **IPv6 源慎用**：`fanmingming` 的 ipv6.m3u 需要家庭网络支持 IPv6，本机无 IPv6 所以实测只有 13%，
   若你的宽带/路由器开了 IPv6，电视上可能反而很流畅（多为运营商内网源，速度快）。
4. **gh-proxy 是第三方加速**：用于绕过 raw.githubusercontent.com 访问不畅，若失效可换 `ghps.cc`、
   `raw.gitmirror.com` 等前缀，或直接访问原始地址。
5. **合规提醒**：请仅用于收看合法公开的免费频道，勿用于传播付费频道解密源。
6. 调试完记得在**设置 → 账号与安全**里关闭 ADB 调试。
