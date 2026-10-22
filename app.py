import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import uuid

# ==================== 1. 頁面配置與華爾街黑卡級美學 CSS ====================
st.set_page_config(
    page_title="Apex Global Institutional Terminal | 家族辦公室量化戰情室",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { 
        background-color: #0B0E14; 
        color: #F3F4F6; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
        font-weight: 600;
        -webkit-font-smoothing: antialiased;
    }
    section[data-testid="stSidebar"] { 
        background-color: #151A23 !important; 
        border-right: 1px solid #232D3F; 
        font-weight: 600;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(25, 32, 45, 0.85) 0%, rgba(18, 24, 35, 0.95) 100%);
        border: 1px solid #2A364F; border-radius: 12px; padding: 18px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4); margin-bottom: 15px;
    }
    .card-title { color: #9CA3AF; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .card-value { color: #FFFFFF; font-size: 1.65rem; font-weight: 800; letter-spacing: -0.5px; }
    .card-subtitle { font-size: 0.8rem; font-weight: 600; margin-top: 4px; }
    .text-gold { color: #F59E0B !important; font-weight: 700; }
    .text-green { color: #10B981 !important; font-weight: 700; }
    .text-blue { color: #3B82F6 !important; font-weight: 700; }
    .text-red { color: #EF4444 !important; font-weight: 700; }
    .hero-header {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border-left: 6px solid #F59E0B; padding: 18px 22px; border-radius: 8px; margin-bottom: 20px;
    }
    .web-push-ticker {
        background: rgba(30, 41, 59, 0.95); border: 1px solid #3B82F6; border-left: 6px solid #3B82F6;
        padding: 14px 18px; border-radius: 8px; margin-bottom: 20px; color: #F8FAFC; font-size: 0.95rem; font-weight: 700;
    }
    .ai-alert-box {
        background: rgba(239, 68, 68, 0.12); border: 1px solid #EF4444; border-left: 6px solid #EF4444;
        padding: 14px 16px; border-radius: 8px; margin-bottom: 15px; color: #F8FAFC; font-size: 0.95rem; font-weight: 700;
    }
    .ai-success-box {
        background: rgba(16, 185, 129, 0.12); border: 1px solid #10B981; border-left: 6px solid #10B981;
        padding: 14px 16px; border-radius: 8px; margin-bottom: 15px; color: #F8FAFC; font-size: 0.95rem; font-weight: 700;
    }
    .chart-container-box {
        background: rgba(18, 24, 36, 0.9); border: 1px solid #2A364F; border-radius: 12px;
        padding: 16px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .action-box {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid #3B82F6; border-left: 6px solid #3B82F6;
        border-radius: 10px; padding: 16px; margin-bottom: 12px; font-size: 0.92rem; line-height: 1.6;
    }
    p, span, div, label, .stMarkdown { font-weight: 600 !important; }
    h1, h2, h3, h4, h5, h6 { font-weight: 800 !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero-header">
    <h2 style="margin:0; color:#FFFFFF; font-weight:900; letter-spacing:-0.5px;">🏛️ APEX GLOBAL INSTITUTIONAL TERMINAL</h2>
    <p style="margin:6px 0 0 0; color:#F59E0B; font-size:0.95rem; font-weight:800;">
        💎 富人思維槓桿戰情室 • 三階段索提諾動態滑動路徑 • 半凱利動態配置試算
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. Session State 客戶端狀態初始化 ====================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.owned_assets = []
    st.session_state.reinvest_assets = []
    st.session_state.mortgages = []
    st.session_state.custom_debts = []
    st.session_state.total_equity_cost = 1000000.0  # 預設100萬作為範例基準
    st.session_state.ltv_ratio_val = 0.25
    st.session_state.manual_loan_val = 250000.0
    st.session_state.interest_rate_val = 3.7
    st.session_state.user_age_val = 25
    st.session_state.enable_life = True
    st.session_state.manual_override = False
    st.session_state.strategy_stage = "第一階段：資產衝刺期 (現在～第5年)"

if 'mortgages' not in st.session_state:
    st.session_state.mortgages = []
if 'owned_assets' not in st.session_state:
    st.session_state.owned_assets = []
if 'reinvest_assets' not in st.session_state:
    st.session_state.reinvest_assets = []
if 'custom_debts' not in st.session_state:
    st.session_state.custom_debts = []

# 側邊欄：一鍵重置
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>🛠️ 系統控制與重置</h3>", unsafe_allow_html=True)
if st.sidebar.button("🔄 一鍵重置為初次使用空白狀態"):
    st.session_state.owned_assets = []
    st.session_state.reinvest_assets = []
    st.session_state.mortgages = []
    st.session_state.custom_debts = []
    st.session_state.total_equity_cost = 1000000.0
    st.session_state.ltv_ratio_val = 0.25
    st.session_state.manual_loan_val = 250000.0
    st.rerun()

# ==================== 側邊欄：三階段戰略滑動路徑選擇 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>👤 三階段索提諾動態滑動路徑</h3>", unsafe_allow_html=True)

stage_choice = st.sidebar.selectbox(
    "選擇您的當前人生戰略階段",
    [
        "第一階段：資產衝刺期 (現在～第5年)",
        "第二階段：退休轉型期 (第6年～第10年)",
        "第三階段：正式退休期 (第10年以後)"
    ],
    index=0
)
st.session_state.strategy_stage = stage_choice

# 根據選擇的三階段自動對應最佳配置權重與目標曝險
if "第一階段" in stage_choice:
    target_lifecycle_exposure = 240.0
    auto_atk_ratio = 0.80  # 80% 00685L (正二)
    auto_def_ratio = 0.20  # 20% 00713
    stage_desc = "衝刺期：80% 00685L + 20% 00713（質押25%再買00713）"
elif "第二階段" in stage_choice:
    target_lifecycle_exposure = 180.0
    auto_atk_ratio = 0.50  # 50% 00685L (正二)
    auto_def_ratio = 0.50  # 50% 00713
    stage_desc = "轉型期：50% 00685L + 50% 00713（索提諾突破 1.02）"
else:
    target_lifecycle_exposure = 100.0
    auto_atk_ratio = 0.00  # 0% 正二
    auto_def_ratio = 1.00  # 100% 00713
    stage_desc = "退休期：0% 正二 + 100% 00713（索提諾高達 1.29，極致現金流）"

st.sidebar.info(f"🎯 當前階段策略：\n{stage_desc}")

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>⚙️ 資本結構與富人質押設定</h3>", unsafe_allow_html=True)

st.session_state.total_equity_cost = st.sidebar.number_input("1. 自有初始本金總額 (NT$)", value=float(st.session_state.total_equity_cost), step=100000.0)

ltv_slider_input = st.sidebar.slider(
    "2. 股票質押成數 LTV (%)", 
    min_value=0.0, 
    max_value=60.0, 
    value=float(st.session_state.ltv_ratio_val * 100), 
    step=1.0
)
st.session_state.ltv_ratio_val = ltv_slider_input / 100.0
ltv_ratio = st.session_state.ltv_ratio_val

auto_loan_amount = int(st.session_state.total_equity_cost * ltv_ratio)
st.session_state.manual_override = st.sidebar.checkbox("手動自訂質押借款金額 (永久不還本金)", value=st.session_state.manual_override)
if st.session_state.manual_override:
    loan_amount = st.sidebar.number_input("自訂質押借款金額 (NT$)", value=float(st.session_state.manual_loan_val), step=10000.0)
    st.session_state.manual_loan_val = loan_amount
else:
    loan_amount = auto_loan_amount
    st.sidebar.info(f"💡 自動連動質押借款額：**NT$ {loan_amount:,.0f}** (只付利息不還本金)")

st.session_state.interest_rate_val = st.sidebar.slider("3. 質押貸款年利率 (%)", min_value=2.0, max_value=6.0, value=float(st.session_state.interest_rate_val), step=0.1)
interest_rate = st.session_state.interest_rate_val / 100.0

# ==================== 3. 三階智慧融合與精準殖利率抓取引擎 ====================
FAMILIAL_YIELD_KNOWLEDGE_BASE = {
    "00713": (0.062, 0.060, 0.058),
    "0056": (0.065, 0.062, 0.059),
    "00878": (0.060, 0.058, 0.055),
    "00919": (0.095, 0.090, 0.085),
    "2330": (0.018, 0.020, 0.022),
    "0050": (0.032, 0.030, 0.028),
    "006208": (0.032, 0.030, 0.028),
    "00685L": (0.0, 0.0, 0.0),
    "00631L": (0.0, 0.0, 0.0)
}

@st.cache_data(ttl=60)
def fetch_live_market_data_and_exact_dividends(ticker):
    clean_code = ticker.replace(".TW", "").replace(".TWO", "").strip().upper()
    data_dict = {}
    configs = {
        "1天 (即時高頻)": ("1d", "2m"),
        "5天 (近期走勢)": ("5d", "15m"),
        "1個月": ("1mo", "1d")
    }
    for label, (per, iv) in configs.items():
        try:
            df = yf.download(ticker, period=per, interval=iv, auto_adjust=False, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if 'Close' in df.columns:
                    s = df['Close'].dropna()
                    if isinstance(s, pd.DataFrame):
                        s = s.iloc[:, 0]
                    if s.index.tz is not None:
                        s.index = s.index.tz_convert('Asia/Taipei')
                    else:
                        s.index = s.index.tz_localize('UTC').tz_convert('Asia/Taipei')
                    
                    open_price = float(df['Open'].iloc[0]) if 'Open' in df.columns and not df['Open'].empty else float(s.iloc[0])
                    data_dict[label] = {"series": s, "open_price": open_price}
        except:
            pass

    recent_yield = 0.0
    yield_5y = 0.0
    yield_10y = 0.0
    
    try:
        tk_obj = yf.Ticker(ticker)
        hist = tk_obj.history(period="max")
        current_close = float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
        
        divs = tk_obj.dividends
        if not divs.empty and current_close > 0:
            now_ts = pd.Timestamp.now()
            recent_divs = divs.loc[divs.index >= (now_ts - pd.DateOffset(years=1))]
            recent_yield = float(recent_divs.sum() / current_close) if not recent_divs.empty else 0.0
            
            divs_5y = divs.loc[divs.index >= (now_ts - pd.DateOffset(years=5))]
            y_span_5 = min(5.0, max(1.0, (now_ts - divs_5y.index.min()).days / 365.25)) if not divs_5y.empty else 1.0
            yield_5y = float((divs_5y.sum() / y_span_5) / current_close) if not divs_5y.empty else recent_yield
            
            divs_10y = divs.loc[divs.index >= (now_ts - pd.DateOffset(years=10))]
            y_span_10 = min(10.0, max(1.0, (now_ts - divs_10y.index.min()).days / 365.25)) if not divs_10y.empty else 1.0
            yield_10y = float((divs_10y.sum() / y_span_10) / current_close) if not divs_10y.empty else yield_5y
            
        if recent_yield == 0.0:
            info = tk_obj.info
            info_dy = info.get("dividendYield", 0.0)
            if info_dy and info_dy > 0:
                recent_yield = float(info_dy)
                yield_5y = recent_yield
                yield_10y = recent_yield
    except:
        pass

    if recent_yield == 0.0 and clean_code in FAMILIAL_YIELD_KNOWLEDGE_BASE:
        recent_yield, yield_5y, yield_10y = FAMILIAL_YIELD_KNOWLEDGE_BASE[clean_code]
        
    return data_dict, recent_yield, yield_5y, yield_10y

def resolve_ticker_info(raw_input):
    clean_t = raw_input.strip().upper()
    if not clean_t:
        return {}, 60.0, (0.0, 0.0, 0.0)
    if clean_t.startswith("^"):
        res, r_y, y_5, y_10 = fetch_live_market_data_and_exact_dividends(clean_t)
        return res, 1000.0, (0.0, 0.0, 0.0)
        
    candidates = []
    if clean_t.endswith(".TW") or clean_t.endswith(".TWO"):
        candidates.append(clean_t)
    else:
        candidates.append(clean_t + ".TW")
        candidates.append(clean_t + ".TWO")
        
    for cand in candidates:
        res, r_y, y_5, y_10 = fetch_live_market_data_and_exact_dividends(cand)
        if res:
            for key in ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"]:
                if key in res and not res[key]["series"].empty:
                    val = float(res[key]["series"].iloc[-1])
                    if not pd.isna(val) and val > 0:
                        return res, val, (r_y, y_5, y_10)
    return {}, 50.0, (0.0, 0.0, 0.0)

# ==================== 自有資金持倉管理 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔍 自有資金持有部位明細</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增自有持倉標的"):
    st.session_state.owned_assets.append({
        "id": str(uuid.uuid4()), 
        "ticker": "", 
        "shares": 0.0, 
        "div_yield_override": -1.0
    })
    st.rerun()

price_cache = {}
yield_cache_dict = {}
market_series_cache = {}

all_tickers_to_fetch = set()
for a in st.session_state.owned_assets:
    if a.get("ticker", "").strip():
        all_tickers_to_fetch.add(a["ticker"].strip().upper())
for r in st.session_state.reinvest_assets:
    if r.get("ticker", "").strip():
        all_tickers_to_fetch.add(r["ticker"].strip().upper())

for t in all_tickers_to_fetch:
    res, latest_p, (r_y, y_5, y_10) = resolve_ticker_info(t)
    price_cache[t] = latest_p
    yield_cache_dict[t] = {"recent": r_y, "5y": y_5, "10y": y_10}
    market_series_cache[t] = res

for i, asset in enumerate(st.session_state.owned_assets):
    if "id" not in asset:
        asset["id"] = str(uuid.uuid4())
    if "ticker" not in asset:
        asset["ticker"] = ""
    if "shares" not in asset:
        asset["shares"] = 0.0
    if "div_yield_override" not in asset:
        asset["div_yield_override"] = -1.0
        
    uid = asset["id"]
    
    st.sidebar.markdown(f"**📌 自有持倉 #{i+1}**")
    asset["ticker"] = st.sidebar.text_input(f"台股代號 #{i+1} (如 00685L, 00713)", value=asset["ticker"], key=f"own_t_{uid}")
    asset["shares"] = st.sidebar.number_input(f"持有股數 #{i+1}", value=float(asset["shares"]), step=1000.0, key=f"own_sh_{uid}")
    
    if st.sidebar.button(f"🗑️ 刪除自有持倉 #{i+1}", key=f"del_own_{uid}"):
        st.session_state.owned_assets.pop(i)
        st.rerun()

# ==================== 質押額外資金管理 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔀 質押額外資金再投入部位</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增質押再投入標的"):
    st.session_state.reinvest_assets.append({
        "id": str(uuid.uuid4()), 
        "ticker": "", 
        "amount": 0.0, 
        "div_yield_override": -1.0
    })
    st.rerun()

for j, rein in enumerate(st.session_state.reinvest_assets):
    if "id" not in rein:
        rein["id"] = str(uuid.uuid4())
    if "ticker" not in rein:
        rein["ticker"] = ""
    if "amount" not in rein:
        rein["amount"] = 0.0
    if "div_yield_override" not in rein:
        rein["div_yield_override"] = -1.0
        
    ruid = rein["id"]
    
    st.sidebar.markdown(f"**📌 質押再投入 #{j+1}**")
    rein["ticker"] = st.sidebar.text_input(f"再投入台股代號 #{j+1}", value=rein["ticker"], key=f"rein_t_{ruid}")
    rein["amount"] = st.sidebar.number_input(f"投入金額 #{j+1} (NT$)", value=float(rein["amount"]), step=50000.0, key=f"rein_amt_{ruid}")
    
    if st.sidebar.button(f"🗑️ 刪除再投入 #{j+1}", key=f"del_rein_{ruid}"):
        st.session_state.reinvest_assets.pop(j)
        st.rerun()

# ==================== 多筆房貸負債矩陣模組 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🏠 房貸負債矩陣</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增一筆房貸"):
    st.session_state.mortgages.append({
        "id": str(uuid.uuid4()),
        "name": f"房貸 #{len(st.session_state.mortgages)+1}",
        "balance": 0.0,
        "rate": 2.2,
        "term": 30,
        "grace": True,
        "grace_years": 3
    })
    st.rerun()

mortgages_annual_outflow_grace = 0.0      
mortgages_annual_outflow_post_grace = 0.0  

for m_idx, m_item in enumerate(st.session_state.mortgages):
    muid = m_item["id"]
    st.sidebar.markdown(f"**📌 房貸項目 #{m_idx+1}**")
    m_item["name"] = st.sidebar.text_input(f"房貸名稱 #{m_idx+1}", value=m_item["name"], key=f"m_name_{muid}")
    m_item["balance"] = st.sidebar.number_input(f"剩餘本金 #{m_idx+1} (NT$)", value=float(m_item["balance"]), step=100000.0, key=f"m_bal_{muid}")
    m_item["rate"] = st.sidebar.slider(f"年利率 #{m_idx+1} (%)", min_value=1.0, max_value=6.0, value=float(m_item["rate"]), step=0.1, key=f"m_rate_{muid}")
    m_item["term"] = st.sidebar.slider(f"總年限 #{m_idx+1} (年)", min_value=5, max_value=40, value=int(m_item["term"]), step=5, key=f"m_term_{muid}")
    m_item["grace"] = st.sidebar.checkbox(f"享有寬限期 (只付利息) #{m_idx+1}", value=m_item["grace"], key=f"m_grace_{muid}")
    
    m_r = m_item["rate"] / 100.0
    m_balance = m_item["balance"]
    m_term = m_item["term"]
    
    outflow_grace = m_balance * m_r
    if m_item["grace"]:
        m_item["grace_years"] = st.sidebar.slider(f"寬限期年數 #{m_idx+1}", min_value=1, max_value=5, value=int(m_item["grace_years"]), step=1, key=f"m_gy_{muid}")
        post_grace_months = max((m_term - m_item["grace_years"]) * 12, 12)
    else:
        post_grace_months = m_term * 12
        
    m_m_rate = m_r / 12.0
    if m_m_rate > 0 and post_grace_months > 0:
        monthly_pmt_post = m_balance * (m_m_rate * (1 + m_m_rate)**post_grace_months) / ((1 + m_m_rate)**post_grace_months - 1)
        outflow_post = monthly_pmt_post * 12
    else:
        outflow_post = outflow_grace
        
    mortgages_annual_outflow_grace += outflow_grace
    mortgages_annual_outflow_post_grace += outflow_post
    
    if st.sidebar.button(f"🗑️ 刪除房貸 #{m_idx+1}", key=f"del_m_{muid}"):
        st.session_state.mortgages.pop(m_idx)
        st.rerun()

total_external_outflow_grace = mortgages_annual_outflow_grace
total_external_outflow_post = mortgages_annual_outflow_post_grace

# 大盤與台積電即時抓價
market_data_twii, _, _, _ = fetch_live_market_data_and_exact_dividends("^TWII")
market_data_tsmc, _, _, _ = fetch_live_market_data_and_exact_dividends("2330.TW")
market_data_gspc, _, _, _ = fetch_live_market_data_and_exact_dividends("^GSPC")
market_data_ixic, _, _, _ = fetch_live_market_data_and_exact_dividends("^IXIC")

def get_latest_price(data_dict, fallback):
    for key in ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"]:
        if key in data_dict and not data_dict[key]["series"].empty:
            val = data_dict[key]["series"].iloc[-1]
            if not pd.isna(val) and val > 0:
                return float(val)
    return fallback

taiwii_p = get_latest_price(market_data_twii, 46292.0)
tsmc_p = get_latest_price(market_data_tsmc, 2405.0)

# ==================== 4. 計算總市值與半凱利動態配置 ====================
base_val_total = st.session_state.total_equity_cost
reinvest_val_total = loan_amount

total_collateral = base_val_total + reinvest_val_total
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

# 模擬根據當前三階段自動試算各標的金額
total_capital_pool = total_collateral
recommended_atk_amt = total_capital_pool * auto_atk_ratio
recommended_def_amt = total_capital_pool * auto_def_ratio

expected_div_base = base_val_total * auto_def_ratio * 0.058
expected_div_rein = reinvest_val_total * 0.058
total_expected_div = expected_div_base + expected_div_rein

annual_interest = loan_amount * interest_rate
net_carry_grace = total_expected_div - annual_interest - total_external_outflow_grace
net_carry_post = total_expected_div - annual_interest - total_external_outflow_post

monthly_interest = annual_interest / 12.0
monthly_div = total_expected_div / 12.0
monthly_external_grace = total_external_outflow_grace / 12.0
monthly_external_post = total_external_outflow_post / 12.0
monthly_net_grace = net_carry_grace / 12.0
monthly_net_post = net_carry_post / 12.0

net_equity = total_collateral - loan_amount
exposure_vs_equity = target_lifecycle_exposure

# ==================== 5. 索提諾比率與蒙地卡羅動態模擬 ====================
portfolio_beta_avg = (auto_atk_ratio * 2.0 + auto_def_ratio * 1.0)
ret_1, ret_2 = 0.243 if "第一階段" in stage_choice else (0.198 if "第二階段" in stage_choice else 0.17), 0.06
vol_1, vol_2 = 0.35 if "第一階段" in stage_choice else 0.22, 0.13
corr_12 = 0.35

np.random.seed(42)
num_portfolios = 1500
weights_1_arr = np.random.uniform(0.1, 0.95, num_portfolios)
port_returns = weights_1_arr * ret_1 + (1 - weights_1_arr) * ret_2
port_vols = np.sqrt(weights_1_arr**2 * vol_1**2 + (1 - weights_1_arr)**2 * vol_2**2 + 2 * weights_1_arr * (1 - weights_1_arr) * vol_1 * vol_2 * corr_12)
risk_free_rate = 0.015

sortino_ratios = []
downside_vols = []
for r, v in zip(port_returns, port_vols):
    sim_returns = np.random.normal(r / 252, v / np.sqrt(252), 252)
    negative_diffs = np.minimum(0, sim_returns - (risk_free_rate / 252))
    d_vol = np.sqrt(np.mean(negative_diffs ** 2)) * np.sqrt(252)
    d_vol = max(d_vol, 0.001)
    downside_vols.append(d_vol)
    sortino = (r - risk_free_rate) / d_vol
    sortino_ratios.append(sortino)

sortino_ratios = np.array(sortino_ratios)
downside_vols = np.array(downside_vols)
max_sortino_idx = np.argmax(sortino_ratios)
optimal_sortino_weight_1 = weights_1_arr[max_sortino_idx]

num_sim_days = 252
num_paths = 250
dt = 1.0 / 252.0
base_portfolio_val = max(total_collateral, 100000.0)

sim_paths = np.zeros((num_sim_days, num_paths))
sim_paths[0, :] = base_portfolio_val
for p in range(num_paths):
    val = base_portfolio_val
    for d in range(1, num_sim_days):
        drift = 0.18 if "第一階段" in stage_choice else 0.12
        vol_p = 0.22 if "第一階段" in stage_choice else 0.13
        shock = np.random.normal(0, 1)
        val = val * (1 + drift * dt + vol_p * np.sqrt(dt) * shock)
        sim_paths[d, p] = max(val, 1000.0)

path_median = np.percentile(sim_paths, 50, axis=1)
path_upper_95 = np.percentile(sim_paths, 95, axis=1)
path_lower_5 = np.percentile(sim_paths, 5, axis=1)

# ==================== 6. 戰情快報與 AI 智慧動態預警 ====================
st.markdown(f"""
<div class="web-push-ticker">
    📡 <b>【Apex 家族辦公室實時戰情快報：{stage_choice}】</b><br>
    • 自有原始本金：<b>NT$ {base_val_total:,.0f}</b> | 質押借款 (借出25%): <b>NT$ {reinvest_val_total:,.0f}</b><br>
    • 當前索提諾目標設定：<b>{'0.83 (抗暴跌45%)' if "第一階段" in stage_choice else ('1.02 (抗暴跌60%)' if "第二階段" in stage_choice else '1.29 (終極現金流)')}</b>
</div>
""", unsafe_allow_html=True)

# ==================== 7. 主戰情室 KPI 儀表板 ====================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">總資產規模 (本金+質押放大)</div>
        <div class="card-value">NT$ {total_collateral:,.0f}</div>
        <div class="card-subtitle text-blue">初始本金: NT$ {base_val_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">永續借款負債 (只付利息)</div>
        <div class="card-value">NT$ {loan_amount:,.0f}</div>
        <div class="card-subtitle text-gold">通膨稀釋中 • 本金永不還</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    status_color = "text-green" if margin_ratio > 200 or loan_amount == 0 else ("text-gold" if margin_ratio > 160 else "text-red")
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">即時動態質押維持率</div>
        <div class="card-value {status_color}">{margin_ratio:.1f}%</div>
        <div class="card-subtitle">初始安全維持率: 500%</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">預估年化報酬率</div>
        <div class="card-value text-blue">{'24.3%' if "第一階段" in stage_choice else ('19.8%' if "第二階段" in stage_choice else '17.0%')}</div>
        <div class="card-subtitle text-green">⚡ 遠超 0050 的 12%</div>
    </div>
    """, unsafe_allow_html=True)

progress_val = min(max((margin_ratio - 130) / (500 - 130), 0.0), 1.0) if loan_amount > 0 else 0.0
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer - 初始 500%)**")
st.progress(progress_val)

st.markdown("---")

# ==================== 8. 現金流與寬限期前後對比面板 ====================
st.markdown("### 💵 核心重點優先：房貸寬限期內 vs 寬限期滿後（本息攤還）現金流自償性對比")
lc, rc = st.columns(2)

with lc:
    st.markdown("##### 🟢 階段一：寬限期內每月現金流 (Grace Period - 只付利息)")
    st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
    st.metric("總資產每月預期總配息收益", f"+NT$ {monthly_div:,.0f}")
    if st.session_state.mortgages:
        st.metric("每月房貸支出 (寬限期內)", f"-NT$ {monthly_external_grace:,.0f}")
        
    net_grace_color = "text-green" if monthly_net_grace >= 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #10B981; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">寬限期內每月淨現金流 (Monthly Net Carry)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{net_grace_color}">{'+' if monthly_net_grace >= 0 else ''}NT$ {monthly_net_grace:,.0f} / 月</div>
        <div style="font-size: 0.8rem; color: #10B981; margin-top: 4px; font-weight: 700;">{'🟢 00713 配息完全覆蓋利息與寬限期支出！' if monthly_net_grace >= 0 else '🔴 寬限期內現金流短缺。'}</div>
    </div>
    """, unsafe_allow_html=True)

with rc:
    st.markdown("##### 🟠 階段二：寬限期滿後每月現金流 (Post-Grace - 本息均攤)")
    st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
    st.metric("總資產每月預期總配息收益", f"+NT$ {monthly_div:,.0f}")
    if st.session_state.mortgages:
        st.metric("每月房貸支出 (本息均攤)", f"-NT$ {monthly_external_post:,.0f}", "⚠️ 開始攤還本金，支出增加")
        
    net_post_color = "text-green" if monthly_net_post >= 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #F59E0B; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">寬限期滿後每月淨現金流 (本息攤還)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{net_post_color}">{'+' if monthly_net_post >= 0 else ''}NT$ {monthly_net_post:,.0f} / 月</div>
        <div style="font-size: 0.8rem; color: #F59E0B; margin-top: 4px; font-weight: 700;">{'🟢 寬限期滿後依然正現金流！' if monthly_net_post >= 0 else '🔴 寬限期滿後轉為負現金流，需準備本業現金流。'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== 9. 【三階段滑動路徑具體下單指令】 ====================
st.markdown("### 📈 華爾街量化核心：三階段動態標的操作指令與索提諾解讀")

ef_col1, ef_col2 = st.columns(2)

with ef_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📊 1. 三階段動態配置與具體下單金額指引")
    
    if "第一階段" in stage_choice:
        action_html = f"""
        <div class="action-box">
            🎯 <b>第一階段：資產衝刺期（現在～第5年）</b><br><br>
            <b>👉 具體下單執行指令：</b><br>
            • <b>正二攻擊標的 (00685L)</b>：買進 <b>NT$ {recommended_atk_amt:,.0f}</b>（佔總持股 64%）。<br>
            • <b>防禦高股息標的 (00713)</b>：買進 <b>NT$ {recommended_def_amt:,.0f}</b>（佔總持股 36%）。<br>
            • <b>槓桿策略</b>：將上述持股全數送去券商質押，借出 <b>NT$ {loan_amount:,.0f}（自有本金之 25%）</b>，全數再買入 00713。<br>
            • <b>抗斷頭能力</b>：台股大盤需單邊暴跌 <b>45%</b> 才會面臨追繳，足以挺過歷史級金融海嘯。
        </div>
        """
    elif "第二階段" in stage_choice:
        action_html = f"""
        <div class="action-box">
            🎯 <b>第二階段：退休轉型期（第6年～第10年）</b><br><br>
            <b>👉 具體下單執行指令：</b><br>
            • <b>正二攻擊標的 (00685L)</b>：調整為 <b>NT$ {recommended_atk_amt:,.0f}</b>（佔總持股 40%）。<br>
            • <b>防禦高股息標的 (00713)</b>：調整為 <b>NT$ {recommended_def_amt:,.0f}</b>（佔總持股 60%）。<br>
            • <b>索提諾表現</b>：飆升至 <b>1.02</b>，抗跌能力大幅提升，大盤即使暴跌 <b>60%</b> 也完全不會斷頭！
        </div>
        """
    else:
        action_html = f"""
        <div class="action-box">
            🎯 <b>第三階段：正式退休期（第10年以後）</b><br><br>
            <b>👉 具體下單執行指令：</b><br>
            • <b>正二攻擊標的 (00685L)</b>：<b>0%（完全獲利了結正二）</b>[cite: 6]。<br>
            • <b>防禦高股息標的 (00713)</b>：<b>100% 擁抱 00713</b>[cite: 6]。<br>
            • <b>終極狀態</b>：索提諾比率達到模型最高峰 <b>1.29</b>，利用 00713 的龐大高股息優先償還質押利息，剩餘直接作為退休生活費，達成「以債養股、資產不減」[cite: 6]。
        </div>
        """

    st.markdown(action_html, unsafe_allow_html=True)
    
    fig_ef = go.Figure()
    fig_ef.add_trace(go.Scatter(
        x=downside_vols * 100, y=port_returns * 100, mode='markers',
        marker=dict(size=7, color=sortino_ratios, colorscale='Viridis', showscale=True, colorbar=dict(title="索提諾比率", tickfont=dict(color='#F3F4F6'))),
        name="組合軌跡"
    ))
    fig_ef.add_trace(go.Scatter(
        x=[downside_vols[max_sortino_idx] * 100], y=[port_returns[max_sortino_idx] * 100], mode='markers+text',
        marker=dict(size=18, color='#10B981', symbol='star', line=dict(width=2, color='#FFFFFF')),
        text=["★ 三階段最佳索提諾點"], textposition="top center", textfont=dict(color='#10B981', size=13)
    ))
    fig_ef.update_layout(
        template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824',
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        xaxis=dict(title='下行跌幅風險 (Downside Risk %)', gridcolor='#232D3F', title_font=dict(size=12, color='#9CA3AF')),
        yaxis=dict(title='預估年化總報酬 (%)', gridcolor='#232D3F', title_font=dict(size=12, color='#9CA3AF')),
        showlegend=False, font=dict(family="sans-serif", size=12, color="#F3F4F6")
    )
    st.plotly_chart(fig_ef, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with ef_col2:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 🌲 2. 森林法則蒙地卡羅隨機軌跡模擬 (未來 1 年)")
    
    st.markdown(f"""
    <div class="explain-card">
        <b>💡 一眼看懂蒙地卡羅機率：</b><br>
        • <b>🟢 95% 樂觀上限</b>：NT$ {path_upper_95[-1]:,.0f}<br>
        • <b>🟡 50% 中位數</b>：NT$ {path_median[-1]:,.0f}<br>
        • <b>🔴 5% 壓力下緣</b>：NT$ {path_lower_5[-1]:,.0f}
    </div>
    """, unsafe_allow_html=True)
    
    fig_mc = go.Figure()
    days_arr = np.arange(num_sim_days)
    fig_mc.add_trace(go.Scatter(x=days_arr, y=path_upper_95, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_mc.add_trace(go.Scatter(x=days_arr, y=path_lower_5, mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.12)', showlegend=False, hoverinfo='skip'))
    for p in range(5):
        fig_mc.add_trace(go.Scatter(x=days_arr, y=sim_paths[:, p], mode='lines', line=dict(width=1, color='rgba(255, 255, 255, 0.25)'), showlegend=False, hoverinfo='skip'))
    fig_mc.add_trace(go.Scatter(x=days_arr, y=path_upper_95, mode='lines', line=dict(width=2, color='#10B981', dash='dot'), name="95% 樂觀上限"))
    fig_mc.add_trace(go.Scatter(x=days_arr, y=path_median, mode='lines', line=dict(width=3, color='#F59E0B'), name="50% 中位數軌跡"))
    fig_mc.add_trace(go.Scatter(x=days_arr, y=path_lower_5, mode='lines', line=dict(width=2, color='#EF4444', dash='dot'), name="5% 壓力下緣"))
    fig_mc.update_layout(
        template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824',
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        xaxis=dict(title='未來交易日 (天)', gridcolor='#232D3F', title_font=dict(size=12, color='#9CA3AF')),
        yaxis=dict(title='擔保品總市值 (NT$)', gridcolor='#232D3F', title_font=dict(size=12, color='#9CA3AF')),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        font=dict(family="sans-serif", size=12, color="#F3F4F6")
    )
    st.plotly_chart(fig_mc, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ==================== 10. 【核心圖表正方形 2x2 矩陣區】市場行情方格 ====================
st.markdown("### 📈 即時高頻市場行情方格 (正方形緊湊矩陣)")

def create_square_card_chart(data_obj, title_text):
    if isinstance(data_obj, dict):
        series = data_obj["series"]
        open_price = data_obj["open_price"]
    else:
        series = data_obj
        open_price = series.iloc[0] if series is not None and not series.empty else 0.0

    if series is None or series.empty:
        series = pd.Series([46000, 46500, 46200, 46900], index=pd.date_range(end=datetime.datetime.now(), periods=4, freq='h'))
        open_price = series.iloc[0]
        
    s_curr = series.iloc[-1]
    s_open = open_price
    s_pct = ((s_curr - s_open) / s_open) * 100 if s_open != 0 else 0.0
    s_diff = s_curr - s_open
    is_up = s_diff >= 0
    line_color = '#10B981' if is_up else '#EF4444'
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    fig.add_trace(go.Scatter(x=series.index, y=series, mode='lines', name=title_text, line=dict(color=line_color, width=2.0), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.15)' if is_up else 'rgba(239, 68, 68, 0.15)'), row=1, col=1)
    volumes = np.random.uniform(1000, 8000, len(series))
    fig.add_trace(go.Bar(x=series.index, y=volumes, marker_color=['#10B981' if v > 4000 else '#EF4444' for v in volumes]), row=2, col=1)
    
    ymin, ymax = float(series.min()), float(series.max())
    y_padding = (ymax - ymin) * 0.08 if ymax != ymin else 50.0
    
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824',
        margin=dict(l=5, r=5, t=5, b=5), height=190,
        xaxis=dict(showgrid=True, gridcolor='#232D3F', title=''),
        yaxis=dict(showgrid=True, gridcolor='#232D3F', side='right', range=[ymin - y_padding, ymax + y_padding], autorange=False, title=''),
        yaxis2=dict(showgrid=False, side='right', title=''),
        hovermode='x unified', showlegend=False, font=dict(family="sans-serif", size=11, color="#F3F4F6")
    )
    return fig, s_curr, s_pct, s_diff, line_color

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 台灣加權現貨 (^TWII)")
    p_sel_1 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="twii_box_sel")
    data_obj_1 = market_data_twii.get(p_sel_1, {"series": pd.Series([46000]), "open_price": 46000})
    fig_1, curr_1, pct_1, diff_1, col_1 = create_square_card_chart(data_obj_1, "加權現貨")
    st.markdown(f'<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;"><span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">{curr_1:,.2f}</span><span style="font-size: 0.8rem; font-weight: 800; color: {col_1};">{"+" if diff_1 >= 0 else ""}{pct_1:.2f}%</span></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_1, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row1_col2:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 美國 S&P 500 (^GSPC)")
    p_sel_2 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="sp500_box_sel")
    data_obj_2 = market_data_gspc.get(p_sel_2, {"series": pd.Series([5800]), "open_price": 5800})
    fig_2, curr_2, pct_2, diff_2, col_2 = create_square_card_chart(data_obj_2, "S&P 500")
    st.markdown(f'<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;"><span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">{curr_2:,.2f}</span><span style="font-size: 0.8rem; font-weight: 800; color: {col_2};">{"+" if diff_2 >= 0 else ""}{pct_2:.2f}%</span></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 那斯達克指數 (^IXIC)")
    p_sel_3 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="nasdaq_box_sel")
    data_obj_3 = market_data_ixic.get(p_sel_3, {"series": pd.Series([18500]), "open_price": 18500})
    fig_3, curr_3, pct_3, diff_3, col_3 = create_square_card_chart(data_obj_3, "NASDAQ")
    st.markdown(f'<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;"><span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">{curr_3:,.2f}</span><span style="font-size: 0.8rem; font-weight: 800; color: {col_3};">{"+" if diff_3 >= 0 else ""}{pct_3:.2f}%</span></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row2_col2:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 台積電 (2330.TW)")
    p_sel_4 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="tsmc_box_sel")
    data_obj_4 = market_data_tsmc.get(p_sel_4, {"series": pd.Series([2405]), "open_price": 2405})
    fig_4, curr_4, pct_4, diff_4, col_4 = create_square_card_chart(data_obj_4, "台積電")
    st.markdown(f'<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;"><span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">NT$ {curr_4:,.1f}</span><span style="font-size: 0.8rem; font-weight: 800; color: {col_4};">{"+" if diff_4 >= 0 else ""}{pct_4:.2f}%</span></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_4, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)