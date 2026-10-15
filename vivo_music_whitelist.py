#!/usr/bin/env python3
"""Add extra music apps to the vivo "Origin Player" (原子隨身聽) whitelist over adb.

Origin Player (com.vivo.musicwidgetmix) reads its supported-app list from
Settings.Secure "music_app_white_list" and falls back to a built-in list when
that key is absent. This tool writes that key: the built-in list plus the
packages you add. No root is needed, because the adb shell user may write
secure settings.

Usage:
    python3 vivo_music_whitelist.py status
    python3 vivo_music_whitelist.py apply [--package PKG ...] [--dry-run]
    python3 vivo_music_whitelist.py restore

Pass --serial SERIAL before the subcommand when more than one device is connected.
"""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

WIDGET_PACKAGE = "com.vivo.musicwidgetmix"
WHITELIST_KEY = "music_app_white_list"
# Origin Player derives these two keys from the whitelist on startup.
DERIVED_KEYS = ("resident_music_app_white_list", "lock_music_app_white_list")

DEFAULT_EXTRA_PACKAGES = ["com.google.android.apps.youtube.music"]

# Built-in lists of Origin Player 6.2.0.x, used when the key is absent.
BUILTIN_WHITELIST = """
com.android.bbkmusic com.tencent.qqmusic com.ximalaya.ting.android com.kugou.android
com.netease.cloudmusic bubei.tingshu cn.kuwo.player cmccwm.mobilemusic com.kugou.android.lite
com.kugou.android.elder app.podcast.cosmos fm.qingting.qtradio com.yibasan.lizhifm cn.missevan
com.luna.music com.hiby.music com.tencent.blackkey com.vivo.newsreader com.tencent.qqmusiclite
cn.wenyu.bodian com.tencent.weread com.ting.mp3.android com.xs.fm com.xs.fm.lite
com.ximalaya.ting.lite com.shinyv.cnr com.ormatch.android.asmr com.luojilab.player
com.kugou.android.tingshu com.tencent.radio com.audio.tingting com.spotify.music com.kugou.viper
com.baidu.netdisk com.vivo.agent com.vivo.base.agent com.apple.android.music com.dragon.read
com.kmxs.reader com.qidian.QDReader com.qq.reader com.jjwxc.reader com.jd.app.reader
bubei.tingshu.pro io.dushu.fandengreader com.larus.nova com.vivo.screenreader com.vivo.ai.gptagent
com.psyone.brainmusic com.ifeng.fhdt com.ximalaya.ting.kid com.vivo.ai.copilot com.qiyi.video
com.ss.android.ugc.aweme com.tencent.qqmusicpad tv.danmaku.bili com.shuqi.controller com.salt.music
com.tencent.mm
""".split()

# Apps Origin Player has dedicated integrations for ("cooperate" apps).
BUILTIN_COOPERATE = set("""
com.android.bbkmusic com.tencent.qqmusic com.ximalaya.ting.android com.kugou.android
com.netease.cloudmusic bubei.tingshu cn.kuwo.player cmccwm.mobilemusic com.kugou.android.lite
com.kugou.android.elder app.podcast.cosmos fm.qingting.qtradio com.yibasan.lizhifm com.luna.music
com.hiby.music com.tencent.blackkey com.xs.fm com.xs.fm.lite com.apple.android.music
com.spotify.music cn.missevan cn.wenyu.bodian
""".split())

# Apps shown on the lock screen card.
BUILTIN_LOCK_SCREEN = set("""
com.android.bbkmusic com.tencent.qqmusic com.ximalaya.ting.android com.kugou.android
com.netease.cloudmusic com.vivo.newsreader bubei.tingshu cn.kuwo.player cmccwm.mobilemusic
com.kugou.android.lite com.kugou.android.elder app.podcast.cosmos fm.qingting.qtradio
com.yibasan.lizhifm com.luna.music com.hiby.music com.tencent.blackkey com.vivo.agent
com.vivo.base.agent com.xs.fm com.xs.fm.lite com.apple.android.music com.spotify.music cn.missevan
com.vivo.screenreader com.vivo.ai.gptagent com.qiyi.video com.ss.android.ugc.aweme
com.tencent.qqmusicpad cn.wenyu.bodian com.kmxs.reader com.qidian.QDReader com.dragon.read
com.qq.reader io.dushu.fandengreader com.jjwxc.reader com.jd.app.reader bubei.tingshu.pro
com.luojilab.player com.kugou.android.tingshu tv.danmaku.bili com.shuqi.controller com.salt.music
com.kugou.viper com.tencent.weread com.shinyv.cnr com.tencent.mm
""".split())


def app_entry(package, app_name="", cooperate=False, lock_screen=True):
    return {
        "packageName": package,
        "appName": app_name,
        "isCooperate": 1 if cooperate else 0,
        "showLockScreen": 1 if lock_screen else 0,
        "dataStatus": 0,
    }


def builtin_entries():
    packages = list(BUILTIN_WHITELIST)
    for package in sorted(BUILTIN_COOPERATE | BUILTIN_LOCK_SCREEN):
        if package not in packages:
            packages.append(package)
    return [
        app_entry(p, cooperate=p in BUILTIN_COOPERATE, lock_screen=p in BUILTIN_LOCK_SCREEN)
        for p in packages
    ]


def build_whitelist(current_json, extra_packages):
    """Return the new whitelist: the current one (or the built-in list) plus extra packages."""
    entries = json.loads(current_json) if current_json else builtin_entries()
    known = {e.get("packageName") for e in entries}
    for package in extra_packages:
        if package not in known:
            # Not a cooperate app, so Origin Player controls it through the
            # standard MediaSession API.
            entries.append(app_entry(package, cooperate=False, lock_screen=True))
            known.add(package)
    return entries


class Adb:
    def __init__(self, serial=None):
        self.base = ["adb"] + (["-s", serial] if serial else [])

    def shell(self, command):
        result = subprocess.run(self.base + ["shell", command], capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"adb failed: {command}\n{result.stderr.strip()}")
        return result.stdout.strip()

    def get_secure(self, key):
        value = self.shell(f"settings get secure {key}")
        return None if value in ("", "null") else value

    def put_secure(self, key, value):
        self.shell(f"settings put secure {key} {shlex.quote(value)}")

    def delete_secure(self, key):
        self.shell(f"settings delete secure {key}")

    def restart_widget(self):
        self.shell(f"am force-stop {WIDGET_PACKAGE}")

    def serial(self):
        return self.shell("getprop ro.serialno") or "device"


def backup_path(adb):
    return Path(f"music_app_white_list.backup.{adb.serial()}.json")


def cmd_status(adb, _args):
    version = adb.shell(f"dumpsys package {WIDGET_PACKAGE} | grep -m1 versionName").strip()
    print(f"Origin Player: {version or 'not installed'}")
    current = adb.get_secure(WHITELIST_KEY)
    if current is None:
        print(f"{WHITELIST_KEY}: not set (the built-in list is in use)")
    else:
        entries = json.loads(current)
        print(f"{WHITELIST_KEY}: {len(entries)} apps")
    print(f"Current music source: {adb.get_secure('MusicWidgetMix_MusicSource')}")


def cmd_apply(adb, args):
    packages = args.package or DEFAULT_EXTRA_PACKAGES
    current = adb.get_secure(WHITELIST_KEY)
    entries = build_whitelist(current, packages)
    new_json = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
    if args.dry_run:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return

    backup = backup_path(adb)
    if not backup.exists():
        backup.write_text(json.dumps({WHITELIST_KEY: current}))
        print(f"Saved the original value to {backup}")

    adb.put_secure(WHITELIST_KEY, new_json)
    adb.restart_widget()
    print(f"Wrote {len(entries)} apps and restarted Origin Player. Added: {', '.join(packages)}")
    print("Start playback in the added app, then run 'status' to check the music source.")


def cmd_restore(adb, _args):
    backup = backup_path(adb)
    original = json.loads(backup.read_text()).get(WHITELIST_KEY) if backup.exists() else None
    if original:
        adb.put_secure(WHITELIST_KEY, original)
    else:
        adb.delete_secure(WHITELIST_KEY)
    for key in DERIVED_KEYS:
        adb.delete_secure(key)
    adb.restart_widget()
    if backup.exists():
        backup.unlink()
    print("Restored the original whitelist and restarted Origin Player.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--serial", help="adb device serial (when several devices are connected)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show the current whitelist state")
    apply_parser = sub.add_parser("apply", help="add packages to the whitelist")
    apply_parser.add_argument("--package", action="append",
                              help="package to add (repeatable); default: YouTube Music")
    apply_parser.add_argument("--dry-run", action="store_true", help="print the JSON without writing it")
    sub.add_parser("restore", help="undo 'apply'")
    args = parser.parse_args()

    adb = Adb(args.serial)
    {"status": cmd_status, "apply": cmd_apply, "restore": cmd_restore}[args.command](adb, args)


if __name__ == "__main__":
    main()
