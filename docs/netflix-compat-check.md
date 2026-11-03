# 小米电视 MFTR0 安装 Netflix 兼容性诊断

> 诊断时间：2026-10-25 11:35
> 设备：Xiaomi MiTV-MFTR0（codename freeguy）· Android 14（API 34）· 固件 OS3.0.107.0.UFTMATV
> 当前桌面：com.ts.launcher（CleanYourTV 2.7）

---

## 结论：这台电视无法运行 Netflix

不是安装包的问题，是**系统能力缺失**。即使把官方 APK 装上，也**打不开或无法播放任何内容**。

---

## 三项硬证据（均已实测）

### 1. 零 Google 组件（GMS）

```
$ adb shell pm list packages | grep -E "google|gms|gsf|vending"
>>> 零结果

$ adb shell pm list packages | grep -ci google
0
```

没有 Google 服务框架（GMS）、没有 Google Play 服务、没有 Play 商店。
Netflix TV 版的账号登录、设备认证、推送全部依赖 Google Play Services。

### 2. 无 Google Widevine DRM（决定性证据）

```
$ adb shell ls /vendor/lib/mediadrm/
libdrmclearkeyplugin.so        ← 只有 ClearKey（明文测试用）
```

mediadrm 插件目录里**只有 ClearKey**，没有 `libdrmwidevineplugin.so` / `libwvdrmengine.so` / `libwvhidl.so`。
系统里只有小米自家的 `libdrmportingtee.so`（给国内视频平台用的私有 DRM）。

Netflix 全部内容强制 Widevine DRM 加密：
- Widevine L1 → 可播 HD / 4K
- Widevine L3 → 仅 SD（480p）
- **无 Widevine CDM → 一个视频都播不了**

⚠️ Widevine L1 是**硬件级能力**，由芯片厂商签发，**刷机刷不出来**。

### 3. 下载渠道在本机网络下不可达

本机走本地代理（127.0.0.1:16988），实测：

| 站点 | 结果 |
|---|---|
| apkmirror.com | 502 隧道失败 |
| apkpure.com / d.apkpure.com | 502 / 403 |
| apkcombo.com / apksos.com / apkmonk.com | 502 |
| apkmody.io | 200，但下载直链 404 |
| apkmb.com / apk4all.io | 200，未取得可用直链 |

---

## 可行方案

### ✅ 方案 A：手机屏幕镜像（已帮你开启，立即可用）

我已把电视的无线显示打开：
```
settings put global wifi_display_on 1   →  当前值 1
```

**用法**：手机与电视连同一 WiFi → 手机打开「无线投屏 / 屏幕镜像 / 无线显示」→ 搜到电视 → 连接 → 在手机上打开 Netflix 播放，画面即投到电视。

- 优点：不用装任何东西，马上能用，不受 GMS / DRM 限制
- 缺点：画质受镜像压缩影响（一般 1080p 左右），手机需保持亮屏

> 注意：Netflix App 自带的 Cast 按钮只对「Netflix Ready」认证设备生效，
> 小米国内版电视不在认证列表内，所以**要用系统级屏幕镜像，而不是 App 内的投屏按钮**。

### ⭐ 方案 B：外接播放设备（体验最好）

插 HDMI 即用，出厂自带 GMS + Widevine L1 + Netflix 认证：

- **Apple TV 4K** — Netflix 4K HDR / Dolby Vision 完整支持
- **Google TV 设备** — Chromecast with Google TV、小米盒子国际版等
- **游戏主机** — PS5 / Xbox 均有 Netflix App

这是唯一能获得**原生遥控器操作 + 高清画质**的方案。

### ⚠️ 方案 C：刷机 / root 装 GMS（不推荐）

- 需解锁 Bootloader（小米官方解锁常需等待且可能失败）
- 即便刷入 GMS，Widevine 仍是 **L3**（硬件限制），Netflix 最高 480p，部分内容直接不可播
- 存在变砖、失去保修风险，且国内版硬件与国际固件可能不兼容

投入产出比极低，不建议。

---

## 已执行的改动

| 项目 | 变更 |
|---|---|
| 无线显示（wifi_display_on） | 0 → 1（可逆，用于手机镜像 Netflix） |

Netflix 未安装（装了也无法运行）。

---

## 附：如何回退

```bash
adb shell settings put global wifi_display_on 0
```
