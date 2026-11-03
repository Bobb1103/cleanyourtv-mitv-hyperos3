# 澎湃 3.0（HyperOS TV 3）适配笔记

一台机器的实测记录，不保证适用于其他型号，但踩过的坑大概率通用。

## 这台电视

| 项 | 值 |
| --- | --- |
| 型号 | 小米电视 MiTV-MFTR0（代号 freeguy，MediaTek mt9653） |
| 固件 | OS3.0.107.0.UFTMATV（HyperOS TV 3 / 澎湃） |
| 系统 | Android 14（SDK 34），**只有 armeabi-v7a 32 位** |
| 原桌面 | PatchWall，`com.mitv.tvhome` |
| GMS | 无（`pm list packages \| grep -c google` = 0） |
| Widevine | 无 CDM（`/vendor/lib/mediadrm/` 只有 clearkey） |

## 一、HOME 白名单：标准包名会被静默拒绝

CN 固件只允许白名单内的包名接管 HOME：

```bash
# 返回 Success，但实际不生效，FallbackHome 接管，最后落回系统设置页
adb shell cmd package set-home-activity com.gathin.tvhome/com.gathin.tvhome.MainActivity
```

**解法**：用 Gradle 参数把安装身份换成白名单内的包名，组件名保持不变。

```bash
cd launcher
./gradlew assembleRelease -PlauncherApplicationId=com.ts.launcher
adb install -r app/build/outputs/apk/release/app-release.apk
adb shell cmd package set-home-activity com.ts.launcher/com.gathin.tvhome.MainActivity
```

同一固件族里 `com.ts.launcher` 是有效的（ASTR0 机型已有人验证）。换机型时可以先试这个身份，
不行再回到 `device/` 里比对 `home-activities.txt`（`cmd package query-activities` 的原始输出）。

> 副作用：用 `com.ts.launcher` 身份构建时，资源 ID 前缀会变成 `com.ts.launcher:id/...`，
> 用 `uiautomator dump` 抓控件时记得跟着改（`tools/tv_check.py` 里已按这个身份匹配）。

## 二、停用系统应用

清单见 [debloat-packages.txt](../device/xiaomi-mitv-mftr0/debloat-packages.txt)，操作说明见
[device/xiaomi-mitv-mftr0/README.md](../device/xiaomi-mitv-mftr0/README.md)。

要点：

- 全部用 `pm disable-user --user 0`，**不卸载**，可逆。
- 停用分四类：遥测/广告/推送/云控 12 个、预装工具 7 个、AOSP 广告模块 4 个、系统更新 1 个。
- **保留**：小爱语音（voicecontrol / wakeupservice）、投屏（MiPlay / smartshare）、
  Mi Home + 电视管家、小米应用商店、全部流媒体。
- 组件级 `pm disable` 需要 root，这台机器没有 root（`adbd cannot run as root in production builds`），
  整包停用已经足够阻断。

### 系统自动更新

```bash
adb shell pm disable-user --user 0 com.xiaomi.mitv.upgrade   # 关闭
adb shell pm enable com.xiaomi.mitv.upgrade                  # 需要 OTA 时恢复
```

停用后：进程不存在、`monkey -p` 拉不起来、设置里的"系统更新"入口失效。

## 三、小米应用商店补一个入口

商店其实一直是 ENABLED，只是它的 `MainActivity` 只挂了小米自定义的 `APPSTORE_LAUNCHER` 类别，
**没有 LEANBACK 入口**，所以桌面网格里根本不显示。

解法：`launcher/shortcut/` 模块 —— 包名 `com.local.shortcut`，一个转发用的 Activity
（`AppStoreEntry`）把点击转发给 `com.xiaomi.mitv.appstore/com.xiaomi.mitv.appstore.MainActivity`，
图标从商店 APK 里提取（`res/OS.png`，192 px 橙色购物袋）。

## 四、图标与磁贴美化

改的是 `AppAdapter.java` 与 `item_app.xml`：

- `backdrop()` / `iconPlate()`：用图标边缘色填充底板，从 "uniform_tiles 主题专属"推广到
  所有无 banner 图标的卡片；图标尺寸 48 → 56 dp。
- `zoomIcon()`：图标主体过小时（夸克云朵、商店 Mi 标）裁掉留白再放大，上限 1.4×，
  用 `InsetDrawable` 负 inset 实现，比例不变。
- 网格名称常显：`GRID_NAME_ALPHA = 0.75`，Dock 不显示名称。
- 主题 `themes/uniform-tiles/` 下 `uniform_tiles: true` 让磁贴统一为图标卡；
  `tile_menu: true` 打开长按菜单（替换/移动/应用信息），换 Dock 应用不需要改代码。

> 坑：`Bitmap.getPixels` 读竖列时 stride 不能用行宽（`checkPixelsAccess` 按行校验），
> 会 `ArrayIndexOutOfBounds` 崩溃；改成逐像素 `getPixel` 就没事了。

## 五、已知限制

- **ADB 每次重启自动关闭**：设置 → 账号与安全 → ADB 调试 重新打开，首次连接要在电视上勾"一律允许"。
  日常用不着建议**装完就关**（5555 是明文端口）。
- **TVBox/影视仓在前台时按 HOME** 会先落奇异果开屏（固件行为），需要 `am force-stop` 再拉桌面。
- **Netflix 不可用**：无 GMS、无 Widevine CDM，L1 是硬件级刷不出来。
  能做的只有开无线显示用手机投屏，见 [netflix-compat-check.md](netflix-compat-check.md)。
- 电视只支持 `armeabi-v7a`，装 APK 前确认 ABI，别装 java64/java 变体。

## 六、本机构建环境（记录用）

| 项 | 值 |
| --- | --- |
| JDK | 17（Adoptium 17.0.20） |
| Android SDK | platform-34 + build-tools 34.0.0，`launcher/local.properties` 写 `sdk.dir` |
| 构建 | `cd launcher && ./gradlew assembleRelease [-PlauncherApplicationId=com.ts.launcher]` |
| Git Bash 调 Python 脚本 | 必须 `export MSYS_NO_PATHCONV=1`，否则远程路径被转成 Windows 路径 |

## 七、直播源（附带结论）

57 个候选地址实测只有 11 个能抓到播放列表，真正能看的更少。当前最佳：
`https://live.zbds.top/tv/iptv4.txt`（633 频道，可播率 86%）。完整清单与失效列表见
[live-sources.md](live-sources.md)。
