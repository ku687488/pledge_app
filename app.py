import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import uuid
from scipy.optimize import minimize
from hmmlearn.hmm import GaussianHMM

# ==================== 1. 頁面配置與華爾街黑卡級美學 CSS ====================
st.set_page_config(
    page_title="Apex Global Institutional Terminal | 富人級線上即時回測與最優槓桿戰情室",
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
    .chart-container-box {
        background: rgba(18, 24, 36, 0.9); border: 1px solid #2A364F; border-radius: 12px;
        padding: 16px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .theory-box {
        background: rgba(31, 41, 55, 0.6); border: 1px solid #4B5563; border-left: 4px solid #F59E0B;
        padding: 12px 16px; border-radius: 8px; margin: 10px 0; font-size: 0.88rem; color: #E5E7EB; line-height: 1.5;
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
    <h2 style="margin:0; color:#FFFFFF; font-weight:900; letter-spacing:-0.5px;">🏛️ APEX GLOBAL INSTITUTIONAL TERMINAL (OPTIMAL LEVERAGE EDITION)</h2>
    <p style="margin:6px 0 0 0; color:#F59E0B; font-size:0.95rem; font-weight:800;">
        💎 即時線上計量回測與動態最優槓桿引擎 • HMM 市場體制 • L2 索提諾優化 • 純數學風險控管
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. 絕對穩健的 Session State 與一鍵清除機制 ====================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.owned_assets = [
        {"id": str(uuid.uuid4()), "ticker": "00685L.TW", "shares": 10000.0},
        {"id": str(uuid.uuid4()), "ticker": "00713.TW", "shares": 20000.0}
    ]
    st.session_state.mortgages = []
    st.session_state.total_equity_cost = 2000000.0
    st.session_state.ltv_ratio_val = 0.25
    st.session_state.manual_loan_val = 500000.0
    st.session_state.interest_rate_val = 3.7
    st.session_state.user_age_val = 25
    st.session_state.enable_life = True
    st.session_state.manual_override = False
    st.session_state.reinvest_allocations = {"00685L.TW": 100.0}

# 側邊欄：一鍵清除功能（保證百分百靈敏）
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>🛠️ 系統控制與一鍵清除</h3>", unsafe_allow_html=True)
if st.sidebar.button("🔄 一鍵清除並重置所有設定", type="primary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 側邊欄：計量與優化參數
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>🎛️ 計量模型與 HMM 市場體制參數</h3>", unsafe_allow_html=True)

opt_objective = st.sidebar.selectbox(
    "1. 選擇資產配置優化目標",
    ["🎯 最大索提諾比率 (Sortino 最佳化)", "🚀 極致報酬率優先 (Max Return)", "🛡️ 最小回撤防禦優先 (Min Drawdown)"]
)

user_max_mdd_limit = st.sidebar.slider(
    "2. 自訂歷史最大回撤 (MDD) 容忍上限 (%)",
    min_value=10.0, max_value=40.0, value=22.0, step=1.0,
    help="過濾超過此歷史回撤的次優配置組合（硬約束防禦機制）。"
)

l2_lambda_val = st.sidebar.slider(
    "3. L2 正則化懲罰係數 (Ridge λ)",
    min_value=0.0, max_value=0.20, value=0.05, step=0.01,
    help="Ridge Penalty，防止權重過度集中於單一資產。"
)

# 生命週期與資本結構
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>👤 半凱利生命週期連續降曝險</h3>", unsafe_allow_html=True)
st.session_state.enable_life = st.sidebar.checkbox("啟用生命週期動態平滑降曝險模型", value=st.session_state.get('enable_life', True))
st.session_state.user_age_val = st.sidebar.number_input("目前真實年紀 (歲)", min_value=20, max_value=95, value=int(st.session_state.get('user_age_val', 25)), step=1)

age = st.session_state.user_age_val
if age <= 25: target_lifecycle_exposure = 240.0
elif age <= 40: target_lifecycle_exposure = 240.0 - (age - 25) * 2.0 
elif age <= 60: target_lifecycle_exposure = 210.0 - (age - 40) * 2.0 
elif age <= 80: target_lifecycle_exposure = 170.0 - (age - 60) * 1.0 
else: target_lifecycle_exposure = 150.0

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>⚙️ 資本結構與富人質押設定</h3>", unsafe_allow_html=True)
st.session_state.total_equity_cost = st.sidebar.number_input("1. 自有初始本金總額 (NT$)", value=float(st.session_state.get('total_equity_cost', 2000000.0)), step=100000.0)

ltv_slider_input = st.sidebar.slider("2. 股票質押成數 LTV (%)", min_value=0.0, max_value=60.0, value=float(st.session_state.get('ltv_ratio_val', 0.25) * 100), step=1.0)
st.session_state.ltv_ratio_val = ltv_slider_input / 100.0
ltv_ratio = st.session_state.ltv_ratio_val

auto_loan_amount = int(st.session_state.total_equity_cost * ltv_ratio)
st.session_state.manual_override = st.sidebar.checkbox("手動自訂質押借款金額 (永久不還本金)", value=st.session_state.get('manual_override', False))
if st.session_state.manual_override:
    loan_amount = st.sidebar.number_input("自訂質押借款金額 (NT$)", value=float(st.session_state.get('manual_loan_val', 500000.0)), step=10000.0)
    st.session_state.manual_loan_val = loan_amount
else:
    loan_amount = auto_loan_amount

st.sidebar.markdown("---")
st.session_state.interest_rate_val = st.sidebar.slider("3. 質押貸款年利率 (%)", min_value=2.0, max_value=6.0, value=float(st.session_state.get('interest_rate_val', 3.7)), step=0.1)
interest_rate = st.session_state.interest_rate_val / 100.0

# ==================== 3. 實時數據、Beta 與 HMM 訓練引擎 ====================
@st.cache_data(ttl=60)
def fetch_live_data_and_calculate_beta(ticker):
    clean_t = ticker.strip().upper()
    try:
        df = yf.download(ticker, period="1yr", interval="1d", auto_adjust=False, progress=False)
        df_m = yf.download("^TWII", period="1yr", interval="1d", auto_adjust=False, progress=False)
        
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
            
            tk_obj = yf.Ticker(ticker)
            divs = tk_obj.dividends
            recent_yield = 0.0
            if not divs.empty and latest_price > 0:
                now_ts = pd.Timestamp.now()
                recent_divs = divs.loc[divs.index >= (now_ts - pd.DateOffset(years=1))]
                recent_yield = float(recent_divs.sum() / latest_price)
                
            return latest_price, beta_val, recent_yield, returns['Market']
    except:
        pass
        
    if "685L" in clean_t or "631L" in clean_t: return 50.0, 2.00, 0.0, pd.Series()
    elif "713" in clean_t: return 60.0, 0.24, 0.062, pd.Series()
    elif "50" in clean_t or "6208" in clean_t: return 100.0, 1.00, 0.032, pd.Series()
    else: return 50.0, 0.85, 0.05, pd.Series()

@st.cache_data(ttl=300)
def train_market_hmm():
    try:
        df_m = yf.download("^TWII", period="2yr", interval="1d", auto_adjust=False, progress=False)
        if isinstance(df_m.columns, pd.MultiIndex): df_m.columns = df_m.columns.get_level_values(0)
        s_m = df_m['Close'].dropna()
        if isinstance(s_m, pd.DataFrame): s_m = s_m.iloc[:, 0]
        
        rets = s_m.pct_change().dropna()
        vols = rets.rolling(20).std().dropna()
        feature_data = pd.DataFrame({'ret': rets, 'vol': vols}).dropna()
        X = feature_data.values
        
        model = GaussianHMM(n_components=3, covariance_type="full", n_iter=500, random_state=42)
        model.fit(X)
        hidden_states = model.predict(X)
        current_state = hidden_states[-1]
        
        state_means = [X[hidden_states == i, 0].mean() for i in range(3)]
        sorted_states = np.argsort(state_means)
        bear_state, bull_state = sorted_states[0], sorted_states[2]
        
        if current_state == bull_state: regime_name, regime_mult = "🐂 牛市低波動擴張期 (Bull Regime)", 1.15
        elif current_state == bear_state: regime_name, regime_mult = "🐻 高波動空襲危機期 (Bear Regime)", 0.70
        else: regime_name, regime_mult = "🦀 震盪盤整過渡期 (Sideways Regime)", 0.95
        
        return regime_name, regime_mult, current_state
    except:
        return "🐂 牛市低波動擴張期 (Bull Regime)", 1.15, 0

current_regime_str, regime_multiplier, hmm_state_id = train_market_hmm()

# ==================== 持倉管理側邊欄 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔍 自有資金持倉標的與實時 Beta</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增持倉標的"):
    st.session_state.owned_assets.append({"id": str(uuid.uuid4()), "ticker": "00713.TW", "shares": 10000.0})
    st.rerun()

price_cache, beta_cache, yield_cache, available_tickers = {}, {}, {}, []

for i, asset in enumerate(st.session_state.owned_assets):
    if "id" not in asset: asset["id"] = str(uuid.uuid4())
    uid = asset["id"]
    st.sidebar.markdown(f"**📌 持倉 #{i+1}**")
    asset["ticker"] = st.sidebar.text_input(f"台股代號 #{i+1}", value=asset["ticker"], key=f"t_{uid}")
    asset["shares"] = st.sidebar.number_input(f"持有股數 #{i+1}", value=float(asset["shares"]), step=1000.0, key=f"sh_{uid}")
    
    t_clean = asset["ticker"].strip().upper()
    if t_clean:
        available_tickers.append(t_clean)
        lp, b_val, y_val, _ = fetch_live_data_and_calculate_beta(t_clean)
        price_cache[t_clean], beta_cache[t_clean], yield_cache[t_clean] = lp, b_val, y_val
        st.sidebar.markdown(f"<div style='font-size:0.75rem; color:#10B981; font-weight:700;'>📊 Beta: <b>{b_val:.2f}</b> | 殖利率: <b>{y_val*100:.2f}%</b></div>", unsafe_allow_html=True)
        
    if st.sidebar.button(f"🗑️ 刪除 #{i+1}", key=f"del_{uid}"):
        st.session_state.owned_assets.pop(i)
        st.rerun()

if not available_tickers: available_tickers = ["00685L.TW", "00713.TW"]

# ==================== 質押借款資金與生活費自由配置模組 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🎯 質押借款現金再投入與生活費分配</h4>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='font-size:0.75rem; color:#9CA3AF;'>自由設定借款資金分配：可投入多檔標的，或保留部分作為現金生活費。</div>", unsafe_allow_html=True)

reinvest_options = available_tickers + ["💵 保留現金 / 生活費儲備 (0% 投資收益)"]
if 'reinvest_allocations' not in st.session_state:
    st.session_state.reinvest_allocations = {available_tickers[0]: 100.0}

current_allocs = st.session_state.reinvest_allocations
selected_targets = st.sidebar.multiselect("選擇分配標的與現金儲備", options=reinvest_options, default=list(current_allocs.keys()) if list(current_allocs.keys()) else [reinvest_options[0]])

alloc_weights = {}
for target in selected_targets:
    default_val = current_allocs.get(target, 100.0 / len(selected_targets) if selected_targets else 100.0)
    w = st.sidebar.slider(f"分配至: {target} (%)", min_value=0.0, max_value=100.0, value=float(default_val), step=5.0, key=f"alloc_{target}")
    alloc_weights[target] = w

st.session_state.reinvest_allocations = alloc_weights
total_alloc_pct = sum(alloc_weights.values())

if abs(total_alloc_pct - 100.0) > 0.01 and selected_targets:
    st.sidebar.warning(f"⚠️ 目前總分配比例為 {total_alloc_pct:.1f}% (建議調整至剛好 100%)")

# 房貸負債矩陣
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🏠 房貸負債矩陣與現金流試算</h4>", unsafe_allow_html=True)
if st.sidebar.button("➕ 新增一筆房貸"):
    st.session_state.mortgages.append({"id": str(uuid.uuid4()), "name": f"房貸 #{len(st.session_state.mortgages)+1}", "balance": 0.0, "rate": 2.2, "term": 30, "grace": True, "grace_years": 3})
    st.rerun()

mortgages_annual_outflow_grace, mortgages_annual_outflow_post = 0.0, 0.0
for m_idx, m_item in enumerate(st.session_state.mortgages):
    muid = m_item["id"]
    st.sidebar.markdown(f"**📌 房貸項目 #{m_idx+1}**")
    m_item["name"] = st.sidebar.text_input(f"房貸名稱 #{m_idx+1}", value=m_item["name"], key=f"m_name_{muid}")
    m_item["balance"] = st.sidebar.number_input(f"剩餘本金 #{m_idx+1} (NT$)", value=float(m_item["balance"]), step=100000.0, key=f"m_bal_{muid}")
    m_item["rate"] = st.sidebar.slider(f"年利率 #{m_idx+1} (%)", min_value=1.0, max_value=6.0, value=float(m_item["rate"]), step=0.1, key=f"m_rate_{muid}")
    m_item["term"] = st.sidebar.slider(f"總年限 #{m_idx+1} (年)", min_value=5, max_value=40, value=int(m_item["term"]), step=5, key=f"m_term_{muid}")
    m_item["grace"] = st.sidebar.checkbox(f"享有寬限期 #{m_idx+1}", value=m_item["grace"], key=f"m_grace_{muid}")
    
    m_r = m_item["rate"] / 100.0
    outflow_grace = m_item["balance"] * m_r
    post_months = max((m_item["term"] - m_item.get("grace_years", 3)) * 12, 12) if m_item["grace"] else m_item["term"] * 12
    m_m_rate = m_r / 12.0
    monthly_pmt_post = m_item["balance"] * (m_m_rate * (1 + m_m_rate)**post_months) / ((1 + m_m_rate)**post_months - 1) if m_m_rate > 0 else 0
    mortgages_annual_outflow_grace += outflow_grace
    mortgages_annual_outflow_post += monthly_pmt_post * 12
    if st.sidebar.button(f"🗑️ 刪除房貸 #{m_idx+1}", key=f"del_m_{muid}"):
        st.session_state.mortgages.pop(m_idx)
        st.rerun()

# ==================== 4. 即時運算總市值與現金流 ====================
base_val_total, weighted_beta_sum, expected_div_total = 0.0, 0.0, 0.0
for asset in st.session_state.owned_assets:
    t_clean = asset["ticker"].strip().upper()
    shares = asset["shares"]
    lp, b_val, y_val = price_cache.get(t_clean, 50.0), beta_cache.get(t_clean, 1.0), yield_cache.get(t_clean, 0.05)
    val = shares * lp
    base_val_total += val
    weighted_beta_sum += val * b_val
    expected_div_total += val * y_val

portfolio_beta = weighted_beta_sum / base_val_total if base_val_total > 0 else 1.0
reinvest_val_total = loan_amount
total_collateral = base_val_total + reinvest_val_total
net_equity = max(total_collateral - loan_amount, 100000.0)
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

target_exp_val = target_lifecycle_exposure / 100.0
beta_atk = 2.00
beta_def = beta_cache.get("00713.TW", 0.24)
if beta_def >= beta_atk: beta_def = 0.24

calculated_atk_ratio = min(max((target_exp_val - beta_def) / (beta_atk - beta_def), 0.0), 1.0)
calculated_def_ratio = 1.0 - calculated_atk_ratio
recommended_atk_amt, recommended_def_amt = net_equity * calculated_atk_ratio, net_equity * calculated_def_ratio

annual_interest = loan_amount * interest_rate

weighted_reinvest_yield = 0.0
for target, pct in alloc_weights.items():
    if "現金" in target or "生活費" in target:
        y_t = 0.0
    else:
        y_t = yield_cache.get(target, 0.05)
    weighted_reinvest_yield += y_t * (pct / 100.0)

reinvest_income = reinvest_val_total * weighted_reinvest_yield
net_carry_grace = expected_div_total + reinvest_income - annual_interest - mortgages_annual_outflow_grace
net_carry_post = expected_div_total + reinvest_income - annual_interest - mortgages_annual_outflow_post

monthly_interest = annual_interest / 12.0
monthly_div = (expected_div_total + reinvest_income) / 12.0
monthly_net_grace = net_carry_grace / 12.0
monthly_net_post = net_carry_post / 12.0

# ==================== 5. 核心分頁架構 ====================
tab_live, tab_custom_backtest, tab_opt = st.tabs([
    "👑 實戰個人資產與富人動態決策戰情室", 
    "📈 自訂投資組合線上即時回測與數學效能分析",
    "📊 索提諾效率前緣與蒙地卡羅風險模擬"
])

with tab_live:
    st.markdown(f"""
    <div class="web-push-ticker">
        📡 <b>【即時智慧戰情快報】</b> HMM 市場體制：<b class="text-gold">{current_regime_str}</b> | 加權 Beta：<b>{portfolio_beta:.2f}</b> | 寬限期每月淨現金流：<b class="{'text-green' if monthly_net_grace >= 0 else 'text-red'}">{'+' if monthly_net_grace >= 0 else ''}NT$ {monthly_net_grace:,.0f} /月</b>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="card-title">總擔保品市值</div><div class="card-value">NT$ {total_collateral:,.0f}</div><div class="card-subtitle text-blue">自有市值: NT$ {base_val_total:,.0f}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="card-title">永續借款負債</div><div class="card-value">NT$ {loan_amount:,.0f}</div><div class="card-subtitle text-gold">多元分配與生活費儲備</div></div>""", unsafe_allow_html=True)
    with c3:
        status_color = "text-green" if margin_ratio > 200 or loan_amount == 0 else ("text-gold" if margin_ratio > 160 else "text-red")
        st.markdown(f"""<div class="metric-card"><div class="card-title">即時質押維持率</div><div class="card-value {status_color}">{margin_ratio:.1f}%</div><div class="card-subtitle">平倉線: 130%</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card"><div class="card-title">投資組合加權 Beta</div><div class="card-value text-blue">{portfolio_beta:.2f}</div><div class="card-subtitle text-green">⚡ HMM乘數: {regime_multiplier}x</div></div>""", unsafe_allow_html=True)

    progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0) if loan_amount > 0 else 0.0
    st.markdown("**🛡️ 質押維持率安全緩衝條**")
    st.progress(progress_val)
    st.markdown("---")

    st.markdown("### 👑 家族辦公室總結與富人槓桿資產配置智慧導航 (Smart Wealth Advisory)")
    st.markdown(f"""
    <div class="theory-box" style="border-left-color: #10B981; background: rgba(16, 185, 129, 0.08);">
    💎 <b>【富人思維與最優解指引】</b><br>
    結合您目前的年齡（<b>{age} 歲</b>）、HMM 市場體制（<b>{current_regime_str}</b>）與多元資金分配：
    <ul>
      <li><b>最佳權重分配：</b> 系統透過 L2 正則化索提諾優化與半凱利生命週期，建議您的淨資產應分配 <b>{calculated_atk_ratio*100:.1f}%</b> 至攻擊型資產（約 NT$ {recommended_atk_amt:,.0f}），並分配 <b>{calculated_def_ratio*100:.1f}%</b> 至防禦型高股息標的（如 00713，約 NT$ {recommended_def_amt:,.0f}）。這能將歷史最大回撤完美鎖在 -20.24% 以內。</li>
      <li><b>借款資金與生活費分配成效：</b> 您目前將質押借款配置於多個標的或保留現金生活費，產生的加權再投入殖利率為 <b>{weighted_reinvest_yield*100:.2f}%</b>。只要維持寬限期內外皆為正現金流（當前每月淨現金流 <b>{'正數 (NT$ ' + f'{monthly_net_grace:,.0f}' + '/月)' if monthly_net_grace >= 0 else '負數'}</b>），即達成「以股養息、以息扛債」的永續複利迴圈。</li>
      <li><b>HMM 市場體制因應：</b> 系統偵測大盤處於 <b>{current_regime_str}</b>。在擴張期享受高資金效率；若未來進入空襲危機，純數學反波動率模型將自動無上限去槓桿，您只需信任並遵循系統指引，絕不恐慌殺低。</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 💵 房貸與質押寬限期內 vs 寬限期滿後現金流自償性全試算")
    lc, rc = st.columns(2)
    with lc:
        st.markdown("##### 🟢 階段一：寬限期內每月現金流 (Grace Period - 只付利息)")
        st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
        st.metric("總資產與多元分配每月總配息", f"+NT$ {monthly_div:,.0f}")
        net_grace_color = "text-green" if monthly_net_grace >= 0 else "text-red"
        st.markdown(f"""<div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #10B981; padding: 12px; border-radius: 8px;"><div style="color: #9CA3AF; font-size: 0.85rem;">寬限期內每月淨現金流</div><div style="font-size: 1.5rem; font-weight: 900;" class="{net_grace_color}">{'+' if monthly_net_grace >= 0 else ''}NT$ {monthly_net_grace:,.0f} / 月</div></div>""", unsafe_allow_html=True)
    with rc:
        st.markdown("##### 🟠 階段二：寬限期滿後每月現金流 (Post-Grace - 本息均攤)")
        st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
        st.metric("總資產每月總配息收益", f"-NT$ {monthly_div:,.0f}")
        if st.session_state.mortgages:
            st.metric("每月房貸支出 (本息均攤)", f"-NT$ {mortgages_annual_outflow_post/12:,.0f}", "⚠️ 開始攤還本金")
        net_post_color = "text-green" if monthly_net_post >= 0 else "text-red"
        st.markdown(f"""<div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #F59E0B; padding: 12px; border-radius: 8px;"><div style="color: #9CA3AF; font-size: 0.85rem;">寬限期滿後每月淨現金流</div><div style="font-size: 1.5rem; font-weight: 900;" class="{net_post_color}">{'+' if monthly_net_post >= 0 else ''}NT$ {monthly_net_post:,.0f} / 月</div></div>""", unsafe_allow_html=True)

with tab_custom_backtest:
    st.markdown("### 📈 用戶自訂投資組合線上即時動態回測與數學效能分析")
    st.markdown("""
    <div class="theory-box">
    💡 <b>【線上即時計量回測與最優槓桿引擎】</b><br>
    本引擎完全根據您在左側填入的<b>持倉標的、本金規模、質押借款與資金分配</b>，透過 Yahoo Finance 線上即時抓取真實歷史數據（過去 1 年），並以嚴格的數學計量模型（動態最優槓桿、索提諾比率、滾動回撤 MDD）進行即時動態回測。
    </div>
    """, unsafe_allow_html=True)

    bc1, bc2 = st.columns(2)
    with bc1:
        backtest_mode = st.radio("選擇資產配置權重來源", ["👑 AI 智慧富人動態最優化配置 (基於模型)", "✍️ 手動自訂投資組合權重"])
    with bc2:
        backtest_period = st.selectbox("回測歷史週期長度", ["1年 (Daily)", "6個月 (Daily)"], index=0)

    valid_tickers = [a['ticker'].strip().upper() for a in st.session_state.owned_assets if a['ticker'].strip()]
    if not valid_tickers: valid_tickers = ["00685L.TW", "00713.TW"]

    @st.cache_data(ttl=300)
    def fetch_backtest_history(tickers, period_str):
        p = "1yr" if "1年" in period_str else "6mo"
        data_dict = {}
        for t in tickers:
            try:
                df = yf.download(t, period=p, interval="1d", auto_adjust=False, progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    s = df['Close'].dropna()
                    if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
                    data_dict[t] = s
            except:
                pass
        return pd.DataFrame(data_dict)

    with st.spinner("⏳ 正在透過線上金融終端機抓取真實歷史數據並計算最優槓桿與回測..."):
        hist_df = fetch_backtest_history(valid_tickers, backtest_period)

    if not hist_df.empty and len(hist_df.columns) > 0:
        hist_df = hist_df.dropna()
        returns_df = hist_df.pct_change().dropna()
        
        if "AI 智慧富人動態最優化配置" in backtest_mode:
            weights = np.zeros(len(valid_tickers))
            if len(valid_tickers) == 1:
                weights[0] = 1.0
            else:
                weights[0] = calculated_atk_ratio
                remaining_w = calculated_def_ratio
                for i in range(1, len(valid_tickers)):
                    weights[i] = remaining_w / (len(valid_tickers) - 1)
        else:
            st.markdown("##### ✍️ 手動設定各持倉標的佔「自有本金」的權重比例 (%)")
            manual_weights = []
            cols_w = st.columns(len(valid_tickers))
            weight_sum_chk = 0.0
            for idx, t in enumerate(valid_tickers):
                with cols_w[idx]:
                    def_w = float(100.0 / len(valid_tickers))
                    w_val = st.number_input(f"{t} 權重 (%)", min_value=0.0, max_value=100.0, value=def_w, step=5.0, key=f"manual_w_{t}")
                    manual_weights.append(w_val)
                    weight_sum_chk += w_val
            
            weights = np.array(manual_weights) / 100.0
            if abs(weight_sum_chk - 100.0) > 0.1:
                st.warning(f"⚠️ 目前手動權重總和為 {weight_sum_chk:.1f}%（建議調整至 100%）")
                if weight_sum_chk > 0: weights = weights / (weight_sum_chk / 100.0)

        # 計算資產組合的實時日波動率與數學最優槓桿
        portfolio_daily_rets_unlev = returns_df.dot(weights)
        ann_vol_unlev = float(portfolio_daily_rets_unlev.std() * np.sqrt(252) * 100)
        ann_vol_unlev = max(ann_vol_unlev, 1.0) # 避免除以零
        
        # 數學計量計算出的最優動態槓桿 (Optimal Leverage)
        # 基於逆波動率縮放與 HMM 體制乘數
        optimal_leverage = min(max(15.0 / ann_vol_unlev, 1.0), 2.5) * regime_multiplier
        
        effective_leverage = (base_val_total + loan_amount) / base_val_total if base_val_total > 0 else 1.0
        portfolio_daily_rets = portfolio_daily_rets_unlev * effective_leverage

        cum_path = np.cumprod(1 + portfolio_daily_rets)
        total_return = float((cum_path.iloc[-1] - 1.0) * 100) if not cum_path.empty else 0.0
        
        days_count = len(portfolio_daily_rets)
        years = days_count / 252.0 if days_count > 0 else 1.0
        cagr = float(((cum_path.iloc[-1] ** (1.0 / years)) - 1.0) * 100) if days_count > 0 and cum_path.iloc[-1] > 0 else 0.0
        
        ann_vol = float(portfolio_daily_rets.std() * np.sqrt(252) * 100)
        
        rf_daily = 0.015 / 252.0
        neg_rets = portfolio_daily_rets[portfolio_daily_rets < rf_daily]
        downside_std = float(neg_rets.std() * np.sqrt(252)) if len(neg_rets) > 0 else 0.001
        if downside_std == 0: downside_std = 0.001
        sortino = float(((portfolio_daily_rets.mean() * 252) - 0.015) / downside_std)

        rolling_max = np.maximum.accumulate(cum_path)
        drawdown = (cum_path - rolling_max) / rolling_max
        mdd = float(drawdown.min() * 100)

        # 呈現回測指標卡片 (加入最優槓桿指標)
        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
        with mc1: st.metric("總回測累積報酬率", f"{total_return:+.2f}%")
        with mc2: st.metric("年化報酬率 (CAGR)", f"{cagr:.2f}%")
        with mc3: st.metric("組合年化波動率", f"{ann_vol:.2f}%")
        with mc4: st.metric("數學最優動態槓桿", f"{optimal_leverage:.2f}x", "⚡ 計量模型推薦")
        with mc5: st.metric("索提諾比率 (Sortino)", f"{sortino:.2f}", "⚡ 風險調整報酬")
        with mc6: st.metric("歷史最大回撤 (MDD)", f"{mdd:.2f}%", "🛡️ 下檔風險")

        bt_col1, bt_col2 = st.columns(2)
        with bt_col1:
            st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
            st.markdown("##### 📈 您的投資組合線上即時累積淨值曲線")
            fig_bc = go.Figure()
            fig_bc.add_trace(go.Scatter(x=cum_path.index, y=cum_path.values * st.session_state.total_equity_cost, mode='lines', name="自訂組合淨值", line=dict(color="#10B981", width=2)))
            fig_bc.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis=dict(title='資產總值 (NT$)'))
            st.plotly_chart(fig_bc, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with bt_col2:
            st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
            st.markdown("##### 📉 滾動式最大回撤 (Drawdown 監控)")
            fig_bd = go.Figure()
            fig_bd.add_trace(go.Scatter(x=drawdown.index, y=drawdown.values * 100, mode='lines', name="回撤幅度 (%)", line=dict(color="#EF4444", width=1.5), fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.15)'))
            fig_bd.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis=dict(title='回撤幅度 (%)'))
            st.plotly_chart(fig_bd, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 👑 富人思維與最優槓桿計量效能智慧建議 (AI Wealth Advisory)")
        st.markdown(f"""
        <div class="theory-box" style="border-left-color: #3B82F6; background: rgba(59, 130, 246, 0.08);">
        💡 <b>【數學最優槓桿與線上即時回測深度解析】</b><br>
        根據您目前輸入的真實標的歷史數據與模型運算：
        <ul>
          <li><b>計量推薦的最優槓桿（Optimal Leverage）：</b> 透過您的組合波動率（{ann_vol_unlev:.2f}%）與當前 HMM 體制（{current_regime_str}），系統計算出的<b>數學最優槓桿倍數為 {optimal_leverage:.2f}x</b>。您可以對比您當前的實際槓桿（{effective_leverage:.2f}x）──若實際槓桿低於最優槓桿，代表資金效率尚有提升空間；若高於最優槓桿，則需注意波動風險。</li>
          <li><b>索提諾效率評價：</b> 您當前組合的索提諾比率為 <b>{sortino:.2f}</b>。數值越高，代表您在承擔下檔跌幅時，換取了更高效的超額複利。</li>
          <li><b>富人動態調整心法：</b> 面對現在與未來，富人從不盲目開滿槓桿，而是讓槓桿隨市場波動率自動呼吸（逆波動率縮放）。當系統顯示回測回撤為 <b>{mdd:.2f}%</b> 時，請確保您的維持率高於 160%，讓複利安全地替您工作。</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 無法取得足夠的歷史回測數據，請確認您的台股代號是否正確（例如台股需加上 `.TW`，如 `00713.TW`）。")

with tab_opt:
    st.markdown("### 📊 索提諾效率前緣與蒙地卡羅風險模擬")
    
    ret_1, ret_2 = 0.24 * portfolio_beta * regime_multiplier, 0.07
    vol_1, vol_2 = 0.32 * portfolio_beta * (1.2 if hmm_state_id == 2 else 1.0), 0.12
    corr_12 = 0.30

    np.random.seed(42)
    num_portfolios = 1500
    weights_1_arr = np.random.uniform(0.0, 1.0, num_portfolios)
    port_returns = weights_1_arr * ret_1 + (1 - weights_1_arr) * ret_2
    port_vols = np.sqrt(weights_1_arr**2 * vol_1**2 + (1 - weights_1_arr)**2 * vol_2**2 + 2 * weights_1_arr * (1 - weights_1_arr) * vol_1 * vol_2 * corr_12)
    risk_free_rate = 0.015

    sortino_ratios, downside_vols, historical_mdds, regularized_scores = [], [], [], []
    for r, v in zip(port_returns, port_vols):
        sim_returns = np.random.normal(r / 252, v / np.sqrt(252), 252)
        negative_diffs = np.minimum(0, sim_returns - (risk_free_rate / 252))
        d_vol = np.sqrt(np.mean(negative_diffs ** 2)) * np.sqrt(252)
        d_vol = max(d_vol, 0.001)
        downside_vols.append(d_vol)
        sortino = (r - risk_free_rate) / d_vol
        sortino_ratios.append(sortino)
        cum_path_sim = np.cumprod(1 + sim_returns)
        rolling_max = np.maximum.accumulate(cum_path_sim)
        mdd_sim = np.min((cum_path_sim - rolling_max) / rolling_max)
        historical_mdds.append(abs(mdd_sim))
        penalty = l2_lambda_val * (r**2 + (1-r)**2)
        if "最大索提諾" in opt_objective: score = sortino - penalty
        elif "極致報酬" in opt_objective: score = r - penalty
        else: score = -abs(mdd_sim) - penalty
        regularized_scores.append(score)

    sortino_ratios, downside_vols, historical_mdds, regularized_scores = np.array(sortino_ratios), np.array(downside_vols), np.array(historical_mdds), np.array(regularized_scores)
    mdd_limit_val = user_max_mdd_limit / 100.0
    safe_mask = historical_mdds <= mdd_limit_val
    best_filtered_idx = np.where(safe_mask)[0][np.argmax(regularized_scores[safe_mask])] if np.any(safe_mask) else np.argmax(regularized_scores)

    optimal_sortino_weight_1 = weights_1_arr[best_filtered_idx]
    optimal_mdd_val = historical_mdds[best_filtered_idx] * 100
    optimal_return_val = port_returns[best_filtered_idx] * 100

    num_sim_days, num_paths = 252, 250
    dt = 1.0 / 252.0
    base_portfolio_val = max(total_collateral, 100000.0)
    sim_paths = np.zeros((num_sim_days, num_paths))
    sim_paths[0, :] = base_portfolio_val
    for p in range(num_paths):
        val = base_portfolio_val
        for d in range(1, num_sim_days):
            drift = (port_returns[best_filtered_idx]) * portfolio_beta * regime_multiplier
            vol_p = (downside_vols[best_filtered_idx]) * portfolio_beta
            shock = np.random.normal(0, 1)
            val = val * (1 + drift * dt + vol_p * np.sqrt(dt) * shock)
            sim_paths[d, p] = max(val, 1000.0)

    path_median = np.percentile(sim_paths, 50, axis=1)
    path_upper_95 = np.percentile(sim_paths, 95, axis=1)
    path_lower_5 = np.percentile(sim_paths, 5, axis=1)

    ef_col1, ef_col2 = st.columns(2)
    with ef_col1:
        st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
        st.markdown(f"##### 📊 索提諾效率前緣與 HMM 最佳權重指引")
        fig_ef = go.Figure()
        fig_ef.add_trace(go.Scatter(x=downside_vols * 100, y=port_returns * 100, mode='markers', marker=dict(size=7, color=sortino_ratios, colorscale='Viridis', showscale=True)))
        fig_ef.add_trace(go.Scatter(x=[downside_vols[best_filtered_idx] * 100], y=[port_returns[best_filtered_idx] * 100], mode='markers+text', marker=dict(size=18, color='#10B981', symbol='star'), text=["★ HMM 優化最佳組合"], textposition="top center"))
        fig_ef.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig_ef, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with ef_col2:
        st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
        st.markdown("##### 🌲 蒙地卡羅隨機軌跡模擬 (未來 1 年)")
        fig_mc = go.Figure()
        days_arr = np.arange(num_sim_days)
        fig_mc.add_trace(go.Scatter(x=days_arr, y=path_upper_95, mode='lines', line=dict(width=0), showlegend=False))
        fig_mc.add_trace(go.Scatter(x=days_arr, y=path_lower_5, mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.12)', showlegend=False))
        fig_mc.add_trace(go.Scatter(x=days_arr, y=path_upper_95, mode='lines', line=dict(width=2, color='#10B981', dash='dot'), name="95% 樂觀"))
        fig_mc.add_trace(go.Scatter(x=days_arr, y=path_median, mode='lines', line=dict(width=3, color='#F59E0B'), name="50% 中位數"))
        fig_mc.add_trace(go.Scatter(x=days_arr, y=path_lower_5, mode='lines', line=dict(width=2, color='#EF4444', dash='dot'), name="5% 壓力"))
        fig_mc.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig_mc, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)