import yfinance as yf
import pandas as pd
import datetime
import os

def run_background_tracker():
    tickers = ["00685L.TW", "00713.TW", "2330.TW", "^TWII", "^VIX"]
    print(f"🏛️ APEX 24H 背景數據追蹤器啟動: {datetime.datetime.now()}")
    
    data = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="1d")
            if not hist.empty:
                data[t] = float(hist['Close'].iloc[-1])
        except Exception as e:
            print(f"抓取 {t} 失敗: {e}")
            
    # 將每日數據寫入紀錄 CSV 檔案（實現資料持久化）
    log_entry = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **data
    }
    
    df_new = pd.DataFrame([log_entry])
    if os.path.exists("market_log.csv"):
        df_old = pd.read_csv("market_log.csv")
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_combined = df_new
        
    df_combined.tail(100).to_csv("market_log.csv", index=False)
    print("✅ 背景數據同步與日誌寫入完成。")

if __name__ == "__main__":
    run_background_tracker()