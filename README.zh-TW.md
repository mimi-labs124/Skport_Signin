# EFCheck

[English README](./README.md)

EFCheck 是一個以 Windows 為主的 SKPORT 每日簽到工具，支援《明日方舟：終末地》與《明日方舟》。

它使用獨立的 Playwright 瀏覽器 profile，把登入 session 保存在本機資料夾中，平常以 headless 方式執行，也可以在 Windows 登入後自動背景觸發。

## 功能

- 使用本機瀏覽器 profile 的 headless 自動簽到
- 預設每天最多嘗試 2 次
- 一旦出現 `SUCCESS` 或 `ALREADY_DONE` 就停止重試
- 偵測到 session 失效時顯示 Windows 桌面通知
- 提供安裝、擷取 session、手動執行與註冊排程的批次檔
- 單次執行可依序處理 Endfield 與 Arknights

## 需求

- Windows
- Python 3.11 以上
- Google Chrome，或 Playwright 自帶的 Chromium

## 快速開始

1. 執行引導式安裝：

```bat
install_efcheck.bat
```

這個流程會：

- 安裝 Python 依賴與 Playwright runtime
- 詢問是否加入 Arknights
- 若加入 Arknights，詢問是否與 Endfield 共用 browser profile
- 詢問是否立即擷取 session
- 詢問是否立即註冊 Windows 登入排程

如果你偏好手動流程，可以先執行 `setup_windows.bat`。如果是從舊版本升級，也建議再跑一次，確保 `tzdata` 已安裝。

2. 依提示完成一次 session 擷取。

若你選擇立即擷取：

- 會先開啟 Endfield 簽到頁
- 如果安裝時加入 Arknights，之後會再開一次 Arknights 簽到頁
- 如果兩者共用 profile，第二次通常不需要重新登入，只要確認頁面正常載入後按 Enter 即可

3. 手動測一次：

```bat
run_signin.bat
```

## 排程

註冊 Windows 登入排程：

```powershell
register_logon_task.bat
```

如果目前不是系統管理員，包裝器會自動重新以提升權限啟動，並要求 UAC 同意。

排程本身會：

- 使用 Task Scheduler 的延遲機制，而不是在 PowerShell 內 `Start-Sleep`
- 以隱藏的 PowerShell 視窗直接啟動 `sign_in.py`
- 不透過 `run_signin.bat`

`run_signin.bat` 保留為手動執行用的 helper。

## 設定

只有在你要覆寫預設值時，才需要自己建立本機設定檔：

```powershell
copy config\settings.example.json config\settings.json
```

主要設定：

- `timezone`：每日重試的日期邊界
- `browser_channel`：留空時使用 Playwright 管理的 Chromium
- `headless`：是否使用無視窗瀏覽器
- `timeout_seconds`：頁面與網路等待時間
- `max_attempts_per_day`：預設為 `2`
- `sites`：單次執行時要處理的站點清單

每個 site 項目支援：

- `key`：`capture_session.py --site` 使用的識別值
- `name`：log 與終端輸出顯示名稱
- `enabled`：是否啟用
- `signin_url`：簽到頁網址
- `attendance_path`：用來辨識 attendance API 的路徑
- `state_path`：該站點自己的每日 gate 狀態檔
- `browser_profile_dir`：browser profile 路徑；相同代表共用 session，不同代表分開 session

如果你要手動加入 Arknights 並共用 Endfield 的登入 session，可以加上：

```json
{
  "key": "arknights",
  "name": "Arknights",
  "enabled": true,
  "signin_url": "https://game.skport.com/arknights/sign-in",
  "attendance_path": "/api/v1/game/attendance",
  "state_path": "../state/arknights-last_run.json",
  "browser_profile_dir": "../state/browser-profile"
}
```

如果要分開 session，只需要把 `browser_profile_dir` 換成另一個資料夾，例如 `../state/arknights-browser-profile`。

## 執行行為

- 每個啟用站點都使用自己的 `state_path`
- 同一次執行會依序處理所有啟用站點
- 某站點成功或已簽到，不會影響另一個站點的當日 gate
- session 過期時會嘗試顯示 Windows 桌面通知

## 多站點說明

- 舊版單站設定仍可用，會被視為僅有 Endfield
- `capture_session.py` 預設是 `--site endfield`
- 引導式安裝現在可直接加入 Arknights，並設定是否共用 profile
- 依照實際頁面檢查，目前 Arknights 使用：
  - GET `https://zonai.skport.com/api/v1/game/attendance?gameId=1&uid=...`
  - POST `https://zonai.skport.com/api/v1/game/attendance`
- 因此 Arknights 預設 `attendance_path` 應為 `/api/v1/game/attendance`
- 如果 SKPORT 未來改了 endpoint 或 DOM 流程，就要更新 `attendance_path` 並重新實測

## 內含腳本

- [`sign_in.py`](./sign_in.py)：主簽到程式
- [`capture_session.py`](./capture_session.py)：擷取登入 session（支援 `--site`）
- [`install_efcheck.bat`](./install_efcheck.bat)：引導式安裝入口
- [`setup_windows.bat`](./setup_windows.bat)：安裝依賴與 Chromium runtime
- [`capture_session.bat`](./capture_session.bat)：手動擷取 session
- [`run_signin.bat`](./run_signin.bat)：手動執行 helper
- [`register_logon_task.bat`](./register_logon_task.bat)：註冊排程的包裝器
- [`register_logon_task.ps1`](./register_logon_task.ps1)：建立隱藏 PowerShell 的登入排程
- [`tools/package_windows_release.ps1`](./tools/package_windows_release.ps1)：打包 Windows release zip
- [`config/settings.example.json`](./config/settings.example.json)：範例設定檔

## 打包 Windows 發行版

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

輸出 zip 會放在 `dist/`。

## 注意事項

- `state/`、`logs/`、真實的 `config/settings.json`、`state/browser-profile/` 都是私有資料，不要上傳
- 如果登入 session 失效，重新執行 `capture_session.bat`
- 目標網站的結構與政策可能改變
- `tests/` 目錄刻意保留在 repo 中，用來固定行為與避免回歸
- 發布或分享前請先看 [`SECURITY.md`](./SECURITY.md)
- 本專案為非官方工具，與 Hypergryph、GRYPHLINE、SKPORT 均無隸屬關係
