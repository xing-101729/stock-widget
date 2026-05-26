#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
台股行情小工具 - 自動打包腳本
直接執行此檔案: python build_exe.py
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """執行命令並顯示進度"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False, text=True)
        print(f"✅ {description} 成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗")
        print(f"錯誤: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 台股即時行情桌面小工具 - EXE 打包器")
    print("="*60)
    
    # 變更工作目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目錄: {script_dir}")
    
    # 步驟 1: 安裝依賴
    print("\n📋 步驟 1/3: 檢查並安裝 Python 依賴...")
    if not run_command(
        f"{sys.executable} -m pip install yfinance pyinstaller certifi matplotlib -q",
        "安裝依賴套件"
    ):
        print("❌ 依賴安裝失敗，請檢查網路連線")
        return False
    
    # 步驟 2: 驗證源代碼
    print("\n📋 步驟 2/3: 驗證源代碼...")
    if not os.path.exists("stock_widget.py"):
        print("❌ 找不到 stock_widget.py 檔案")
        return False
    print("✅ stock_widget.py 存在")
    
    # 步驟 3: 執行打包
    print("\n📋 步驟 3/3: 打包成 EXE...")
    pyinstaller_cmd = (
        f"{sys.executable} -m PyInstaller --onefile --windowed "
        f"--collect-all certifi "
        f"--hidden-import=yfinance stock_widget.py"
    )
    
    if not run_command(pyinstaller_cmd, "PyInstaller 打包"):
        print("❌ 打包失敗")
        return False
    
    # 驗證生成的 EXE
    print("\n" + "="*60)
    print("🎉 打包完成！")
    print("="*60)
    
    exe_path = os.path.join(script_dir, "dist", "stock_widget.exe")
    if os.path.exists(exe_path):
        exe_size = os.path.getsize(exe_path) / (1024 * 1024)  # 轉為 MB
        print(f"\n✅ 執行檔已成功生成！")
        print(f"📍 位置: {exe_path}")
        print(f"📊 大小: {exe_size:.1f} MB")
        print(f"\n💡 你可以：")
        print(f"   1. 直接雙擊執行 stock_widget.exe")
        print(f"   2. 複製到桌面或其他位置")
        print(f"   3. 創建快捷方式")
        print(f"   4. 分享給其他人使用")
        print(f"\n💾 自選股清單會自動存在 exe 旁邊的 watchlist.json")
        return True
    else:
        print(f"\n❌ 找不到生成的 EXE 檔案: {exe_path}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "="*60)
    if success:
        print("✨ 祝你使用愉快！")
    else:
        print("⚠️  請檢查上述錯誤訊息")
    print("="*60 + "\n")
    sys.exit(0 if success else 1)
