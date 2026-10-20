import yfinance as yf
import pandas as pd
import datetime
import os

def run_global_live_tracker():
    watchlist = {
        "2330.TW": {"name": "台積電 (2330)", "type": "權值核心"},
        "00685L.TW": {"name": "元大台灣加權正2", "type": "槓桿攻擊"},
        "00631L.TW": {"name": "富邦台灣加權正2", "type": "槓桿攻擊"},
        "00713.TW": {"name": "元大台灣高息低波", "type": "防禦收息"},
        "^TWII": {"name": "台灣加權指數", "type": "大盤指標"},
        "^GSPC": {"name": "S&P 500", "type": "美股宏觀"},
        "^VIX": {"name": "VIX 恐慌指數", "type": "市場情緒"}
    }
    
    print(f"🏛️ APEX 每日機構與市場數據即時追蹤引擎啟動: {datetime.datetime.now()}")
    
    records = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for ticker, info_meta in watchlist.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            if not current_price:
                hist = stock.history(period="2d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
            
            forward_eps = info.get('forwardEps', 0.0)
            target_mean = info.get('targetMeanPrice', 0.0)
            
            records.append({
                "Timestamp": timestamp,
                "Ticker": ticker,
                "Name": info_meta["name"],
                "Category": info_meta["type"],
                "Price": round(float(current_price), 2) if current_price else 0.0,
                "Forward_EPS": forward_eps if forward_eps else "N/A",
                "Target_Mean_Price": target_mean if target_mean else "N/A"
            })
        except Exception as e:
            print(f"抓取 {ticker} 異常: {e}")
            
    df_new = pd.DataFrame(records)
    log_file = "global_market_consensus.csv"
    
    if os.path.exists(log_file):
        df_old = pd.read_csv(log_file)
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_combined = df_new
        
    df_combined.tail(2000).to_csv(log_file, index=False)
    print("✅ 每日最新機構預估與市場數據同步完成。")

if __name__ == "__main__":
    run_global_live_tracker()