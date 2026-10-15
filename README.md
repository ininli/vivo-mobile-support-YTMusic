# 讓 vivo 原子隨身聽支援 YouTube Music / YouTube Music for vivo Origin Player

[中文](#中文) | [English](#english)

## 中文

vivo OriginOS 的「原子隨身聽」（Origin Player，套件 `com.vivo.musicwidgetmix`）只支援內建名單裡的音樂 App，YouTube Music 不在名單上，所以播放時不會出現在小工具、控制中心和鎖定畫面。

這個專案用 adb 把 YouTube Music 加進原子隨身聽的白名單，**不需要 root，也不用修改系統 App**。

### 測試環境

| 項目 | 版本 |
| --- | --- |
| 手機 | vivo V2359A |
| 系統 | OriginOS 6（Android 16） |
| 原子隨身聽 | 6.2.0.3 |

其他機型或版本的名單內容和判斷方式可能不同，請先用 `status` 確認。

### 原理

原子隨身聽啟動時，會讀取 `Settings.Secure` 裡的 `music_app_white_list`（一個 JSON 陣列）。這個值不存在時，就改用程式內建的名單。

adb shell 有權限寫入 secure settings，所以只要把「內建名單 + YouTube Music」寫進這個 key，原子隨身聽重啟後就會認得 YouTube Music。

名單裡的 App 分成兩種：

- **合作 App**（`isCooperate: 1`）：vivo 有專門的串接，例如 QQ 音樂、網易雲音樂。
- **一般 App**（`isCooperate: 0`）：透過 Android 標準的 MediaSession API 控制。YouTube Music 本來就有 MediaSession，所以歌名、封面、播放和暫停、上下首、拖曳進度都能用。

### 使用方式

需要：電腦已安裝 adb 和 Python 3，手機已開啟 USB 偵錯並連上電腦。

```bash
# 檢查目前狀態
python3 vivo_music_whitelist.py status

# 加入 YouTube Music（預設 com.google.android.apps.youtube.music）
python3 vivo_music_whitelist.py apply

# 加入其他 App，可以重複指定
python3 vivo_music_whitelist.py apply --package com.example.player

# 只印出要寫入的 JSON，不實際寫入
python3 vivo_music_whitelist.py apply --dry-run

# 還原
python3 vivo_music_whitelist.py restore
```

同時連著多支裝置時，在子指令前面加上 `--serial <序號>`。

`apply` 第一次執行時，會把原本的值存到目前目錄的 `music_app_white_list.backup.<序號>.json`，`restore` 會用它還原。如果手機原本就有這個 key（例如 vivo 透過雲端設定推送過），腳本會在原本的名單上增加，不會覆蓋掉。

#### 確認是否成功

1. 執行 `apply`。
2. 打開 YouTube Music 播一首歌。
3. 再執行 `status`，`Current music source` 應該顯示 YouTube Music 的套件名稱。
4. 下拉控制中心，或查看鎖定畫面，應該會出現原子隨身聽的播放卡片。

### 限制：原子島

原子島（狀態列上的動態膠囊）**無法**用這個方法加入。

原子島能顯示哪些 App，是另一份**寫死在程式碼裡**的名單，不讀取任何系統設定。原子隨身聽是用 vivo 平台金鑰簽章的系統 App，沒有 root 就無法修改。

唯一的方法是讓播放 App 的套件名稱剛好在那份名單裡。原子隨身聽 6.2.0.3 的原子島名單如下：

```
com.android.bbkmusic  com.tencent.qqmusic  com.kugou.android  com.netease.cloudmusic
cn.kuwo.player  cmccwm.mobilemusic  com.tencent.qqmusiclite  com.kugou.android.elder
com.kugou.android.lite  com.tencent.blackkey  com.luna.music  cn.wenyu.bodian
com.kugou.viper  com.ting.mp3.android  com.hiby.music  com.spotify.music
com.apple.android.music  com.xs.fm.lite  com.xs.fm  com.ximalaya.ting.android
com.dragon.read  bubei.tingshu  com.kmxs.reader  fm.qingting.qtradio
app.podcast.cosmos  com.baidu.netdisk  com.ximalaya.ting.lite  cn.missevan
com.yibasan.lizhifm  com.shinyv.cnr  com.audio.tingting  com.tencent.qqmusicpad
com.shuqi.controller  com.salt.music
```

這代表 YouTube Music 必須重新封裝成上面其中一個套件名稱。本專案不提供重新封裝的方法。如果你自己這樣做，有兩點要注意：

- **不要用 `com.spotify.music`**：原子隨身聽對 Spotify 有特殊處理，會關掉進度條拖曳。另外，冒用 Google Play 上真實存在的 App 名稱，但簽章對不上，可能會讓 Google 的服務判定為可疑，造成播放異常。
- **建議用不在 Google Play 上的名稱**，例如 `com.salt.music`。它在原子島名單裡、不會被當成合作 App，會走一般的 MediaSession 控制，實測原子島、播放控制和拖曳都正常。改用其他名稱之後，記得用 `apply --package <新名稱>` 把它也加進白名單（`com.salt.music` 本來就在內建名單裡）。

### 注意事項

- 系統更新、恢復原廠設定，或 vivo 推送新的雲端設定之後，這個值可能被覆蓋，重新執行 `apply` 即可。
- 這是非官方的方法，與 vivo 和 Google 無關，使用風險自負。
- 「vivo」「OriginOS」「YouTube Music」等名稱為各自所有者的商標。

## English

vivo's Origin Player (原子隨身聽, package `com.vivo.musicwidgetmix`) on OriginOS only supports the music apps on its built-in list. YouTube Music is not on that list, so its playback never shows up in the Origin Player widget, the control center or the lock screen.

This project adds YouTube Music to Origin Player's whitelist over adb. **No root is needed, and no system app is modified.**

### Tested on

| Item | Version |
| --- | --- |
| Phone | vivo V2359A |
| System | OriginOS 6 (Android 16) |
| Origin Player | 6.2.0.3 |

Other models or versions may use a different list or logic. Run `status` first to check.

### How it works

On startup, Origin Player reads `music_app_white_list` (a JSON array) from `Settings.Secure`. When that key is absent, it falls back to a list built into the app.

The adb shell user is allowed to write secure settings. Writing "built-in list + YouTube Music" to that key makes Origin Player recognize YouTube Music after a restart.

Apps on the list come in two kinds:

- **Cooperate apps** (`isCooperate: 1`) have dedicated vivo integrations, such as QQ Music and NetEase Cloud Music.
- **Regular apps** (`isCooperate: 0`) are controlled through Android's standard MediaSession API. YouTube Music already has a MediaSession, so title, artwork, play/pause, previous/next and seeking all work.

### Usage

Requirements: adb and Python 3 on your computer, USB debugging enabled on the phone, and the phone connected.

```bash
# Check the current state
python3 vivo_music_whitelist.py status

# Add YouTube Music (com.google.android.apps.youtube.music by default)
python3 vivo_music_whitelist.py apply

# Add other apps; --package can be repeated
python3 vivo_music_whitelist.py apply --package com.example.player

# Print the JSON without writing it
python3 vivo_music_whitelist.py apply --dry-run

# Undo
python3 vivo_music_whitelist.py restore
```

With several devices connected, put `--serial <serial>` before the subcommand.

The first `apply` saves the original value to `music_app_white_list.backup.<serial>.json` in the current directory, and `restore` uses that file. If the phone already has this key (for example, pushed by vivo's cloud config), the script adds to that list instead of replacing it.

#### Checking that it worked

1. Run `apply`.
2. Play a song in YouTube Music.
3. Run `status` again. `Current music source` should show YouTube Music's package name.
4. Pull down the control center or look at the lock screen. The Origin Player card should appear.

### Limitation: the Atom Island

The Atom Island (原子島, the dynamic capsule in the status bar) **cannot** be enabled this way.

The apps the island can show come from a separate list that is **hardcoded** in the app and does not read any setting. Origin Player is a system app signed with vivo's platform key, so it cannot be modified without root.

The only option is for the player's package name to be on that list. In Origin Player 6.2.0.3 the island list is:

```
com.android.bbkmusic  com.tencent.qqmusic  com.kugou.android  com.netease.cloudmusic
cn.kuwo.player  cmccwm.mobilemusic  com.tencent.qqmusiclite  com.kugou.android.elder
com.kugou.android.lite  com.tencent.blackkey  com.luna.music  cn.wenyu.bodian
com.kugou.viper  com.ting.mp3.android  com.hiby.music  com.spotify.music
com.apple.android.music  com.xs.fm.lite  com.xs.fm  com.ximalaya.ting.android
com.dragon.read  bubei.tingshu  com.kmxs.reader  fm.qingting.qtradio
app.podcast.cosmos  com.baidu.netdisk  com.ximalaya.ting.lite  cn.missevan
com.yibasan.lizhifm  com.shinyv.cnr  com.audio.tingting  com.tencent.qqmusicpad
com.shuqi.controller  com.salt.music
```

So YouTube Music would have to be repackaged under one of these names. This project does not cover how to repackage it. If you do it yourself, keep two things in mind:

- **Don't use `com.spotify.music`.** Origin Player special-cases Spotify and disables seek-bar dragging. Also, claiming the name of a real Google Play app with a mismatched signature may look suspicious to Google services and break playback.
- **Prefer a name that is not on Google Play**, such as `com.salt.music`. It is on the island list but is not a cooperate app, so it goes through regular MediaSession control. In testing, the island, playback controls and seeking all worked. If you pick another name, add it to the whitelist with `apply --package <name>` (`com.salt.music` is already on the built-in list).

### Notes

- A system update, a factory reset or a new cloud config from vivo may overwrite the value. Run `apply` again if that happens.
- This is unofficial and not affiliated with vivo or Google. Use at your own risk.
- "vivo", "OriginOS" and "YouTube Music" are trademarks of their respective owners.

## 授權 / License

MIT License，見 [LICENSE](LICENSE)。 / MIT License, see [LICENSE](LICENSE).
