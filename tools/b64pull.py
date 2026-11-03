"""Fallback file transfer: read a file off the TV as base64 chunks through plain shell commands.

Same transport as b64push.py, reversed: each shell command cats one slice of the file through
`base64` and the script decodes and appends it locally. Only used for small pulls (icons, configs).
"""
import base64
import hashlib
import sys

sys.path.insert(0, '.')
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

CHUNK = 24 * 1024  # raw bytes per shell command; base64 of it must fit one output payload


def safe_local(p):
    return p.replace('\\', '_').replace('/', '_').replace(':', '_')


def q(p):
    return "'" + p.replace("'", "'\\''") + "'"


def load_signer():
    import os
    key = os.path.expanduser('~/.android/adbkey')
    if not os.path.exists(key):
        os.makedirs(os.path.dirname(key), exist_ok=True)
        keygen(key)
    with open(key) as f:
        priv = f.read()
    with open(key + '.pub') as f:
        pub = f.read()
    return PythonRSASigner(pub, priv)


def main():
    src, dst = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else safe_local(sys.argv[1]))
    host = __import__('os').environ.get('TV_HOST', '<tv-ip>')
    dev = AdbDeviceTcp(host, 5555)
    dev.connect(rsa_keys=[load_signer()], auth_timeout_s=30)

    size = int(dev.shell(f'stat -c %s {q(src)}').strip())
    md5 = dev.shell(f'md5sum {q(src)}').split()[0]
    print(f'{src}: {size} bytes, md5 {md5}')

    import time
    with open(dst, 'wb') as out:
        got = 0
        t0 = time.time()
        while got < size:
            end = min(got + CHUNK, size)
            raw = dev.shell(f'dd if={q(src)} bs={CHUNK} skip={got // CHUNK} count=1 2>/dev/null | base64')
            out.write(base64.b64decode(''.join(raw.split())))
            got = end
            if (got // CHUNK) % 50 == 0:
                print(f'  {got}/{size} ({time.time() - t0:.0f}s)', flush=True)
    check = hashlib.md5(open(dst, 'rb').read()).hexdigest()
    print(f'local md5 {check}: ' + ('OK' if check == md5 else f'MISMATCH (expected {md5})'))


if __name__ == '__main__':
    main()
