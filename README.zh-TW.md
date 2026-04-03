# EFCheck

[English README](./README.md)

EFCheck 是一個非官方、以 Windows 為主的 SKPORT 自動簽到工具，支援《明日方舟：終末地》與《明日方舟》。

它同時支援兩種使用方式：

- 原始碼模式：clone repo 後用 Python 執行
- 打包模式：使用 Windows onedir 或 onefile 發行包

EFCheck 會把瀏覽器 session 保存在本機，不適合公開分享。發布或打包前請先閱讀 [SECURITY.md](./SECURITY.md)。

## 功能

- 擷取並重用 Playwright 瀏覽器 profile
- 依序處理一個或多個已啟用的 SKPORT 簽到頁
- 以每個站點分開保存 local state 與重試 gate
- 可註冊 Windows 登入後自動執行的工作排程
- 提供統一 CLI 與相容的 batch wrapper
- 支援：
  - 可攜式 one-folder Windows 發行包
  - 單一 one-file Windows 執行檔，搭配外部 browser bootstrap

## 支援平台

- 主要支援 Windows
- 原始碼模式需要 Python 3.11+
- 實際簽到與 session capture 需要 Playwright Chromium

## 敏感資料

不要公開或分享以下資料：

- `state/`
- `logs/`
- 真實的 `config/settings.json`
- 任何 browser profile 目錄
- 任何 cookie、session、request dump

這些資料可能包含 cookies、local storage、access token 或其他登入憑證。

## 快速開始

### 原始碼模式

1. clone repo
2. 執行：

```bat
install_efcheck.bat
```

導引流程會：

- 在 `.venv` 安裝 Python 套件
- 初始化本機設定檔
- 可選擇是否加入 Arknights
- 可選擇 Arknights 是否共用 Endfield 的 browser profile
- 可選擇是否立即擷取 session
- 可選擇是否立即註冊 Windows logon task

### 打包模式

使用 onedir 或 onefile 發行包後，同樣執行：

```bat
install_efcheck.bat
```

在打包模式下，wrapper 會優先使用 `efcheck.exe`。

## 統一 CLI

套件入口：

```powershell
python -m efcheck --help
```

安裝後也可以：

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

`efcheck package ...` 只支援原始碼模式。已打包的 `efcheck.exe` 適合執行日常命令，不應再拿來重建 PyInstaller 發行物。

## 典型流程

### 1. 初始化設定

```powershell
python -m efcheck init
```

若 `settings.json` 不存在，這會建立一份預設設定。

### 2. 查看路徑

```powershell
python -m efcheck paths --json
```

設定檔路徑解析順序：

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

若也啟用了 Arknights：

```powershell
python -m efcheck capture-session --site arknights
```

### 4. 測試執行

```powershell
python -m efcheck run --dry-run --force
python -m efcheck run --force
```

### 5. 註冊 Windows logon task

```powershell
python -m efcheck register-task
```

相容 wrapper 仍可使用：

```bat
register_logon_task.bat
```

## 原始碼模式與打包模式

### 原始碼模式預設

- Config：`<repo>/config/settings.json`
- State：`<repo>/state/`
- Logs：`<repo>/logs/`
- 舊的 source-mode 設定仍可相容

### 打包模式預設

- Base dir：`%LOCALAPPDATA%\EFCheck`
- Config：`%LOCALAPPDATA%\EFCheck\config\settings.json`
- State：`%LOCALAPPDATA%\EFCheck\state\`
- Logs：`%LOCALAPPDATA%\EFCheck\logs\`
- Runtime：`%LOCALAPPDATA%\EFCheck\runtime\`
- Browser profiles：`%LOCALAPPDATA%\EFCheck\browser-profile\`

## Browser runtime

### 原始碼模式

你仍可使用標準 Playwright 安裝方式：

```powershell
playwright install chromium
```

`setup_windows.bat` 會改用：

```powershell
python -m efcheck doctor --install-browser
```

這是本專案支援的 browser bootstrap 方式。

### 打包模式

執行檔本身不會把完整 Chromium browser runtime 直接包進二進位檔。

請改用：

```powershell
efcheck doctor --install-browser
```

這會把 browser runtime 安裝到 EFCheck 的資料目錄下，例如 `runtime/playwright-browsers`。

## one-folder 與 one-file

### one-folder

- 穩定性較高
- 啟動較快
- 較容易除錯
- 建議一般使用者優先使用

### one-file

- 攜帶較方便
- 啟動較慢，因為 PyInstaller 會先解壓
- 仍需要額外 browser bootstrap
- 更適合當成便利 CLI，不是完全自帶瀏覽器的單檔 GUI 工具

## Batch wrappers

為了相容性與使用者體驗，以下 wrapper 仍保留：

- [`install_efcheck.bat`](./install_efcheck.bat)
- [`setup_windows.bat`](./setup_windows.bat)
- [`capture_session.bat`](./capture_session.bat)
- [`run_signin.bat`](./run_signin.bat)
- [`register_logon_task.bat`](./register_logon_task.bat)

它們會優先使用 `efcheck.exe`，否則 fallback 到 `python -m efcheck ...`。

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

舊 wrapper 仍可使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

## 疑難排解

- `Missing dependency: playwright ...`
  先安裝專案依賴，再做 browser bootstrap。
- `Missing file: Playwright Chromium is not installed ...`
  原始碼模式請執行 `playwright install chromium`；打包模式請執行
  `efcheck doctor --install-browser`。
- `Browser profile not found ...`
  先執行 `capture-session`。
- `SESSION_EXPIRED`
  重新擷取對應站點的 session。
- `Configuration error`
  檢查 `settings.json`，尤其是 booleans 與 integer 欄位。
- 排程沒有出現
  重新執行 `register-task`，並確認 UAC 提權流程有完成。

## 已知限制

- 本工具依賴 SKPORT 頁面結構與 request 模式，站點改版可能導致失效。
- Arknights 與 Endfield 的 attendance endpoint 不相同。
- onefile 模式仍依賴外部 Playwright browser install。
- session capture 必須手動完成登入。

## 支持這個專案

如果 EFCheck 對你有幫助，並且你想支持後續維護、測試與打包工作，可以在 Ko-fi 支持 MimiLab：

[在 Ko-fi 支持 EFCheck](https://ko-fi.com/mimilab)

贊助完全是自願的。EFCheck 仍然是一個由業餘時間維護的非官方個人工具。

## 開發文件

請參考：

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [docs/packaging.md](./docs/packaging.md)
- [docs/release.md](./docs/release.md)
- [docs/repo-metadata.md](./docs/repo-metadata.md)
- [CHANGELOG.md](./CHANGELOG.md)
