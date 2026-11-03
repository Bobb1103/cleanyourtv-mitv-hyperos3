# shortcut: one-tile entries for apps the firmware hides

Some apps on this Xiaomi firmware are installed and enabled but carry no
`android.intent.category.LEANBACK_LAUNCHER` activity, so no third-party launcher can list them.
Xiaomi's own app store is one of them: `com.xiaomi.mitv.appstore/.MainActivity` declares only the
vendor's `android.intent.category.APPSTORE_LAUNCHER`. It is **not** disabled and nothing was removed
from the TV — the grid simply cannot see it.

This module ships one invisible activity (`com.local.shortcut/.AppStoreEntry`) with a Leanback
launcher entry whose `onCreate` forwards to the real component and finishes itself. The tile then
appears in the launcher's app grid and can be pinned to the dock like any other app.

Build and install from the repository root:

```bash
export JAVA_HOME=/path/to/jdk-17 ANDROID_HOME=/path/to/android-sdk
cd launcher && ./gradlew :shortcut:assembleRelease
TV_HOST=<tv ip> tools/venv/Scripts/python.exe -I tools/b64push.py \
  launcher/shortcut/build/outputs/apk/release/shortcut-release.apk /data/local/tmp/storeentry.apk
TV_HOST=<tv ip> tools/venv/Scripts/python.exe -I tools/tv.py \
  'pm install -r /data/local/tmp/storeentry.apk; rm -f /data/local/tmp/storeentry.apk'
```

Check it resolved to the real store:

```bash
TV_HOST=<tv ip> tools/venv/Scripts/python.exe -I tools/tv.py 'am start -n com.local.shortcut/.AppStoreEntry'
TV_HOST=<tv ip> tools/venv/Scripts/python.exe -I tools/tv.py 'dumpsys activity activities | grep topResumedActivity'
# expected: com.xiaomi.mitv.appstore/.MainActivity
```

Adding another hidden app later: add an activity here (manifest intent filter + a tiny forwarder
class), rebuild and reinstall. Uninstall with
`TV_HOST=<tv ip> tools/venv/Scripts/python.exe -I tools/tv.py 'pm uninstall com.local.shortcut'`.
