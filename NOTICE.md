# NOTICE

## 上游归属

本仓库是 [CleanYourTV](https://github.com/Gathin/cleanyourtv) 的 fork，上游代码、文档、
主题与插件全部保留，许可为 MIT © 2026 Gathin。上游原始文档放在 `docs/upstream/`。

上游没有、由本分支新增的部分：

- `launcher/app/src/main/java/com/gathin/tvhome/HabitPanel.java` — 打卡表 + 体重页
- `launcher/app/src/main/java/com/gathin/tvhome/HabitCalendar.java` — 打卡数据存储
- `launcher/app/src/main/java/com/gathin/tvhome/PixelBodyView.java` — 像素小人
- `launcher/shortcut/` — 小米应用商店入口壳（`com.local.shortcut`）
- `device/`、`docs/habit-panel.md`、`docs/pixel-figure.md`、`docs/mitv-hyperos3.md`
- `tools/` 中新增的 `tv_check.py`、`panel_visible.py`、`png_probe.py`、`preview_lift.py`、
  `gen_faint_mock.py`、`gen_lift_mock.py`

上游文件本分支改动过的主要有：`MainActivity.java`、`AppAdapter.java`、
`res/layout/activity_main.xml`、`res/layout/item_app.xml`、`res/values/config.xml`、
`res/values/strings.xml`，以及 `res/drawable/habit_*`、`res/values/` 里的 habit 资源。

## 第三方字体

Press Start 2P（SIL Open Font License 1.1）用于像素时钟，见 `launcher/FONT-LICENSE-OFL.txt`。

## 设备数据

`device/xiaomi-mitv-mftr0/` 下的包名、设置快照来自一台真实的小米电视
（型号 MiTV-MFTR0，代号 freeguy，固件 OS3.0.107.0.UFTMATV，Android 14）。
`android_id`、蓝牙 MAC 地址、小米账号 ID 已替换为 `<redacted>`。
这些快照仅作参考，**不保证适用于你的机型**。
