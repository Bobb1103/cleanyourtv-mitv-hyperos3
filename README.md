# cleanyourtv-mitv-hyperos3

> A CleanYourTV fork for Xiaomi TV (HyperOS TV 3): a **weight-loss habit launcher** plus a written-up **HyperOS 3 device adaption record**.
> Fork of upstream [CleanYourTV](https://github.com/Gathin/cleanyourtv) (MIT, (c) 2026 Gathin). Every upstream feature is kept; this branch adds two layers on top.

![Home screen overview](docs/images/home-overview.png)

---

## Read this first

- **The launcher half** (habit calendar, weight page, pixel figure) is ordinary Android application code. Build it, install it, done. No risk involved.
- **The device half** (`device/xiaomi-mitv-mftr0/`, disabling system apps and taking over HOME) changes the state of your TV:
  - Everything goes through **ADB disable, never uninstall**, so one command puts it all back;
  - Disabling `com.xiaomi.mitv.upgrade` means **no more official OTA firmware updates** until you enable it again;
  - After taking over HOME, the stock PatchWall launcher is still on the box (only disabled) and you can switch back at any time;
  - Firmware, package names and HOME whitelists differ per TV. **The lists here were tested on exactly one model: MiTV-MFTR0 (codename freeguy, OS3.0.107.0.UFTMATV, Android 14).** On any other model, compare against the snapshots in `device/xiaomi-mitv-mftr0/inventory/` before you touch anything.
- Device snapshots in this repository are redacted: `android_id`, the Bluetooth MAC and the Xiaomi account id are all replaced with `<redacted>`.

---

## What is in here

### 1. Launcher customisation (added by this branch, not in upstream)

| Feature | What it does | Docs |
| --- | --- | --- |
| Streak calendar | One square per day from the start date to today. **Left pressed twice** checks in or undoes it; a single press does nothing, so a stray touch cannot mark a day | [docs/habit-panel.md](docs/habit-panel.md) |
| Weight page | **Right** on the calendar: start / current / goal weight, days checked in, and the level | [docs/habit-panel.md](docs/habit-panel.md) |
| Pixel figure | A 16x26 pixel person. The pose follows the clock, the build follows your weight | [docs/pixel-figure.md](docs/pixel-figure.md) |
| Barbell animation | Between 14:00 and 16:00: frame B (bar at the belly) then frame A (bar overhead), 500 ms per frame, looping as one complete lift | [docs/pixel-figure.md](docs/pixel-figure.md) |
| Pixel clock | Time and date drawn in the Press Start 2P dot-matrix face | [docs/habit-panel.md](docs/habit-panel.md) |
| Tile polish | Tile plates sampled from the icon's edge colour, small artwork scaled up, app names always shown on the grid, Dock left icon-only | [docs/mitv-hyperos3.md](docs/mitv-hyperos3.md) |

![The two barbell frames](docs/images/lift-preview.png)

### 2. HyperOS 3 device adaption (record and scripts)

| Item | Notes |
| --- | --- |
| HOME whitelist workaround | CN firmware refuses to let `com.gathin.tvhome` take HOME; build with `-PlauncherApplicationId=com.ts.launcher` instead |
| Disable list | 24 telemetry / ad / preinstalled packages plus the system updater, with before-and-after package snapshots |
| Xiaomi App Store entry shell | `launcher/shortcut` (`com.local.shortcut`) puts a tile on the home screen for a store that has no LEANBACK entry |
| Live TV sources | 57 candidate URLs tried, 11 returned a playable list - [docs/live-sources.md](docs/live-sources.md) |
| Netflix compatibility | Verdict: this TV has no Widevine CDM, so Netflix neither installs nor works - [docs/netflix-compat-check.md](docs/netflix-compat-check.md) |
| Snapshots and restore scripts | [device/xiaomi-mitv-mftr0/](device/xiaomi-mitv-mftr0/) |

---

## Quick start (just want the launcher)

```bash
git clone <this repository> && cd cleanyourtv-mitv-hyperos3

# 1. Tell Gradle where your SDK is (use your own path)
echo "sdk.dir=C:/Path/To/android-sdk" > launcher/local.properties

# 2. Build (JDK 17 + Android SDK 34)
cd launcher
./gradlew assembleRelease                                           # standard package com.gathin.tvhome
./gradlew assembleRelease -PlauncherApplicationId=com.ts.launcher   # required on Xiaomi CN firmware

# 3. Install (enable ADB debugging on the TV first: Settings - Accounts & Security - ADB debugging)
adb connect <tv-ip>:5555
adb install -r app/build/outputs/apk/release/app-release.apk
```

> **On Xiaomi CN firmware:** the standard package name `com.gathin.tvhome` is not in the firmware's HOME whitelist. `set-home-activity` reports Success but nothing changes (FallbackHome takes over instead). Build with `-PlauncherApplicationId=com.ts.launcher` as above; the component is still `com.gathin.tvhome/.MainActivity`.

Then make it the default home:

```bash
adb shell cmd package set-home-activity com.ts.launcher/com.gathin.tvhome.MainActivity
```

---

## Remote control

| Where | Key | Effect |
| --- | --- | --- |
| Calendar | **Left twice** (within 800 ms) | Check in today; twice again to undo |
| Calendar | **Right** | Go to the weight page |
| Calendar | **Left once** | Nothing - deliberate, so a stray press cannot mark a day |
| Weight page | **Left** | Back to the calendar |
| Weight page | **Down** then **OK**, then up/down, then **OK** | Select the weight box, start editing, step by 0.1 kg, save |
| Any tile | **Up** | Focus returns to the habit panel |

Outside edit mode, up and down only navigate; they do **not** change the number.

---

## Layout

```
cleanyourtv-mitv-hyperos3/
├── launcher/                 launcher sources (all of upstream + this branch's changes)
│   ├── app/src/main/java/com/gathin/tvhome/
│   │   ├── HabitPanel.java      calendar + weight page (added here)
│   │   ├── HabitCalendar.java   check-in storage (added here)
│   │   ├── PixelBodyView.java   the pixel figure (added here)
│   │   └── MainActivity.java    wires up the panel, focus and fade rules (modified from upstream)
│   └── shortcut/              Xiaomi App Store entry shell, com.local.shortcut (added here)
├── device/xiaomi-mitv-mftr0/  HyperOS 3 work: disable list, snapshots, restore notes
├── docs/                      this branch's docs, plus upstream's own under docs/upstream/
├── tools/                     verification and mock-up scripts - see [docs/tools.md](docs/tools.md)
└── addons/ themes/ examples/ tests/   from upstream
```

Upstream files this branch modified: `MainActivity.java`, `AppAdapter.java`, `activity_main.xml`, `config.xml`, `strings.xml`, `item_app.xml`. Files added: `HabitPanel.java`, `HabitCalendar.java`, `PixelBodyView.java` and the `shortcut/` module.

---

## Configuration

All of it lives in `launcher/app/src/main/res/values/config.xml`:

| Key | Meaning |
| --- | --- |
| `habit_calendar` | Turns the calendar on or off |
| `habit_start` | First day of the challenge, e.g. `2026-10-18` |
| `habit_seed` | Backfilled days, comma-separated; how history gets in on a TV without root |
| `habit_weight_page` | Turns the weight page on or off |
| `habit_weight_steps` | The weight scale that splits the five builds, e.g. `80,77,74,71,68,65` |
| `habit_weight_seed` | Weight history as `2026-10-19=80.0,2026-10-21=79.2` |
| `habit_weight_step` | Editing step in kg, `0.1` by default |
| `dock_apps` | Package names shown on the Dock |

To change things without reinstalling, push a config such as `{"uniform_tiles":true,"tile_menu":true}` to
`/sdcard/Android/data/<package>/files/config.json`. See upstream [docs/modules.md](docs/modules.md) and the `themes/` folder.

---

## Documentation

- [docs/habit-panel.md](docs/habit-panel.md) - the calendar and weight page: interaction, storage, config, show/hide rules
- [docs/pixel-figure.md](docs/pixel-figure.md) - the pixel figure: pose schedule, barbell animation, how it is drawn
- [docs/mitv-hyperos3.md](docs/mitv-hyperos3.md) - HyperOS 3 porting notes and the traps found on the way
- [device/xiaomi-mitv-mftr0/](device/xiaomi-mitv-mftr0/) - device manual, disable list, snapshots
- [docs/live-sources.md](docs/live-sources.md) and [docs/netflix-compat-check.md](docs/netflix-compat-check.md) - two test reports
- [docs/tools.md](docs/tools.md) - what every script under `tools/` does, and how to point them at your TV
- [docs/upstream/](docs/upstream/) - upstream CleanYourTV's own documentation, kept as it is

---

## Credits and licence

- Upstream [CleanYourTV](https://github.com/Gathin/cleanyourtv), MIT (c) 2026 Gathin. Every upstream source file and document is kept here; everything this launcher can do is built on it.
- Press Start 2P font (SIL Open Font License 1.1), see `launcher/FONT-LICENSE-OFL.txt`.
- This branch's changes are released under MIT too - see [LICENSE](LICENSE) and [NOTICE](NOTICE.md).
- The device record comes from one physical Xiaomi TV (MiTV-MFTR0) with all identifiers redacted. **Check it against your own model before copying anything.**
