# Finance 股票研究工具

股票研究工具，兼具 LINE Bot 的功能。

## 環境需求

- Python >= 3.10
- uv (Python 套件管理工具)

## 安裝與設定

### 1. 安裝 uv

```bash
# Windows (使用 PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

### 2. Clone 專案並設定環境

```bash
# Clone 專案
git clone <專案網址>
cd Finance

# 建立虛擬環境並安裝依賴套件
uv sync
```

### 3. 啟動專案

```bash
# 啟動虛擬環境
uv shell

# 或直接執行
uv run python main.py
```

## 主要功能

- 即時股價查詢
- 股票技術指標分析
- LINE Bot 整合
- 金融數據分析

## 專案結構

- `main.py` - 主程式入口
- `Final/` - 完整版本程式碼
- `Homework/` - 作業檔案
- `pyproject.toml` - 專案配置與依賴套件
- `uv.lock` - 鎖定的套件版本

## 依賴套件

- flask>=3.0.0
- line-bot-sdk>=3.19.1
- pandas>=2.3.2
- pyngrok>=7.3.0
- requests>=2.32.5
