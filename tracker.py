import yfinance as yf
import pandas as pd
import datetime
import os
import requests

def run_global_institutional_tracker():
    # 擴增至全球關鍵機構級標的 (可自由擴充美股、台股、權值股與正二槓桿)
    watchlist = {
        "2330.TW": {"name": "台積電 (TSMC)", "type": "台股權值"},
        "00685L.TW": {"name": "元大台灣加權正2", "type": "槓桿攻擊"},
        "00713.TW": {"name": "元大台灣高息低波", "type": "防禦收息"},
        "NVDA": {"name": "NVIDIA (全球AI霸主)", "type": "美股核心"},
        "AAPL": {"name": "Apple", "type": "美股核心"},
        "^TWII": {"name": "台灣加權指數", "type": "大盤指標"},
        "^VIX": {"name": "VIX 恐慌指數", "type": "宏觀風向"}
    }
    
    print(f"🏛️ APEX 全球機構數據追蹤引擎啟動: {datetime.datetime.now()}")
    
    records = []
    fmp_api_key = os.getenv("FMP_API_KEY", "") # 可選：填入 FMP 獲得全球分析師預估
    
    for ticker, info in watchlist.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                change_pct = ((current_price - prev_price) / prev_price) * 100
                
                # 預設法人共識 EPS (若有 API Key 則嘗試串接真實全球分析師數據)
                consensus_eps = "N/A"
                target_high = "N/A"
                target_low = "N/A"
                
                if fmp_api_key and not ticker.startswith("^"):
                    try:
                        url = f"https://financialmodelingprep.com/api/v3/analyst-estimates/{ticker}?apikey={fmp_api_key}"
                        res = requests.get(url).json()
                        if res and isinstance(res, list):
                            consensus_eps = res[0].get("estimatedEpsAvg", "N/A")
                    except:
                        pass
                
                records.append({
                    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Ticker": ticker,
                    "Name": info["name"],
                    "Category": info["type"],
                    "Price": round(current_price, 2),
                    "Change_Pct": round(change_pct, 2),
                    "Consensus_EPS": consensus_eps
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
        
    df_combined.tail(500).to_csv(log_file, index=False)
    print("✅ 全球機構數據與分析師共識同步完成。")

if __name__ == "__main__":
    run_global_institutional_tracker()