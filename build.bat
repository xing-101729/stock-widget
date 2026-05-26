@echo off
REM 台股行情小工具打包腳本
REM 安裝依賴
echo 正在安裝Python依賴套件...
pip install yfinance pyinstaller certifi matplotlib -q

REM 執行打包
echo 正在打包應用...
cd /d c:\Users\User\Desktop\tool
pyinstaller --onefile --windowed --collect-all certifi --hidden-import=yfinance --hidden-import=matplotlib stock_widget.py

echo.
echo ======================================
echo 打包完成！
echo 執行檔位置：dist\stock_widget.exe
echo ======================================
pause
