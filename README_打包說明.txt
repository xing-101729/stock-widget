📦 台股即時行情桌面小工具 - 完整打包指南
===============================================

✅ 第一步：已為你建立好檔案

以下檔案已存放在：c:\Users\User\Desktop\tool\

1️⃣  stock_widget.py  - 應用程式源代碼（已建立）
2️⃣  build.bat        - 自動打包腳本（已建立）

📋 第二步：手動執行打包 (3 種方法選一)

方法 A - 使用現成的 build.bat (最簡單) ⭐ 推薦
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 打開檔案瀏覽器，進入 c:\Users\User\Desktop\tool\
2. 雙擊 build.bat 檔案
3. 等待打包完成（約 2-5 分鐘，視電腦效能而定）
4. 打包完成後會自動在該資料夾生成 dist\ 資料夾
5. 進入 dist\ 資料夾，找到 stock_widget.exe，這就是你的執行檔！

方法 B - 使用 CMD 手動執行
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 按 Win + R，輸入 cmd 按 Enter
2. 貼上以下整行指令並按 Enter：

cd /d c:\Users\User\Desktop\tool && pip install yfinance pyinstaller certifi -q && pyinstaller --onefile --windowed --collect-all certifi --hidden-import=yfinance stock_widget.py

3. 等待完成，你會看到 "completed successfully" 的訊息
4. 進入 dist\ 資料夾找 stock_widget.exe

方法 C - 使用 PowerShell
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 按 Win + X，選擇 "Windows PowerShell (管理員)"
2. 貼上以下指令並按 Enter：

cd /d c:\Users\User\Desktop\tool && pip install yfinance pyinstaller certifi -q && pyinstaller --onefile --windowed --collect-all certifi --hidden-import=yfinance stock_widget.py

3. 等待完成
4. 進入 dist\ 資料夾找 stock_widget.exe

📌 打包完成後會生成的檔案結構
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
c:\Users\User\Desktop\tool\
├── stock_widget.py          (源代碼)
├── build.bat               (打包腳本)
├── stock_widget.spec       (打包配置 - 自動生成)
├── build\                  (編譯臨時文件 - 自動生成)
└── dist\                   (最終輸出 - 自動生成)
    └── stock_widget.exe    🎯 ← 你要的執行檔就在這裡！

✨ 執行 stock_widget.exe 時的提示
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 第一次執行會稍微慢一點（3-5 秒），因為要解壓縮和載入台股資料庫
✓ 之後每次開啟都會很快
✓ 自選股清單會自動存在 stock_widget.exe 旁邊的 watchlist.json
✓ 下次開啟時會自動恢復上次的清單
✓ 如果防毒軟體警告，請將其加入白名單（這是正常的新 exe 檔案行為）

🎯 最終結果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你可以：
1. ✅ 直接執行 stock_widget.exe
2. ✅ 把 stock_widget.exe 複製到桌面或任何地方
3. ✅ 創建快捷方式釘選到工作列
4. ✅ 分享給別人使用（不需要安裝 Python）

🆘 遇到問題？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 找不到 Python：
→ 請確認已安裝 Python 3.8+ (可到 python.org 下載)
→ 安裝時記得勾選 "Add Python to PATH"

❌ pip 指令無法執行：
→ 試試 python -m pip install ...

❌ 防毒軟體攔截 exe：
→ 這是正常的，將檔案加入白名單即可

❌ 無法連到 Yahoo Finance：
→ 檢查網路連線
→ 確認防火牆沒有阻止

有任何問題歡迎提問！
