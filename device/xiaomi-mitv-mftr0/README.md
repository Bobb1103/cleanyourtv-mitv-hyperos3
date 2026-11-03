# MiTV-MFTR0 设备改动手册

一台小米电视（澎湃 / HyperOS TV 3）的降噪 + 桌面接管记录，含**全部可恢复的快照**。
改动说明见 [../../docs/mitv-hyperos3.md](../../docs/mitv-hyperos3.md)。

| 项 | 值 |
| --- | --- |
| 型号 | MiTV-MFTR0（freeguy，MediaTek mt9653） |
| 固件 | OS3.0.107.0.UFTMATV |
| 系统 | Android 14（SDK 34），armeabi-v7a |
| 原桌面 | PatchWall（`com.mitv.tvhome`） |
| 实测日期 | 2026-10-25 |

---

## ⚠️ 风险

- 停用系统应用会让**部分系统功能失效**（例如停用 `com.xiaomi.mitv.upgrade` = 不再收到 OTA）。
- 全部操作是 `pm disable-user`，**没有卸载**，可以逐条恢复；但删错会需要进恢复模式或刷机。
- `inventory/` 里的快照来自**这一台**电视，别的机型包名、白名单、设置项都可能不同。
  **先在你自己电视上跑一遍下面的"取快照"命令作对比，再决定停用哪些。**
- 快照已脱敏（`android_id`、蓝牙 MAC、小米账号 ID 替换为 `<redacted>`）。

---

## 0. 前置

电视上打开 ADB 调试：**设置 → 账号与安全 → ADB 调试**（或原生设置里的开发者选项），
首次连接在电视上勾"一律允许"。

```bash
export TV_HOST=<电视IP>:5555
adb connect $TV_HOST
adb devices            # 应看到 device
```

先取一份自己的快照（放到 `inventory/` 之外的目录，别覆盖本仓库的参考快照）：

```bash
mkdir -p my-tv-$(date +%Y%m%d)
adb shell pm list packages            > my-tv/packages.txt
adb shell pm list packages -s         > my-tv/packages-system.txt
adb shell pm list packages -3         > my-tv/packages-3rd.txt
adb shell pm list packages -d         > my-tv/packages-disabled.txt
adb shell settings list global        > my-tv/settings-global.txt
adb shell settings list secure        > my-tv/settings-secure.txt
adb shell settings list system        > my-tv/settings-system.txt
adb shell cmd package query-activities -a android.intent.action.MAIN \
    -c android.intent.category.HOME   > my-tv/home-activities.txt
```

## 1. 停用清单里的包

脚本在上游 `tools/`，需要一个 Python venv（`tv.py` 是 ADB 封装）：

```bash
python3 -m venv tools/venv
tools/venv/bin/pip install -r tools/requirements.txt      # Windows: tools/venv/Scripts/pip.exe

export MSYS_NO_PATHCONV=1                                  # Git Bash 必须
TV_HOST=$TV_HOST tools/disable.sh device/xiaomi-mitv-mftr0/debloat-packages.txt
```

停用后**重启电视**，再确认：

```bash
adb shell pm list packages -d        # 应包含清单里的每个包
adb shell dumpsys package com.xiaomi.mitv.upgrade | grep 'User 0:'   # enabled=false
```

想临时验证某个包能不能停用，先单独试：

```bash
adb shell pm disable-user --user 0 <包名>
adb shell pm enable <包名>            # 立刻回滚
```

## 2. 接管 HOME

标准包名在 CN 固件里会被静默拒绝，必须换安装身份：

```bash
cd launcher
./gradlew assembleRelease -PlauncherApplicationId=com.ts.launcher
adb install -r app/build/outputs/apk/release/app-release.apk
adb shell cmd package set-home-activity com.ts.launcher/com.gathin.tvhome.MainActivity
```

再按一下遥控器 HOME 键验证是否停在 CleanYourTV 上（若落回系统设置页，说明身份没进白名单，
见 [../../docs/mitv-hyperos3.md](../../docs/mitv-hyperos3.md) 第一节）。

原桌面停用：

```bash
adb shell pm disable-user --user 0 com.mitv.tvhome
```

## 3. 恢复原状

```bash
# 3.1 恢复清单里的包（脚本会读停用前的状态，本来就被停用的不会被动）
export MSYS_NO_PATHCONV=1
TV_HOST=$TV_HOST tools/restore.sh device/xiaomi-mitv-mftr0/debloat-packages.txt com.mitv.tvhome

# 3.2 恢复 PatchWall 与 HOME
adb shell pm enable com.mitv.tvhome
adb shell cmd package set-home-activity com.mitv.tvhome/.MainActivity   # 或按电视默认

# 3.3 需要 OTA 的话
adb shell pm enable com.xiaomi.mitv.upgrade

# 3.4 重启
adb reboot
```

CleanYourTV 本身可以直接卸载：`adb uninstall com.ts.launcher`。

---

## 快照清单（`inventory/`）

| 文件 | 内容 | 用途 |
| --- | --- | --- |
| `packages.txt` | `pm list packages` 全量 | 对照哪些包原本存在 |
| `packages-system.txt` | `-s` 系统包 | 判断哪些能停 |
| `packages-3rd.txt` | `-3` 三方包 | 别误停用户自己装的 |
| `packages-enabled-after.txt` | 改动后仍启用的包 | 对照组 |
| `packages-disabled-after-reboot.txt` | 重启后处于停用的包（25 个，含系统原本就停用的） | 验收依据 |
| `settings-global.txt` / `settings-secure.txt` / `settings-system.txt` | `settings list` 三个命名空间 | 找回被改动的开关 |
| `home-activities.txt` | `query-activities ... HOME` 原始输出 | 查白名单/可用桌面 |
| `home-resolve.txt` | `resolve-activity HOME` 结果 | 当时 HOME 指向 |

`debloat-packages.txt` 就是停用清单本身（24 个包，含分类注释）。

## FAQ

**Q：重启后连不上 ADB？**
A：这台电视每次重启会关掉 ADB 调试，去设置里重新打开。

**Q：桌面又变回系统设置页了？**
A：多半是 launcher 崩溃后系统清掉了默认桌面，重设即可：
`adb shell cmd package set-home-activity com.ts.launcher/com.gathin.tvhome.MainActivity`

**Q：误停用了关键包，电视异常？**
A：`adb shell pm enable <包名>`，或直接跑第 3 节的 `restore.sh` 全量恢复。

**Q：想用小米原生桌面但保留去广告？**
A：别停 `com.mitv.tvhome`，只跑清单里的遥测/广告那部分；桌面接管那步跳过。
