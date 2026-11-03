"""Drive the TV over ADB for the habit-panel checks: reconnect before every command (the link drops
constantly), screenshot each step, and report whether the panel is on screen by counting its green
"day kept" squares.

    python tools/tv_check.py shot <name> [key ...]      press keys, then screenshot
    python tools/tv_check.py run                        the whole walk-through
"""
import os
import subprocess
import sys
import time

ADB = 'adb'
HOST = os.environ.get('TV_HOST', '<tv-ip>:5555')
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = (120, 228, 932, 642)          # the panel's patch of the 1920x1080 screen
KEYS = {'up': '19', 'down': '20', 'left': '21', 'right': '22', 'ok': '23'}


def adb(*args, tries=4):
    last = ''
    for _ in range(tries):
        subprocess.run([ADB, 'connect', HOST], capture_output=True)
        r = subprocess.run([ADB, *args], capture_output=True)
        last = (r.stdout + r.stderr).decode('utf-8', 'replace')
        if 'no devices' not in last and 'error' not in last.lower():
            return last.strip()
    return last.strip()


def shot(name):
    remote = f'/sdcard/{name}.png'
    adb('shell', 'screencap', '-p', remote)
    local = os.path.join(OUT, f'{name}.png')
    adb('pull', remote, local)
    return local


def press(key):
    adb('shell', 'input', 'keyevent', KEYS.get(key, key))


def green(path):
    sys.path.insert(0, os.path.join(OUT, 'tools'))
    from panel_visible import count_green
    return count_green(path, PANEL)


def focus():
    adb('shell', 'uiautomator', 'dump', '/sdcard/ck.xml')
    out = adb('shell', 'cat', '/sdcard/ck.xml')
    import re
    for m in re.finditer(r'<node[^>]*>', out):
        n = m.group(0)
        if 'focused="true"' in n:
            rid = re.search(r'resource-id="com.ts.launcher:id/([a-zA-Z_]+)"', n)
            b = re.search(r'bounds="([^"]+)"', n)
            return (rid.group(1) if rid else '?'), (b.group(1) if b else '')
    return None, None


def texts(ids):
    adb('shell', 'uiautomator', 'dump', '/sdcard/ck.xml')
    out = adb('shell', 'cat', '/sdcard/ck.xml')
    import re
    found = {}
    for m in re.finditer(r'<node[^>]*>', out):
        n = m.group(0)
        rid = re.search(r'resource-id="com.ts.launcher:id/([a-zA-Z_]+)"', n)
        if rid and rid.group(1) in ids:
            t = re.search(r'text="([^"]*)"', n)
            found[rid.group(1)] = t.group(1) if t else ''
    return found


if __name__ == '__main__':
    if sys.argv[1] == 'shot':
        for k in sys.argv[3:]:
            press(k)
            time.sleep(0.8)
        p = shot(sys.argv[2])
        print(f'{sys.argv[2]}: green={green(p)} focus={focus()}')
    else:
        adb('shell', 'input', 'keyevent', '224')     # wake
        adb('shell', 'am', 'force-stop', 'com.ts.launcher')
        adb('shell', 'monkey', '-p', 'com.ts.launcher', '-c', 'android.intent.category.HOME', '1')
        time.sleep(5)
        for name in ['r0-start', 'r1-down', 'r2-down', 'r3-down']:
            p = shot(name)
            print(f'{name}: green={green(p)} focus={focus()}')
            press('down')
            time.sleep(1.6)
