#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Put this repository on GitHub: create it if it is not there yet, then push.

The token is never passed on the command line and never written into .git/config.
It is read back out of the Git Credential Manager store - the credential that
`git-credential-manager github login` already saved - and handed to the one `git
push` process that needs it, through its environment.

Run it again at any time: an existing repository is reused, and an existing branch
is simply pushed to.

    python tools/gh_publish.py                     # public repository
    python tools/gh_publish.py --private           # private instead
    python tools/gh_publish.py --name other-name   # a different repository name
"""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args, **kwargs):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, **kwargs)


def git(*args, **kwargs):
    """Run git in this repository and return its stdout, or stop with its message."""
    p = run("git", *args, **kwargs)
    if p.returncode != 0:
        raise SystemExit("git %s failed:\n%s%s" % (" ".join(args), p.stdout, p.stderr))
    return p.stdout.strip()


def credential():
    """Where the token comes from: this process's environment first, the Git
    Credential Manager store second. Either way it never reaches .git/config."""
    env_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_token:
        return "", env_token
    if not run("git", "config", "--get", "credential.helper").stdout.strip():
        git("config", "--local", "credential.helper", "manager")
    p = run("git", "credential", "fill",
            input="protocol=https\nhost=github.com\n\n")
    found = {}
    for line in p.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            found[k] = v
    if p.returncode != 0 or not found.get("password"):
        raise SystemExit(
            "no GitHub credential in the store - sign in once with:\n"
            "  git-credential-manager github login\n" + (p.stderr or ""))
    return found.get("username") or "", found["password"]


def call(token, method, path, payload=None):
    """One API request, JSON in and out, with GitHub's own error text on failure."""
    body = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "cleanyourtv-publish",
    }
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"message": raw}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="cleanyourtv-mitv-hyperos3")
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--description", default=(
        "小米电视（澎湃 OS 3）上的 CleanYourTV 定制分支：减肥打卡桌面 + 像素小人 + "
        "澎湃 3.0 适配记录"))
    ap.add_argument("--topics",
                    default="android-tv,xiaomi,hyperos,launcher,habit-tracker,debloat")
    args = ap.parse_args()

    _, token = credential()
    code, me = call(token, "GET", "/user")
    if code != 200:
        raise SystemExit("the stored token was rejected (%s): %s"
                         % (code, me.get("message")))
    login = me["login"]
    print("signed in as", login)

    # A published commit shows its author, so the placeholder identity the history
    # was written with is replaced by this account. The noreply address keeps a real
    # mailbox out of the public history.
    email = "%s+%s@users.noreply.github.com" % (me.get("id", 0), login)
    git("config", "user.name", login)
    git("config", "user.email", email)
    git("commit", "--amend", "--no-edit", "--reset-author", "-q")
    print("commit author -> %s <%s>" % (login, email))

    full = "%s/%s" % (login, args.name)
    code, repo = call(token, "GET", "/repos/" + full)
    if code == 200:
        print("repository already there:", repo["html_url"])
    elif code == 404:
        code, repo = call(token, "POST", "/user/repos", {
            "name": args.name,
            "description": args.description,
            "homepage": "",
            "private": bool(args.private),
            "has_issues": True,
            "has_wiki": False,
            "has_projects": False,
        })
        if code not in (200, 201):
            raise SystemExit("cannot create the repository (%s): %s"
                             % (code, repo.get("message")))
        print("repository created:", repo["html_url"])
    else:
        raise SystemExit("cannot look up the repository (%s): %s"
                         % (code, repo.get("message")))

    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    if topics:
        code, res = call(token, "PUT", "/repos/%s/topics" % full, {"names": topics})
        print("topics:", ", ".join(topics) if code == 200
              else "rejected (%s) %s" % (code, res.get("message")))

    # main is the branch GitHub opens on; the history was written on master.
    git("branch", "-M", "main")
    if "origin" in git("remote").split():
        git("remote", "set-url", "origin", repo["clone_url"])
    else:
        git("remote", "add", "origin", repo["clone_url"])

    # The token reaches git through the environment of this single push, by way of a
    # one-line helper, so it stays out of .git/config, the reflog and the process list.
    helper = "!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f"
    env = dict(os.environ, GITHUB_TOKEN=token, GIT_TERMINAL_PROMPT="0")
    p = subprocess.run(["git", "-c", "credential.helper=",
                        "-c", "credential.helper=" + helper,
                        "push", "-u", "origin", "main"],
                       cwd=ROOT, env=env)
    if p.returncode != 0:
        raise SystemExit("push failed - see git's own message above")
    print("\ndone:", repo["html_url"])


if __name__ == "__main__":
    main()
