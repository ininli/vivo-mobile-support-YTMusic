# 參與貢獻 / Contributing

[中文](#中文) | [English](#english)

## 中文

謝謝你願意幫忙！這個專案很小，任何回報或修正都很有幫助。

### 回報問題

請用 [Issues](../../issues/new/choose) 的模板回報，並附上：

- 手機型號、OriginOS 版本
- 原子隨身聽版本：`adb shell dumpsys package com.vivo.musicwidgetmix | grep versionName`
- `python3 vivo_music_whitelist.py status` 的輸出
- 你做了什麼、預期的結果、實際的結果

不同機型和版本的白名單內容可能不一樣。如果你的手機能用（或不能用），也歡迎回報，我們可以把它加進 README 的測試環境表格。

### 發 PR

1. Fork 這個 repo，從 `main` 開一個新分支。
2. 修改後，至少在一支 vivo 手機上實際測過 `apply` 和 `restore`。
3. PR 說明請寫清楚測試的機型和版本。
4. 修改 README 時，請同時更新中文和英文兩段。

### 範圍

這個專案只處理「用 adb 修改原子隨身聽的白名單」。重新封裝或重新簽章其他 App 的方法不在範圍內，這類 PR 不會被合併。

### 注意

不要在 issue、PR 或 commit 裡貼出裝置序號、帳號資訊或任何金鑰。

## English

Thanks for helping out! This is a small project, so every report or fix counts.

### Reporting problems

Please use an [issue template](../../issues/new/choose) and include:

- Phone model and OriginOS version
- Origin Player version: `adb shell dumpsys package com.vivo.musicwidgetmix | grep versionName`
- Output of `python3 vivo_music_whitelist.py status`
- What you did, what you expected, and what actually happened

The whitelist can differ between models and versions. Reports that it works (or doesn't) on your phone are welcome too, so the tested devices table in the README can grow.

### Pull requests

1. Fork the repo and create a branch from `main`.
2. Test `apply` and `restore` on at least one real vivo phone.
3. In the PR description, list the models and versions you tested on.
4. When you change the README, update both the Chinese and the English sections.

### Scope

This project only covers editing Origin Player's whitelist over adb. Repackaging or re-signing other apps is out of scope, and PRs that add it will not be merged.

### Privacy

Don't post device serial numbers, account details or any keys in issues, PRs or commits.
