#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
台股即時行情桌面小工具 (v4 - 防止美股降級)
=========================================
依賴：pip install yfinance pyinstaller certifi
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.parse
# matplotlib 延後 import，避免啟動時大量延遲
# (改為在 _draw_intraday_chart 中使用 lazy import)

# ============================================================
# ⚙️ 打包與路徑相容性設定 (PyInstaller 專用)
# ============================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    try:
        import certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()
    except ImportError:
        pass
else:
    BASE_DIR = os.path.abspath(".")

WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
STOCK_NAMES_FILE = os.path.join(BASE_DIR, "stock_names.json")

DEFAULT_WATCHLIST = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2382.TW": "廣達",
    "00878.TW": "國泰永續高股息",
}

# 基本股票名稱映射表
DEFAULT_STOCK_NAMES = {
    "2330": "台積電",
    "2317": "鴻海",
    "2382": "廣達",
    "2454": "聯發科",
    "2327": "國巨",
    "00878": "國泰永續高股息",
    "0050": "元大台灣50",
}

REFRESH_INTERVAL = 30
# ============================================================

class StockWidget:
    COLOR_UP = "#FF4444"
    COLOR_DOWN = "#00CC66"
    COLOR_FLAT = "#CCCCCC"
    COLOR_BG = "#1A1A2E"
    COLOR_BG_ROW1 = "#16213E"
    COLOR_BG_ROW2 = "#0F3460"
    COLOR_HEADER = "#533483"
    COLOR_TEXT = "#E0E0E0"
    COLOR_DIM = "#888888"

    def __init__(self, root):
        self.root = root
        self.root.title("台股即時行情")
        self.root.configure(bg=self.COLOR_BG)
        self.root.attributes('-topmost', True)
        self.lock = threading.Lock()
        self.is_running = True
        self.topmost = True
        self.row_widgets = {}
        self.last_data = {}

        self.watchlist = self._load_watchlist()
        self.stock_names = self._load_stock_names()

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self._build_ui()
        # 延後啟動更新迴圈，先讓 UI 完成繪製以避免啟動緩慢
        self.root.after(150, self._start_refresh_loop)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._update_window_size()
        # 靠左顯示（改為 +10 而非 screen_w - 660）
        self.root.geometry(f"+10+40")

    def _load_watchlist(self):
        if os.path.exists(WATCHLIST_FILE):
            try:
                with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_WATCHLIST.copy()

    def _save_watchlist(self):
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.watchlist, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        top = tk.Frame(self.root, bg=self.COLOR_HEADER, height=44)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        tk.Label(top, text="📈 台股即時行情", font=("Microsoft JhengHei UI", 12, "bold"),
                 fg="white", bg=self.COLOR_HEADER).pack(side=tk.LEFT, padx=12, pady=8)

        self.status_lbl = tk.Label(top, text="⏳ 載入中...", font=("Microsoft JhengHei UI", 8),
                                   fg="#BBBBBB", bg=self.COLOR_HEADER)
        self.status_lbl.pack(side=tk.RIGHT, padx=8)

        self.pin_btn = tk.Button(top, text="📌", font=("Segoe UI Emoji", 11), bg=self.COLOR_HEADER,
                                 fg="white", bd=0, activebackground=self.COLOR_HEADER,
                                 cursor="hand2", command=self._toggle_pin)
        self.pin_btn.pack(side=tk.RIGHT, padx=4)

        tk.Button(top, text="🔄", font=("Segoe UI Emoji", 11), bg=self.COLOR_HEADER, fg="white",
                  bd=0, activebackground=self.COLOR_HEADER, cursor="hand2",
                  command=self._manual_refresh).pack(side=tk.RIGHT, padx=4)

        add_frame = tk.Frame(self.root, bg=self.COLOR_BG, height=40)
        add_frame.pack(fill=tk.X, padx=10, pady=6)
        
        tk.Label(add_frame, text="新增股票:", bg=self.COLOR_BG, fg=self.COLOR_TEXT,
                 font=("Microsoft JhengHei UI", 9)).pack(side=tk.LEFT, padx=(0, 6))
        
        self.entry = tk.Entry(add_frame, width=16, font=("Microsoft JhengHei UI", 10),
                              bg="#2A2A40", fg="white", insertbackground="white",
                              relief=tk.FLAT, bd=4)
        self.entry.pack(side=tk.LEFT, padx=(0, 6))
        self.entry.bind('<Return>', lambda e: self._add_stock())

        tk.Button(add_frame, text="➕ 新增", font=("Microsoft JhengHei UI", 9, "bold"),
                  bg="#007BFF", fg="white", activebackground="#0056b3", bd=0, padx=10, pady=2,
                  cursor="hand2", command=self._add_stock).pack(side=tk.LEFT)
        
        tk.Label(add_frame, text="(可輸入代碼如 2330 或名稱如 台積電)", bg=self.COLOR_BG,
                 fg=self.COLOR_DIM, font=("Microsoft JhengHei UI", 8)).pack(side=tk.LEFT, padx=8)

        hdr = tk.Frame(self.root, bg=self.COLOR_BG)
        hdr.pack(fill=tk.X, padx=6, pady=(2, 0))

        # 欄位寬度，與下方列對齊（以字元寬度為基準）
        columns = [("代碼", 5), ("名稱", 8), ("現價", 8), ("漲跌", 7), ("漲跌幅", 7), ("走勢", 17), ("成交量", 7), ("漲跌停", 6), ("", 3)]
        for i, (text, width) in enumerate(columns):
            tk.Label(hdr, text=text, width=width, anchor="w",
                     font=("Microsoft JhengHei UI", 9, "bold"),
                     fg=self.COLOR_DIM, bg=self.COLOR_BG).grid(row=0, column=i, padx=2, sticky="w")

        # 讓 header 的每一列有固定最小像素（微調對齊）
        hdr.grid_columnconfigure(0, minsize=40)
        hdr.grid_columnconfigure(1, minsize=110)
        hdr.grid_columnconfigure(2, minsize=70)
        hdr.grid_columnconfigure(3, minsize=60)
        hdr.grid_columnconfigure(4, minsize=60)
        hdr.grid_columnconfigure(5, minsize=140)
        hdr.grid_columnconfigure(6, minsize=70)
        hdr.grid_columnconfigure(7, minsize=70)
        hdr.grid_columnconfigure(8, minsize=30)

        self.rows_frame = tk.Frame(self.root, bg=self.COLOR_BG)
        self.rows_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        for code, name in self.watchlist.items():
            self._create_row(code, name)

    def _create_row(self, code, name):
        idx = list(self.watchlist.keys()).index(code)
        bg = self.COLOR_BG_ROW1 if idx % 2 == 0 else self.COLOR_BG_ROW2
        row = tk.Frame(self.rows_frame, bg=bg)
        row.pack(fill=tk.X, pady=1, ipady=2)

        code_short = code.split(".")[0]
        w = {"_frame": row}

        # 第一行：基本資料
        main_frame = tk.Frame(row, bg=bg)
        main_frame.pack(fill=tk.X, side=tk.LEFT)

        w["code"] = tk.Label(main_frame, text=code_short, width=6, anchor="w",
                             font=("Consolas", 10, "bold"), fg=self.COLOR_TEXT, bg=bg)
        w["code"].pack(side=tk.LEFT, padx=2)

        w["name"] = tk.Label(main_frame, text=name, width=10, anchor="w",
                             font=("Microsoft JhengHei UI", 10), fg=self.COLOR_TEXT, bg=bg)
        w["name"].pack(side=tk.LEFT, padx=2)

        for key, width, ft in [
            ("price", 8, ("Consolas", 11, "bold")),
            ("change", 7, ("Consolas", 10)),
            ("pct", 7, ("Consolas", 10)),
        ]:
            w[key] = tk.Label(main_frame, text="--", width=width, anchor="w",
                              font=ft, fg=self.COLOR_DIM, bg=bg)
            w[key].pack(side=tk.LEFT, padx=2)

        # 走勢圖（迷你版，寬度小）
        w["chart_frame"] = tk.Frame(main_frame, bg=bg, width=140, height=32)
        w["chart_frame"].pack(side=tk.LEFT, padx=6)
        w["chart_frame"].pack_propagate(False)

        # 成交量
        w["vol"] = tk.Label(main_frame, text="--", width=8, anchor="w",
                              font=("Consolas", 9), fg=self.COLOR_DIM, bg=bg)
        w["vol"].pack(side=tk.LEFT, padx=2)

        # 漲跌停狀態（簡潔版本）
        w["limits"] = tk.Label(main_frame, text="--", width=6, anchor="w",
                                 font=("Microsoft JhengHei UI", 9, "bold"), fg=self.COLOR_DIM, bg=bg)
        w["limits"].pack(side=tk.LEFT, padx=6)

        w["_del_btn"] = tk.Button(
            main_frame, text="❌", font=("Segoe UI Emoji", 9),
            bg=bg, fg="#FF6666", bd=0, activebackground=bg, cursor="hand2",
            command=lambda c=code: self._remove_stock(c)
        )
        w["_del_btn"].pack(side=tk.LEFT, padx=2)
        self.row_widgets[code] = w

    def _load_stock_names(self):
        """載入或建立股票名稱映射表"""
        if os.path.exists(STOCK_NAMES_FILE):
            try:
                with open(STOCK_NAMES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_STOCK_NAMES.copy()
    
    def _save_stock_names(self):
        """保存股票名稱映射表"""
        try:
            with open(STOCK_NAMES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stock_names, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _search_stock(self, query):
        """搜尋台股 - 線上查詢名稱 + 強制台灣格式"""
        query = query.strip()
        if not query: 
            return None, None
        
        # 提取純數字（移除 .TW/.TWO）
        code_only = query
        if query.endswith(".TW"):
            code_only = query.replace(".TW", "")
        elif query.endswith(".TWO"):
            code_only = query.replace(".TWO", "")
        
        # 1. 檢查是否為 4-6 位數字代碼
        if code_only.isdigit() and 4 <= len(code_only) <= 6:
            code = f"{code_only}.TW"
            
            # 2. 試著線上查詢名稱
            name = self._fetch_stock_name_online(code)
            if name:
                # 保存到本地緩存
                self.stock_names[code_only] = name
                self._save_stock_names()
                return code, name
            
            # 3. 查詢本地緩存
            name = self.stock_names.get(code_only, code_only)
            return code, name
        
        return None, None
    
    def _fetch_stock_name_online(self, code):
        """用 TWSE 與 Yahoo 交替搜尋，回傳中文名稱（若有）"""
        try:
            import urllib.request, urllib.parse
            q = str(code).split('.')[0]

            # 先用台灣證交所的 codeQuery API
            try:
                url = 'https://www.twse.com.tw/zh/api/codeQuery?query=' + urllib.parse.quote(q)
                with urllib.request.urlopen(url, timeout=6) as resp:
                    data = json.load(resp)
                suggestions = data.get('suggestions') or data.get('data') or []
                for s in suggestions:
                    if isinstance(s, str):
                        parts = s.split('\t')
                        if parts and parts[0] == q and len(parts) >= 2:
                            return parts[1]
                    elif isinstance(s, list) and len(s) >= 2 and str(s[0]) == q:
                        return s[1]
            except Exception:
                # 若 TWSE 查詢失敗，繼續到 Yahoo
                pass

            # fallback: Yahoo Finance search
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(q)}"
            with urllib.request.urlopen(url, timeout=6) as resp:
                y = json.load(resp)
            for item in y.get('quotes', []):
                sym = item.get('symbol', '')
                if sym and sym.upper().endswith('.TW'):
                    name = item.get('shortname') or item.get('shortName') or item.get('longname') or item.get('longName')
                    if name and name != code:
                        return name
        except Exception:
            pass
        return None

    def _add_stock(self):
        query = self.entry.get()
        yf_code, name = self._search_stock(query)
        if not yf_code:
            messagebox.showwarning("找不到股票", f"找不到符合 '{query}' 的股票。")
            return
        if yf_code in self.watchlist:
            messagebox.showinfo("提示", f"'{name}' 已在清單中！")
            self.entry.delete(0, tk.END)
            return
        with self.lock:
            self.watchlist[yf_code] = name
            self._save_watchlist()
            # 同時保存代號→名稱對應
            code_num = yf_code.split('.')[0]
            self.stock_names[code_num] = name
            self._save_stock_names()
        self._create_row(yf_code, name)
        self._recolor_rows()
        self._update_window_size()
        self.entry.delete(0, tk.END)
        threading.Thread(target=self._one_shot, daemon=True).start()

    def _remove_stock(self, code):
        if code in self.watchlist:
            with self.lock:
                del self.watchlist[code]
                self._save_watchlist()
            if code in self.row_widgets:
                self.row_widgets[code]["_frame"].destroy()
                del self.row_widgets[code]
            self._recolor_rows()
            self._update_window_size()

    def _recolor_rows(self):
        for idx, code in enumerate(list(self.watchlist.keys())):
            if code in self.row_widgets:
                bg = self.COLOR_BG_ROW1 if idx % 2 == 0 else self.COLOR_BG_ROW2
                w = self.row_widgets[code]
                w["_frame"].configure(bg=bg)
                for key, widget in w.items():
                    if key not in ["_frame", "_del_btn"] and isinstance(widget, tk.Label):
                        widget.configure(bg=bg)
                w["_del_btn"].configure(bg=bg, activebackground=bg)

    def _update_window_size(self):
        h = 145 + len(self.watchlist) * 36
        w = 640
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _fetch_one(self, code):
        try:
            # lazy import yfinance to avoid startup penalty
            import yfinance as yf
            ticker = yf.Ticker(code)
            fi = ticker.fast_info
            price, prev_close = fi.last_price, fi.previous_close
            if not price or not prev_close or prev_close == 0: return None
            change = price - prev_close
            pct = (change / prev_close) * 100
            vol_zhang = int(fi.last_volume) // 1000 if fi.last_volume else 0

            # 漲跌停（簡化計算：±10%）
            limit_up = round(prev_close * 1.1, 2)
            limit_down = round(prev_close * 0.9, 2)

            # 取得當日走勢（先試 1 分鐘，再試 5 分鐘）
            intraday = []
            try:
                # 優先取 1 分鐘線（更細膩的波動）
                hist = ticker.history(period='1d', interval='1m')
                if not hist.empty:
                    closes = hist['Close'].dropna().tolist()
                    intraday = [float(c) for c in closes]
                
                # 如果沒有 1 分鐘線，試試 5 分鐘線
                if len(intraday) < 3:
                    hist = ticker.history(period='1d', interval='5m')
                    if not hist.empty:
                        closes = hist['Close'].dropna().tolist()
                        intraday = [float(c) for c in closes]
                
                # 如果還是不夠，用昨天的收盤 + 今天的開盤 + 現價生成簡單走勢
                if len(intraday) < 3:
                    intraday = [prev_close] * 5 + [price]
            except Exception:
                # fallback：用前一日和現價
                intraday = [prev_close] * 5 + [price]

            return {"price": price, "change": change, "pct": pct, "vol_zhang": vol_zhang,
                    "limit_up": limit_up, "limit_down": limit_down, "intraday": intraday}
        except Exception:
            return None

    def _fetch_all(self):
        with self.lock:
            codes = list(self.watchlist.keys())
        results = {}
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(self._fetch_one, code): code for code in codes}
            for f in as_completed(futures):
                code = futures[f]
                data = f.result()
                if data: results[code] = data
        return results

    def _apply_data(self, results):
        for code, data in results.items():
            if code not in self.row_widgets: continue
            w = self.row_widgets[code]
            change = data["change"]
            color = self.COLOR_UP if change > 0 else (self.COLOR_DOWN if change < 0 else self.COLOR_FLAT)
            sign = "+" if change > 0 else ""
            w["price"].config(text=f'{data["price"]:.2f}', fg=color)
            w["change"].config(text=f'{sign}{data["change"]:.2f}', fg=color)
            w["pct"].config(text=f'{sign}{data["pct"]:.2f}%', fg=color)
            vz = data["vol_zhang"]
            vol_text = f"{vz / 10000:.1f}萬張" if vz >= 10000 else (f"{vz:,}張" if vz > 0 else "--")
            w["vol"].config(text=vol_text, fg=self.COLOR_DIM)

            # 判斷漲跌停狀態
            price = data["price"]
            limit_up = data.get('limit_up', 0)
            limit_down = data.get('limit_down', 0)
            
            # 漲停：價格 >= 漲停價 * 0.99（容許誤差）
            if limit_up > 0 and price >= limit_up * 0.99:
                w["limits"].config(text="🔴 漲停", fg="#FF4444")
            # 跌停：價格 <= 跌停價 * 1.01（容許誤差）
            elif limit_down > 0 and price <= limit_down * 1.01:
                w["limits"].config(text="🟢 跌停", fg="#00CC66")
            else:
                w["limits"].config(text="正常", fg=self.COLOR_DIM)

            # 畫走勢圖
            intraday = data.get('intraday', [])
            self._draw_intraday_chart(w, intraday, limit_up, limit_down, color)

        self.status_lbl.config(text=f"✅ 更新於 {datetime.now().strftime('%H:%M:%S')}", fg="#88CC88")

    def _draw_intraday_chart(self, w, intraday, limit_up, limit_down, color):
        """用 matplotlib 繪製當日走勢圖（迷你版），lazy import 減少啟動延遲"""
        frame = w.get('chart_frame') if isinstance(w, dict) else None
        # 如果用舊版 tree (非 dict)，不可畫
        if not frame or not intraday or len(intraday) < 2:
            return
        # 清除舊圖
        for child in frame.winfo_children():
            child.destroy()
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            fig = Figure(figsize=(1.6, 0.32), dpi=80, facecolor=self.COLOR_BG_ROW1)
            ax = fig.add_subplot(111)

            prices = intraday
            x = list(range(len(prices)))
            ax.plot(x, prices, color=color, linewidth=1.6, solid_capstyle='round')

            ymin = min(prices)
            ymax = max(prices)
            diff = ymax - ymin
            if diff <= 0:
                margin = max(0.5, abs(ymax) * 0.002)
            else:
                margin = max(diff * 0.15, 0.1)
            ax.set_ylim(ymin - margin, ymax + margin)
            lower_fill = ymin - margin
            ax.fill_between(x, prices, lower_fill, alpha=0.18, color=color)

            if limit_up and limit_up > 0:
                ax.axhline(y=limit_up, color='#FF4444', linestyle='--', linewidth=0.8, alpha=0.6)
            if limit_down and limit_down > 0:
                ax.axhline(y=limit_down, color='#00CC66', linestyle='--', linewidth=0.8, alpha=0.6)

            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception:
            return

    def _refresh_loop(self):
        while self.is_running:
            self.root.after(0, lambda: self.status_lbl.config(text="🔄 更新中...", fg="#FFCC00"))
            results = self._fetch_all()
            if results: self.root.after(0, lambda r=results: self._apply_data(r))
            for _ in range(REFRESH_INTERVAL * 10):
                if not self.is_running: return
                time.sleep(0.1)

    def _start_refresh_loop(self):
        threading.Thread(target=self._refresh_loop, daemon=True).start()

    def _manual_refresh(self):
        threading.Thread(target=self._one_shot, daemon=True).start()

    def _one_shot(self):
        self.root.after(0, lambda: self.status_lbl.config(text="🔄 更新中...", fg="#FFCC00"))
        results = self._fetch_all()
        if results: self.root.after(0, lambda r=results: self._apply_data(r))

    def _toggle_pin(self):
        self.topmost = not self.topmost
        self.root.attributes('-topmost', self.topmost)
        self.pin_btn.config(text="📌" if self.topmost else "📍")

    def _on_close(self):
        self.is_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockWidget(root)
    root.mainloop()