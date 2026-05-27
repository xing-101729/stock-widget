# 📈 台股即時行情桌面小工具

一個輕量級的桌面應用程式，即時顯示台股與美股的即時行情資訊。

## ✨ 功能特色

### 📊 即時行情顯示
- **即時更新**：每 30 秒自動更新股票資料
- **多股監控**：同時監控多支股票的即時行情
- **走勢圖**：顯示當日即時走勢圖（1分鐘/5分鐘線）

### 🌍 雙市場支援
- **台股 (TW)**：支援台股代碼查詢（如 2330 台積電）
- **美股 (US)**：支援美股代碼查詢（如 AAPL、TSLA）
- **一鍵切換**：點擊按鈕即可在台股/美股之間切換

### 📈 詳細資訊
| 欄位 | 說明 |
|------|------|
| 代碼 | 股票代號 |
| 名稱 | 股票名稱 |
| 現價 | 即時成交價 |
| 漲跌 | 較前日收盤漲跌點數 |
| 漲跌幅 | 漲跌百分比 |
| 盤前 | 盤前交易漲跌幅（僅美股） |
| 走勢 | 當日即時走勢迷你圖 |
| 成交量 | 當日成交量 |
| 漲跌停 | 漲跌停狀態（僅台股） |

### 🎨 使用者介面
- **深色主題**：護眼的深色介面設計
- **自適應視窗**：視窗大小自動適應內容
- **置頂顯示**：可設定視窗始終置於最上層
- **手動刷新**：支援手動立即更新資料

### 💾 資料持久化
- **自選股清單**：自動儲存至 `watchlist_tw.json` / `watchlist_us.json`
- **股票名稱快取**：自動儲存股票名稱至 `stock_names.json`
- **自動恢復**：下次開啟時自動載入上次的自選股清單

## 🚀 安裝與使用

### 環境需求
- Python 3.8+
- 作業系統：Windows 10/11

### 安裝依賴
```bash
pip install yfinance matplotlib certifi
```

### 執行程式
```bash
python stock_widget.py
```

### 打包為執行檔 (Windows)
使用 PyInstaller 打包成獨立的 `.exe` 檔案：
```bash
pyinstaller --onefile --windowed --collect-all certifi --hidden-import=yfinance stock_widget.py
```
打包完成後，執行檔位於 `dist/stock_widget.exe`

## 📖 使用說明

### 新增股票
1. 在輸入框中輸入股票代碼（如 `2330`）或名稱（如 `台積電`）
2. 按 Enter 或點擊「➕ 新增」按鈕
3. 股票將自動加入清單並開始監控

### 移除股票
- 點擊股票列右側的「❌」按鈕即可移除

### 切換市場
- 點擊頂部的「TW」或「US」按鈕即可切換台股/美股模式
- 不同市場有獨立的自選股清單

### 置頂視窗
- 點擊「📌」按鈕可切換視窗是否置於最上層

### 手動刷新
- 點擊「🔄」按鈕可立即更新所有股票資料

## 🏗️ 技術架構

### 核心技術
- **GUI 框架**：Tkinter（Python 內建）
- **資料來源**：Yahoo Finance API（透過 `yfinance`）
- **台股名稱查詢**：TWSE API（台灣證券交易所）
- **走勢圖繪製**：Matplotlib
- **多執行緒**：ThreadPoolExecutor 並行獲取多股資料

### 專案結構
```
stock-widget/
├── stock_widget.py      # 主程式
├── build.bat            # 打包腳本
├── build_exe.py         # 打包輔助腳本
├── .gitignore           # Git 忽略規則
├── watchlist_tw.json    # 台股自選股清單（自動生成）
├── watchlist_us.json    # 美股自選股清單（自動生成）
└── stock_names.json     # 股票名稱快取（自動生成）
```

## ⚙️ 進階設定

### 修改預設股票
編輯 `stock_widget.py` 中的 `DEFAULT_WATCHLIST_TW` 或 `DEFAULT_WATCHLIST_US`：
```python
DEFAULT_WATCHLIST_TW = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    # 新增你的預設股票...
}
```

### 修改更新頻率
修改 `REFRESH_INTERVAL` 變數（單位：秒）：
```python
REFRESH_INTERVAL = 30  # 預設 30 秒
```

## 📝 注意事項
- 首次執行時會稍微慢一點，因為需要載入相關模組
- 需要網路連線以獲取 Yahoo Finance 資料
- 台股漲跌停限制為 ±10%
- 美股無固定漲跌停限制，盤前資料僅在盤前時段有效

## 📄 授權
本專案僅供個人學習與使用。
