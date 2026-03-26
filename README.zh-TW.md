# EFCheck

[English README](./README.md)

EFCheck 是一個以 Windows 為主的 Arknights: Endfield SKPORT 每日簽到輔助工具。

它使用專用的 Playwright 瀏覽器設定檔，將登入 session 保存在本機資料夾中，以 headless 模式執行，並可在 Windows 登入後自動觸發。

## 特色

- 使用專用本機 profile 的 headless 瀏覽器簽到
- 預設每天最多 2 次嘗試
- 一旦結果是 `SUCCESS` 或 `ALREADY_DONE` 就停止重試
- 偵測到登入 session 可能失效時，會顯示 Windows 桌面通知
- 提供安裝、擷取 session、手動執行的批次檔
- 提供延遲啟動的工作排程 PowerShell 腳本
- 透過 `.gitignore` 預設排除本機執行資料

## 需求

- Windows
- Python 3.11 以上
- Google Chrome 或 Playwright 管理的 Chromium

## 快速開始

1. 安裝依賴與瀏覽器執行環境：

```bat
setup_windows.bat
```

2. 先擷取一次登入 session：

```bat
capture_session.bat
```

3. 在開啟的瀏覽器中完成登入，並確認畫面已進入 Endfield 簽到頁。

4. 回到終端機，按 Enter 儲存 session。

5. 先手動測試一次：

```bat
run_signin.bat
```

## 排程

請用系統管理員權限開啟 PowerShell，然後註冊 Windows 工作排程：

```powershell
powershell -ExecutionPolicy Bypass -File .\register_logon_task.ps1
```

這個腳本會在登入後先延遲一小段時間，再執行簽到命令。

## 設定

只有在你想覆蓋預設值時，才需要建立本機設定檔：

```powershell
copy config\settings.example.json config\settings.json
```

主要設定如下：

- `timezone`：每日重試次數的日期判定時區
- `browser_profile_dir`：專用瀏覽器 profile 的本機路徑
- `browser_channel`：留空時使用 Playwright 管理的 Chromium
- `headless`：是否以無視窗模式執行
- `timeout_seconds`：頁面與網路等待逾時秒數
- `max_attempts_per_day`：預設為 `2`

## 執行邏輯

- 當天第一次成功後就不再重試
- 如果結果是 `ALREADY_DONE`，也不再重試
- 若失敗或 session 過期，當天還可再使用第二次嘗試
- 如果判斷 session 可能失效，EFCheck 會顯示 Windows 桌面通知

## 內含腳本

- [`sign_in.py`](./sign_in.py)：主簽到程式
- [`capture_session.py`](./capture_session.py)：一次性登入與 session 擷取
- [`setup_windows.bat`](./setup_windows.bat)：Windows 一鍵安裝
- [`capture_session.bat`](./capture_session.bat)：一鍵擷取 session
- [`run_signin.bat`](./run_signin.bat)：一鍵手動執行
- [`register_logon_task.ps1`](./register_logon_task.ps1)：工作排程註冊腳本
- [`package_windows_release.ps1`](./package_windows_release.ps1)：產出 Windows zip 發佈包
- [`config/settings.example.json`](./config/settings.example.json)：範例設定檔

## 打包 Windows 發佈版

可以用下面指令建立 zip 發佈包：

```powershell
powershell -ExecutionPolicy Bypass -File .\package_windows_release.ps1
```

輸出會建立在 `dist/`。

## 注意事項

- 請不要公開你的 `state/`、`logs/` 或真實的 `config/settings.json`
- 如果登入 session 失效，重新執行 `capture_session.bat` 即可
- 網站結構或政策未來可能變動
- `tests/` 資料夾是刻意保留在版本控制中的，用來記錄預期行為並避免回歸
- 本專案為非官方工具，與 Hypergryph、SKPORT 無隸屬關係
