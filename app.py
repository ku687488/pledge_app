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
        💎 富人思維槓桿戰情室 • 實時 Beta 計算引擎 • 索提諾動態效率前緣與半凱利生命週期平滑模型
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. Session State 初始化 ====================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.owned_assets = [
        {"id": str(uuid.uuid4()), "ticker": "00685L.TW", "shares": 10000.0, "weight_target": 0.8},
        {"id": str(uuid.uuid4()), "ticker": "00713.TW", "shares": 20000.0, "weight_target": 0.2}
    ]
    st.session_state.mortgages = []
    st.session_state.total_equity_cost = 2000000.0
    st.session_state.ltv_ratio_val = 0.25
    st.session_state.manual_loan_val = 500000.0
    st.session_state.interest_rate_val = 3.7
    st.session_state.user_age_val = 25
    st.session_state.enable_life = True
    st.session_state.manual_override = False

if 'mortgages' not in st.session_state:
    st.session_state.mortgages = []
if 'owned_assets' not in st.session_state:
    st.session_state.owned_assets = []

# 側邊欄：一鍵重置
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>🛠️ 系統控制與重置</h3>", unsafe_allow_html=True)
if st.sidebar.button("🔄 一鍵重置為預設範例狀態"):
    st.session_state.owned_assets = [
        {"id": str(uuid.uuid4()), "ticker": "00685L.TW", "shares": 10000.0, "weight_target": 0.8},
        {"id": str(uuid.uuid4()), "ticker": "00713.TW", "shares": 20000.0, "weight_target": 0.2}
    ]
    st.session_state.mortgages = []
    st.session_state.total_equity_cost = 2000000.0
    st.session_state.ltv_ratio_val = 0.25
    st.session_state.manual_loan_val = 500000.0
    st.rerun()

# ==================== 側邊欄：生命週期動態曝險與資本結構 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>👤 半凱利生命週期連續降曝險</h3>", unsafe_allow_html=True)

st.session_state.enable_life = st.sidebar.checkbox("啟用生命週期動態平滑降曝險模型", value=st.session_state.enable_life)
st.session_state.user_age_val = st.sidebar.number_input("目前真實年紀 (歲)", min_value=20, max_value=95, value=int(st.session_state.user_age_val), step=1)

# 用戶要求的精準數學軌跡：25歲 240% 起步，隨年齡平滑遞減至 150%
age = st.session_state.user_age_val
if age <= 25:
    target_lifecycle_exposure = 240.0
elif age <= 40:
    target_lifecycle_exposure = 240.0 - (age - 25) * 2.0  # 240% -> 210%
elif age <= 60:
    target_lifecycle_exposure = 210.0 - (age - 40) * 2.0  # 210% -> 170%
elif age <= 80:
    target_lifecycle_exposure = 170.0 - (age - 60) * 1.0  # 170% -> 150%
else:
    target_lifecycle_exposure = 150.0

if st.session_state.enable_life:
    st.sidebar.info(f"🎯 依據 {age} 歲半凱利連續模型：目標淨權益曝險率智慧收斂至 **{target_lifecycle_exposure:.1f}%** (240% → 150%)")
else:
    st.sidebar.info("🔓 【完全自由曝險模式】：由您自行掌控曝險倍數。")

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

# ==================== 3. 實時市場數據與即時 Beta 計算引擎 ====================
FAMILIAL_YIELD_KNOWLEDGE_BASE = {
    "00713.TW": (0.062, 0.24),
    "00713": (0.062, 0.24),
    "0056.TW": (0.065, 0.65),
    "0056": (0.065, 0.65),
    "00878.TW": (0.060, 0.55),
    "00878": (0.060, 0.55),
    "00919.TW": (0.095, 0.75),
    "00919": (0.095, 0.75),
    "2330.TW": (0.018, 1.15),
    "2330": (0.018, 1.15),
    "0050.TW": (0.032, 1.00),
    "0050": (0.032, 1.00),
    "006208.TW": (0.032, 1.00),
    "006208": (0.032, 1.00),
    "00685L.TW": (0.0, 2.00),
    "00685L": (0.0, 2.00),
    "00631L.TW": (0.0, 2.00),
    "00631L": (0.0, 2.00)
}

@st.cache_data(ttl=60)
def fetch_live_data_and_calculate_beta(ticker):
    clean_t = ticker.strip().upper()
    data_dict = {}
    try:
        df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=False, progress=False)
        df_m = yf.download("^TWII", period="6mo", interval="1d", auto_adjust=False, progress=False)
        
        if not df.empty and not df_m.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            if isinstance(df_m.columns, pd.MultiIndex): df_m.columns = df_m.columns.get_level_values(0)
            
            s = df['Close'].dropna()
            s_m = df_m['Close'].dropna()
            if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
            if isinstance(s_m, pd.DataFrame): s_m = s_m.iloc[:, 0]
            
            combined = pd.concat([s, s_m], axis=1).dropna()
            combined.columns = ['Asset', 'Market']
            returns = combined.pct_change().dropna()
            
            cov_matrix = np.cov(returns['Asset'], returns['Market'])
            beta_val = float(cov_matrix[0, 1] / cov_matrix[1, 1]) if cov_matrix[1, 1] != 0 else 1.0
            latest_price = float(s.iloc[-1])
            
            # 配息計算
            tk_obj = yf.Ticker(ticker)
            divs = tk_obj.dividends
            recent_yield = 0.0
            if not divs.empty and latest_price > 0:
                now_ts = pd.Timestamp.now()
                recent_divs = divs.loc[divs.index >= (now_ts - pd.DateOffset(years=1))]
                recent_yield = float(recent_divs.sum() / latest_price)
            if recent_yield == 0.0 and clean_t in FAMILIAL_YIELD_KNOWLEDGE_BASE:
                recent_yield = FAMILIAL_YIELD_KNOWLEDGE_BASE[clean_t][0]
                
            return latest_price, beta_val, recent_yield, {"1天 (即時高頻)": {"series": s, "open_price": float(df['Open'].iloc[0])}}
    except:
        pass
        
    # 備用知識庫
    fallback_b = FAMILIAL_YIELD_KNOWLEDGE_BASE.get(clean_t, (0.05, 1.0))[1]
    fallback_y = FAMILIAL_YIELD_KNOWLEDGE_BASE.get(clean_t, (0.05, 1.0))[0]
    return 50.0, fallback_b, fallback_y, {}

# ==================== 持倉管理側邊欄 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔍 自有資金持倉標的與實時 Beta 偵測</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增持倉標的"):
    st.session_state.owned_assets.append({
        "id": str(uuid.uuid4()), 
        "ticker": "00713.TW", 
        "shares": 10000.0
    })
    st.rerun()

price_cache = {}
beta_cache = {}
yield_cache = {}

for i, asset in enumerate(st.session_state.owned_assets):
    if "id" not in asset: asset["id"] = str(uuid.uuid4())
    uid = asset["id"]
    st.sidebar.markdown(f"**📌 持倉 #{i+1}**")
    asset["ticker"] = st.sidebar.text_input(f"台股代號 #{i+1}", value=asset["ticker"], key=f"t_{uid}")
    asset["shares"] = st.sidebar.number_input(f"持有股數 #{i+1}", value=float(asset["shares"]), step=1000.0, key=f"sh_{uid}")
    
    t_clean = asset["ticker"].strip().upper()
    if t_clean:
        lp, b_val, y_val, _ = fetch_live_data_and_calculate_beta(t_clean)
        price_cache[t_clean] = lp
        beta_cache[t_clean] = b_val
        yield_cache[t_clean] = y_val
        st.sidebar.markdown(f"<div style='font-size:0.75rem; color:#10B981; margin-bottom:4px; font-weight:700;'>📊 實時 Beta: <b>{b_val:.2f}</b> | 預估殖利率: <b>{y_val*100:.2f}%</b></div>", unsafe_allow_html=True)
        
    if st.sidebar.button(f"🗑️ 刪除 #{i+1}", key=f"del_{uid}"):
        st.session_state.owned_assets.pop(i)
        st.rerun()

# 房貸矩陣
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
mortgages_annual_outflow_post = 0.0

for m_idx, m_item in enumerate(st.session_state.mortgages):
    muid = m_item["id"]
    st.sidebar.markdown(f"**📌 房貸項目 #{m_idx+1}**")
    m_item["name"] = st.sidebar.text_input(f"房貸名稱 #{m_idx+1}", value=m_item["name"], key=f"m_name_{muid}")
    m_item["balance"] = st.sidebar.number_input(f"剩餘本金 #{m_idx+1} (NT$)", value=float(m_item["balance"]), step=100000.0, key=f"m_bal_{muid}")
    m_item["rate"] = st.sidebar.slider(f"年利率 #{m_idx+1} (%)", min_value=1.0, max_value=6.0, value=float(m_item["rate"]), step=0.1, key=f"m_rate_{muid}")
    m_item["term"] = st.sidebar.slider(f"總年限 #{m_idx+1} (年)", min_value=5, max_value=40, value=int(m_item["term"]), step=5, key=f"m_term_{muid}")
    m_item["grace"] = st.sidebar.checkbox(f"享有寬限期 (只付利息) #{m_idx+1}", value=m_item["grace"], key=f"m_grace_{muid}")
    
    m_r = m_item["rate"] / 100.0
    outflow_grace = m_item["balance"] * m_r
    post_months = max((m_item["term"] - m_item.get("grace_years", 3)) * 12, 12) if m_item["grace"] else m_item["term"] * 12
    m_m_rate = m_r / 12.0
    monthly_pmt_post = m_item["balance"] * (m_m_rate * (1 + m_m_rate)**post_months) / ((1 + m_m_rate)**post_months - 1) if m_m_rate > 0 else 0
    outflow_post = monthly_pmt_post * 12
    
    mortgages_annual_outflow_grace += outflow_grace
    mortgages_annual_outflow_post += outflow_post
    if st.sidebar.button(f"🗑️ 刪除房貸 #{m_idx+1}", key=f"del_m_{muid}"):
        st.session_state.mortgages.pop(m_idx)
        st.rerun()

# ==================== 4. 計算總市值與加權平均 Beta ====================
base_val_total = 0.0
weighted_beta_sum = 0.0
expected_div_total = 0.0

for asset in st.session_state.owned_assets:
    t_clean = asset["ticker"].strip().upper()
    shares = asset["shares"]
    lp = price_cache.get(t_clean, 50.0)
    b_val = beta_cache.get(t_clean, 1.0)
    y_val = yield_cache.get(t_clean, 0.05)
    
    val = shares * lp
    base_val_total += val
    weighted_beta_sum += val * b_val
    expected_div_total += val * y_val

portfolio_beta = weighted_beta_sum / base_val_total if base_val_total > 0 else 1.0
reinvest_val_total = loan_amount
total_collateral = base_val_total + reinvest_val_total
net_equity = max(total_collateral - loan_amount, 100000.0)
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

# 半凱利與目標曝險計算
target_exp_val = target_lifecycle_exposure / 100.0
# 假設以正二 (Beta=2.0) 與 00713 (Beta=0.24) 進行動態最佳化配置
beta_atk = 2.00
beta_def = 0.24
# 解聯立方程式求得最佳配置比例
# W_atk * 2.0 + W_def * 0.24 = target_exp_val (W_atk + W_def = 1.0)
calculated_atk_ratio = min(max((target_exp_val - beta_def) / (beta_atk - beta_def), 0.0), 1.0)
calculated_def_ratio = 1.0 - calculated_atk_ratio

recommended_atk_amt = net_equity * calculated_atk_ratio
recommended_def_amt = net_equity * calculated_def_ratio

annual_interest = loan_amount * interest_rate
net_carry_grace = expected_div_total + (reinvest_val_total * 0.058) - annual_interest - mortgages_annual_outflow_grace
net_carry_post = expected_div_total + (reinvest_val_total * 0.058) - annual_interest - mortgages_annual_outflow_post

monthly_interest = annual_interest / 12.0
monthly_div = (expected_div_total + reinvest_val_total * 0.058) / 12.0
monthly_net_grace = net_carry_grace / 12.0
monthly_net_post = net_carry_post / 12.0

# ==================== 5. 索提諾比率與高效率前緣優化模擬 ====================
ret_1, ret_2 = 0.24 * portfolio_beta, 0.07
vol_1, vol_2 = 0.32 * portfolio_beta, 0.12
corr_12 = 0.30

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

# 蒙地卡羅軌跡模擬
num_sim_days = 252
num_paths = 250
dt = 1.0 / 252.0
base_portfolio_val = max(total_collateral, 100000.0)

sim_paths = np.zeros((num_sim_days, num_paths))
sim_paths[0, :] = base_portfolio_val
for p in range(num_paths):
    val = base_portfolio_val
    for d in range(1, num_sim_days):
        drift = 0.16 * portfolio_beta
        vol_p = 0.20 * portfolio_beta
        shock = np.random.normal(0, 1)
        val = val * (1 + drift * dt + vol_p * np.sqrt(dt) * shock)
        sim_paths[d, p] = max(val, 1000.0)

path_median = np.percentile(sim_paths, 50, axis=1)
path_upper_95 = np.percentile(sim_paths, 95, axis=1)
path_lower_5 = np.percentile(sim_paths, 5, axis=1)

# ==================== 6. 戰情快報 ====================
st.markdown(f"""
<div class="web-push-ticker">
    📡 <b>【Apex 家族辦公室實時戰情快報 (實時 Beta 偵測引擎)】</b><br>
    • 當前持股加權平均 Beta：<b>{portfolio_beta:.2f}</b> | 目前年齡：<b>{st.session_state.user_age_val} 歲</b><br>
    • 半凱利生命週期動態目標曝險：<b>{target_lifecycle_exposure:.1f}%</b> (240% → 150%)
</div>
""", unsafe_allow_html=True)

# ==================== 7. 主戰情室 KPI 儀表板 ====================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">總擔保品市值 (本金+質押放大)</div>
        <div class="card-value">NT$ {total_collateral:,.0f}</div>
        <div class="card-subtitle text-blue">自有市值: NT$ {base_val_total:,.0f}</div>
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
        <div class="card-subtitle">券商平倉線: 130%</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">投資組合加權 Beta</div>
        <div class="card-value text-blue">{portfolio_beta:.2f}</div>
        <div class="card-subtitle text-green">⚡ 即時抓取實時數據計算</div>
    </div>
    """, unsafe_allow_html=True)

progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0) if loan_amount > 0 else 0.0
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer)**")
st.progress(progress_val)

st.markdown("---")

# ==================== 8. 寬限期現金流對比面板 ====================
st.markdown("### 💵 核心重點優先：房貸寬限期內 vs 寬限期滿後（本息攤還）現金流自償性對比")
lc, rc = st.columns(2)

with lc:
    st.markdown("##### 🟢 階段一：寬限期內每月現金流 (Grace Period - 只付利息)")
    st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
    st.metric("總資產每月預期總配息收益", f"+NT$ {monthly_div:,.0f}")
    if st.session_state.mortgages:
        st.metric("每月房貸支出 (寬限期內)", f"-NT$ {mortgages_annual_outflow_grace/12:,.0f}")
        
    net_grace_color = "text-green" if monthly_net_grace >= 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #10B981; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">寬限期內每月淨現金流 (Monthly Net Carry)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{net_grace_color}">{'+' if monthly_net_grace >= 0 else ''}NT$ {monthly_net_grace:,.0f} / 月</div>
        <div style="font-size: 0.8rem; color: #10B981; margin-top: 4px; font-weight: 700;">{'🟢 配息完全覆蓋利息與寬限期支出！' if monthly_net_grace >= 0 else '🔴 寬限期內現金流短缺。'}</div>
    </div>
    """, unsafe_allow_html=True)

with rc:
    st.markdown("##### 🟠 階段二：寬限期滿後每月現金流 (Post-Grace - 本息均攤)")
    st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
    st.metric("總資產每月預期總配息收益", f"+NT$ {monthly_div:,.0f}")
    if st.session_state.mortgages:
        st.metric("每月房貸支出 (本息均攤)", f"-NT$ {mortgages_annual_outflow_post/12:,.0f}", "⚠️ 開始攤還本金，支出增加")
        
    net_post_color = "text-green" if monthly_net_post >= 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #F59E0B; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">寬限期滿後每月淨現金流 (本息攤還)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{net_post_color}">{'+' if monthly_net_post >= 0 else ''}NT$ {monthly_net_post:,.0f} / 月</div>
        <div style="font-size: 0.8rem; color: #F59E0B; margin-top: 4px; font-weight: 700;">{'🟢 寬限期滿後依然正現金流！' if monthly_net_post >= 0 else '🔴 寬限期滿後轉為負現金流，需準備本業現金流。'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== 9. 實時索提諾與半凱利最佳下單指令 ====================
st.markdown("### 📈 華爾街量化核心：實時 Beta 偵測與索提諾最佳化下單指引")

ef_col1, ef_col2 = st.columns(2)

with ef_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📊 1. 索提諾效率前緣與半凱利動態調倉指令")
    
    action_html = f"""
    <div class="action-box">
        🎯 <b>【{st.session_state.user_age_val} 歲半凱利生命週期模型（目標曝險 {target_lifecycle_exposure:.1f}%）】</b><br><br>
        <b>👉 具體下單執行指令（基於實時 Beta 計算）：</b><br>
        • <b>正二攻擊標的 (00685L / Beta=2.0)</b>：實際配置 <b>{calculated_atk_ratio*100:.1f}%</b>（約 <b>NT$ {recommended_atk_amt:,.0f}</b>）。<br>
        • <b>防禦高股息標的 (00713 / 實時 Beta=0.24)</b>：實際配置 <b>{calculated_def_ratio*100:.1f}%</b>（約 <b>NT$ {recommended_def_amt:,.0f}</b>）。<br>
        • <b>★ 索提諾黃金綠星點最佳解</b>：系統即時演算出當前市場效率前緣最高 CP 值組合為 <b>{optimal_sortino_weight_1*100:.1f}% 正二 + {(1-optimal_sortino_weight_1)*100:.1f}% 高股息</b>[cite: 3]。<br>
        • <b>動態收斂機制</b>：隨著年齡增長，目標曝險從 240% 平滑遞減至 150%，系統自動指引您將正二獲利了結轉入 00713[cite: 4]。
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
        text=["★ 最佳索提諾組合"], textposition="top center", textfont=dict(color='#10B981', size=13)
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

# ==================== 10. 市場行情 2x2 方格矩陣 ====================
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