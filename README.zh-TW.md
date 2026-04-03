# EFCheck

[English README](./README.md)

EFCheck 是一個非官方、以 Windows 為主的 SKPORT 每日簽到自動化工具，目前支援：

- Arknights: Endfield
- Arknights

它同時支援兩種模式：

- 原始碼模式：clone repo 後用 Python 執行
- 打包模式：使用 Windows `onedir` 或 `onefile` 發行包

EFCheck 會把登入 session 保存在本機。請在分享任何工作區或發行包前，先閱讀 [SECURITY.md](./SECURITY.md)。

## 功能

- 以 Playwright 擷取並重用瀏覽器登入 profile
- 依序簽到一個或多個已啟用的 SKPORT 站點
- `settings.json` 永遠保留完整已知站點清單，並以 `enabled: true/false` 控制是否啟用
- 保留每站「當日已完成」狀態，避免同一天重複對已完成站點再跑一次
- 可註冊 Windows 登入時排程
- 提供統一 CLI 與相容的 batch wrapper
- 可打包成：
  - one-folder Windows 發行包
  - one-file Windows 可執行檔（仍需外部 browser bootstrap）

## 支援平台

- 主要支援 Windows
- 原始碼模式需要 Python 3.11+
- 實際簽到與 session capture 需要 Playwright Chromium

## 敏感資料

以下內容不要公開或分享：

- `state/`
- `logs/`
- 真實的 `config/settings.json`
- 任一 browser profile 目錄
- 任一 cookie / session dump

這些位置可能包含 cookies、local storage、access token 或其他登入材料。

## 快速開始

### 原始碼模式

1. clone repo
2. 執行：

```bat
install_efcheck.bat
```

引導式流程會：

- 在 `.venv` 安裝 Python 套件
- 初始化本機設定檔
- 詢問要啟用哪些已知站點
- 若 Endfield 與 Arknights 都啟用，再詢問是否共用瀏覽器 profile
- 視需要擷取已啟用站點的 session
- 視需要註冊 Windows 登入排程

### 打包模式

使用 `onedir` 或 `onefile` 發行包後，直接執行：

```bat
install_efcheck.bat
```

在打包模式下，wrapper 會優先使用 `efcheck.exe`。

## 統一 CLI

入口：

```powershell
python -m efcheck --help
```

安裝後也可直接用：

```powershell
efcheck --help
```

可用命令：

- `efcheck init`
- `efcheck run`
- `efcheck capture-session`
- `efcheck configure-sites`
- `efcheck register-task`
- `efcheck doctor`
- `efcheck paths`
- `efcheck package onedir`
- `efcheck package onefile`

`efcheck package ...` 只支援原始碼模式。打包後的 `efcheck.exe` 可執行日常操作命令，但不應拿來重新建 PyInstaller 產物。

## 站點設定模型

`settings.json` 會永遠保留完整已知站點清單。目前包含：

- `endfield`
- `arknights`

即使某站點停用，它也會留在設定檔內。可用下列方式切換：

```powershell
python -m efcheck configure-sites --enable-site endfield --disable-site arknights
python -m efcheck configure-sites --enable-site arknights --share-arknights-profile
```

目前的 daily gate 是「完成紀錄」模式：

- 若某站今天已達到 `SUCCESS` 或 `ALREADY_DONE`，之後同一天會直接略過
- 若某站今天曾失敗，EFCheck 允許再次執行

目前的有效設定與新寫入 state 檔，不再使用重試次數計數器。

## 典型流程

### 1. 初始化設定檔

```powershell
python -m efcheck init
```

這會在設定檔不存在時建立預設 `settings.json`。預設只啟用 Endfield，Arknights 會保留但設為停用。

### 2. 檢查實際路徑

```powershell
python -m efcheck paths --json
```

設定檔解析順序：

1. `--config`
2. `EFCHECK_CONFIG`
3. 打包模式預設：`%LOCALAPPDATA%\EFCheck\config\settings.json`
4. 原始碼模式預設：`<repo>\config\settings.json`

Base directory 解析順序：

1. `--base-dir`
2. `EFCHECK_BASE_DIR`
3. 打包模式預設：`%LOCALAPPDATA%\EFCheck`
4. 原始碼模式預設：repo 根目錄

### 3. 擷取 session

```powershell
python -m efcheck capture-session --site endfield
```

如果 Arknights 也有啟用：

```powershell
python -m efcheck capture-session --site arknights
```

### 4. 測試簽到

```powershell
python -m efcheck run --dry-run --force
python -m efcheck run --force
```

### 5. 註冊 Windows 登入排程

```powershell
python -m efcheck register-task
```

相容 wrapper 仍可使用：

```bat
register_logon_task.bat
```

## 原始碼模式 vs 打包模式

### 原始碼模式預設路徑

- Config：`<repo>/config/settings.json`
- State：`<repo>/state/`
- Logs：`<repo>/logs/`
- 舊的 source-mode 設定仍可相容讀取

### 打包模式預設路徑

- Base dir：`%LOCALAPPDATA%\EFCheck`
- Config：`%LOCALAPPDATA%\EFCheck\config\settings.json`
- State：`%LOCALAPPDATA%\EFCheck\state\`
- Logs：`%LOCALAPPDATA%\EFCheck\logs\`
- Runtime：`%LOCALAPPDATA%\EFCheck\runtime\`
- Browser profiles：`%LOCALAPPDATA%\EFCheck\browser-profile\`

## Browser runtime

### 原始碼模式

你仍可用標準 Playwright 安裝方式：

```powershell
playwright install chromium
```

`setup_windows.bat` 會改跑：

```powershell
python -m efcheck doctor --install-browser
```

這是本專案建議的 bootstrap 方式。

### 打包模式

可執行檔本身不會內嵌完整 Chromium browser runtime。

請先執行：

```powershell
efcheck doctor --install-browser
```

這會把 browser runtime 安裝到 `%LOCALAPPDATA%\EFCheck\runtime\playwright-browsers`。

## one-folder vs one-file

### one-folder

- 穩定性較高
- 啟動較快
- 較容易除錯
- 建議大多數使用者優先使用

### one-file

- 較方便攜帶
- 啟動較慢，因為 PyInstaller 會先解壓
- 仍需要外部 browser bootstrap
- 比較適合作為方便攜帶的 CLI，不是完整自含 browser payload

## Batch wrappers

以下 wrapper 會保留：

- [`install_efcheck.bat`](./install_efcheck.bat)
- [`setup_windows.bat`](./setup_windows.bat)
- [`capture_session.bat`](./capture_session.bat)
- [`run_signin.bat`](./run_signin.bat)
- [`register_logon_task.bat`](./register_logon_task.bat)

當 `efcheck.exe` 存在時，wrapper 會優先使用它；否則退回 `python -m efcheck ...`。

## 打包

### 建立 onedir

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_onedir.ps1
```

或在原始碼模式下：

```powershell
python -m efcheck package onedir
```

### 建立 onefile

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_onefile.ps1
```

或在原始碼模式下：

```powershell
python -m efcheck package onefile
```

### 建立 release zip

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\package_release.ps1
```

這會輸出：

- `EFCheck-Windows-onedir.zip`
- `EFCheck-Windows-onefile.zip`
- `EFCheck-SHA256.txt`

舊 wrapper 仍可用：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

## 疑難排解

- `Missing dependency: playwright ...`
  先安裝專案依賴，再執行 browser bootstrap。
- `Missing file: Playwright Chromium is not installed ...`
  原始碼模式請跑 `playwright install chromium`；打包模式請跑 `efcheck doctor --install-browser`。
- `Browser profile not found ...`
  先執行 `capture-session`。
- `SESSION_EXPIRED`
  重新擷取該站點的 session。
- `Configuration error`
  檢查 `settings.json`，尤其是 booleans、integers 和 site key。
- 排程看不到
  重新執行 `register-task`，並允許 UAC 提權。

## 已知限制

- 本工具依賴 SKPORT 頁面結構與 request 模式；網站改版後可能失效。
- Arknights 與 Endfield 的 attendance endpoint 形狀不同。
- onefile 仍依賴外部 Playwright browser 安裝。
- session capture 必須手動登入，無法完全自動化。

## 支援這個專案

如果 EFCheck 有幫你省下時間，想支持後續維護、測試與打包工作，可以透過 Ko-fi 支持 MimiLab：

[在 Ko-fi 支持 EFCheck](https://ko-fi.com/mimilab)

支持完全自願。EFCheck 仍然是一個非官方、以個人使用為主的自動化工具。

## 開發文件

請參考：

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [docs/packaging.md](./docs/packaging.md)
- [docs/release.md](./docs/release.md)
- [docs/repo-metadata.md](./docs/repo-metadata.md)
- [CHANGELOG.md](./CHANGELOG.md)
