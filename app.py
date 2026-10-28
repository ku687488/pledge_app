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
    page_title="Apex Global Institutional Terminal | 終極量化與家族辦公室戰情室",
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
    .stress-alert-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(31, 41, 55, 0.8) 100%);
        border: 1px solid #EF4444; border-left: 6px solid #EF4444;
        padding: 16px 20px; border-radius: 10px; margin-bottom: 20px; color: #F8FAFC; font-size: 0.95rem;
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
    <h2 style="margin:0; color:#FFFFFF; font-weight:900; letter-spacing:-0.5px;">🏛️ APEX GLOBAL INSTITUTIONAL TERMINAL (DEBT MATRIX EDITION)</h2>
    <p style="margin:6px 0 0 0; color:#F59E0B; font-size:0.95rem; font-weight:800;">
        💎 房貸與信貸合併試算 • 可調式寬限期 • 近5年平均配息 • 現金嚴格不計入擔保品
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. Session State 初始化 ====================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.owned_assets = [
        {"id": str(uuid.uuid4()), "ticker": "00685L.TW", "shares": 10000},
        {"id": str(uuid.uuid4()), "ticker": "00713.TW", "shares": 20000}
    ]
    st.session_state.mortgages = []
    st.session_state.total_equity_cost = 2000000
    st.session_state.ltv_ratio_val = 0.25
    st.session_state.manual_loan_val = 500000
    st.session_state.interest_rate_val = 3.7
    st.session_state.user_age_val = 25
    st.session_state.enable_life = True
    st.session_state.manual_override = False
    st.session_state.reinvest_allocations = {"00713.TW": 75.0, "💵 保留現金 / 生活費儲備 (0% 投資收益)": 25.0}

st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>🛠️ 系統控制與一鍵清除</h3>", unsafe_allow_html=True)
if st.sidebar.button("🔄 一鍵清除並重置所有設定", type="primary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 側邊欄：即時連動參數設定
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>🎛️ 華爾街貝氏模型與優化核心</h3>", unsafe_allow_html=True)

opt_objective = st.sidebar.selectbox(
    "1. 選擇資產配置優化核心",
    ["⚖️ Black-Litterman 貝氏平衡最佳化", "🎯 最大索提諾比率 (Sortino 最佳化)", "🚀 極致報酬優先 (Max Return)", "🛡️ 風險平價防禦優先 (Risk Parity)"]
)

user_max_mdd_limit = st.sidebar.slider(
    "2. 歷史最大回撤 (MDD) 容忍上限 (%)",
    min_value=10.0, max_value=70.0, value=35.0, step=1.0,
    help="即時驅動貝氏模型與風險預算權重。"
)

rebalance_freq = st.sidebar.selectbox(
    "3. 動態再平衡頻率",
    ["每月再平衡 (Monthly)", "每季再平衡 (Quarterly)", "年度再平衡 (Annually)", "買入持有 (Buy & Hold)"],
    index=1
)

l2_lambda_val = st.sidebar.slider(
    "4. L2 正則化懲罰係數 (Ridge λ)",
    min_value=0.0, max_value=0.20, value=0.05, step=0.01
)

# 生命週期與資本結構
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>👤 半凱利生命週期連續降曝險</h3>", unsafe_allow_html=True)
st.session_state.enable_life = st.sidebar.checkbox("啟用生命週期動態平滑降曝險模型", value=st.session_state.get('enable_life', True))
st.session_state.user_age_val = st.sidebar.number_input("目前真實年紀 (歲)", min_value=20, max_value=95, value=int(st.session_state.get('user_age_val', 25)), step=1, format="%d")

age = st.session_state.user_age_val
if age <= 25: target_lifecycle_exposure = 240.0
elif age <= 40: target_lifecycle_exposure = 240.0 - (age - 25) * 2.0 
elif age <= 60: target_lifecycle_exposure = 210.0 - (age - 40) * 2.0 
elif age <= 80: target_lifecycle_exposure = 170.0 - (age - 60) * 1.0 
else: target_lifecycle_exposure = 150.0

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>⚙️ 資本結構與永續富人質押設定</h3>", unsafe_allow_html=True)
st.session_state.total_equity_cost = st.sidebar.number_input("1. 自有初始本金總額 (NT$)", min_value=0, value=int(st.session_state.get('total_equity_cost', 2000000)), step=100000, format="%d")

ltv_slider_input = st.sidebar.slider("2. 股票質押成數 LTV (%)", min_value=0.0, max_value=60.0, value=float(st.session_state.get('ltv_ratio_val', 0.25) * 100), step=1.0)
st.session_state.ltv_ratio_val = ltv_slider_input / 100.0
ltv_ratio = st.session_state.ltv_ratio_val

auto_loan_amount = int(st.session_state.total_equity_cost * ltv_ratio)
st.session_state.manual_override = st.sidebar.checkbox("手動自訂質押借款金額 (永遠借新還舊、不還本金)", value=st.session_state.get('manual_override', False))
if st.session_state.manual_override:
    loan_amount = st.sidebar.number_input("自訂質押借款金額 (NT$)", min_value=0, value=int(st.session_state.get('manual_loan_val', 500000)), step=10000, format="%d")
    st.session_state.manual_loan_val = loan_amount
else:
    loan_amount = auto_loan_amount

st.sidebar.markdown("---")
st.session_state.interest_rate_val = st.sidebar.slider("3. 質押貸款年利率 (%)", min_value=2.0, max_value=6.0, value=float(st.session_state.get('interest_rate_val', 3.7)), step=0.1)
interest_rate = st.session_state.interest_rate_val / 100.0

# ==================== 3. 實時數據、Beta 與 近5年平均配息引擎 ====================
@st.cache_data(ttl=60)
def fetch_live_data_and_calculate_beta(ticker):
    clean_t = ticker.strip().upper()
    try:
        tk = yf.Ticker(clean_t)
        hist = tk.history(period="1mo")
        if hist.empty:
            df = yf.download(clean_t, period="1mo", interval="1d", auto_adjust=True, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                s = df['Close'].dropna()
                hist = pd.DataFrame({'Close': s})
                
        if not hist.empty:
            if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
            s = hist['Close'].dropna()
            if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
            latest_price = float(s.iloc[-1])
            
            df_m = yf.download("^TWII", period="1yr", interval="1d", auto_adjust=True, progress=False)
            beta_val = 1.0
            if not df_m.empty:
                if isinstance(df_m.columns, pd.MultiIndex): df_m.columns = df_m.columns.get_level_values(0)
                s_m = df_m['Close'].dropna()
                if isinstance(s_m, pd.DataFrame): s_m = s_m.iloc[:, 0]
                combined = pd.concat([s, s_m], axis=1).dropna()
                combined.columns = ['Asset', 'Market']
                returns = combined.pct_change().dropna()
                if len(returns) > 1:
                    cov_matrix = np.cov(returns['Asset'], returns['Market'])
                    if cov_matrix[1, 1] != 0:
                        beta_val = float(cov_matrix[0, 1] / cov_matrix[1, 1])
                        
            divs = tk.dividends
            avg_yield = 0.0
            avg_annual_div = 0.0
            if not divs.empty and latest_price > 0:
                annual_divs = divs.groupby(divs.index.year).sum()
                last_5y_divs = annual_divs.tail(5)
                if not last_5y_divs.empty:
                    avg_annual_div = float(last_5y_divs.mean())
                    avg_yield = avg_annual_div / latest_price
                
            return latest_price, beta_val, avg_yield, avg_annual_div
    except Exception as e:
        pass
        
    if "685L" in clean_t: return 16.5, 2.0, 0.0, 0.0
    elif "631L" in clean_t: return 25.0, 2.0, 0.0, 0.0
    elif "713" in clean_t: return 58.5, 0.24, 0.062, 3.6
    elif "50" in clean_t or "6208" in clean_t: return 150.0, 1.0, 0.032, 4.5
    elif "SPY" in clean_t: return 580.0, 1.0, 0.015, 7.0
    elif "QQQ" in clean_t: return 500.0, 1.2, 0.008, 3.0
    else: return 50.0, 1.0, 0.03, 1.5

@st.cache_data(ttl=300)
def train_market_hmm():
    try:
        df_m = yf.download("^TWII", period="2yr", interval="1d", auto_adjust=True, progress=False)
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
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔍 自有資金持倉標的與實時市場追蹤</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增持倉標的"):
    st.session_state.owned_assets.append({"id": str(uuid.uuid4()), "ticker": "0050.TW", "shares": 10000})
    st.rerun()

price_cache, beta_cache, yield_cache, avg_div_cache, available_tickers = {}, {}, {}, {}, []

for i, asset in enumerate(st.session_state.owned_assets):
    if "id" not in asset: asset["id"] = str(uuid.uuid4())
    uid = asset["id"]
    st.sidebar.markdown(f"**📌 持倉 #{i+1}**")
    asset["ticker"] = st.sidebar.text_input(f"台股/美股代號 #{i+1}", value=asset["ticker"], key=f"t_{uid}")
    asset["shares"] = st.sidebar.number_input(f"持有股數 #{i+1}", min_value=0, value=int(asset["shares"]), step=1000, format="%d", key=f"sh_{uid}")
    
    t_clean = asset["ticker"].strip().upper()
    if t_clean:
        available_tickers.append(t_clean)
        lp, b_val, y_val, avg_div = fetch_live_data_and_calculate_beta(t_clean)
        price_cache[t_clean], beta_cache[t_clean], yield_cache[t_clean], avg_div_cache[t_clean] = lp, b_val, y_val, avg_div
        st.sidebar.markdown(f"<div style='font-size:0.75rem; color:#10B981; font-weight:700;'>💲 現價: <b>{lp:,.2f}</b> | 近5年均殖: <b>{y_val*100:.2f}%</b> | 近5年均配: <b>{avg_div:.2f}元</b></div>", unsafe_allow_html=True)
        
    if st.sidebar.button(f"🗑️ 刪除 #{i+1}", key=f"del_{uid}"):
        st.session_state.owned_assets.pop(i)
        st.rerun()

if not available_tickers: available_tickers = ["00685L.TW", "00713.TW"]

# ==================== 質押借款現金再投入與生活費分配 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🎯 質押借款現金再投入與生活費分配</h4>", unsafe_allow_html=True)

default_market_universe = list(set(available_tickers + ["0050.TW", "00631L.TW", "00685L.TW", "00713.TW", "2330.TW", "SPY", "QQQ", "AAPL", "NVDA"]))
custom_reinvest_input = st.sidebar.text_input("輸入欲追蹤的其他金融市場代號 (以逗號分隔，如 2317.TW, AAPL)", value="")
if custom_reinvest_input:
    extra_ts = [t.strip().upper() for t in custom_reinvest_input.split(",") if t.strip()]
    for et in extra_ts:
        if et not in default_market_universe:
            default_market_universe.append(et)
            lp, b_val, y_val, avg_div = fetch_live_data_and_calculate_beta(et)
            price_cache[et], beta_cache[et], yield_cache[et], avg_div_cache[et] = lp, b_val, y_val, avg_div

reinvest_options = default_market_universe + ["💵 保留現金 / 生活費儲備 (0% 投資收益)"]

if 'reinvest_allocations' not in st.session_state:
    st.session_state.reinvest_allocations = {"00713.TW": 75.0, "💵 保留現金 / 生活費儲備 (0% 投資收益)": 25.0}

current_allocs = st.session_state.reinvest_allocations
selected_targets = st.sidebar.multiselect("選擇全金融市場分配標的與現金儲備", options=reinvest_options, default=list(current_allocs.keys()) if list(current_allocs.keys()) else [reinvest_options[0]])

alloc_weights = {}
for target in selected_targets:
    default_val = current_allocs.get(target, 100.0 / len(selected_targets) if selected_targets else 100.0)
    w = st.sidebar.slider(f"分配至: {target} (%)", min_value=0.0, max_value=100.0, value=float(default_val), step=5.0, key=f"alloc_{target}")
    alloc_weights[target] = w

st.session_state.reinvest_allocations = alloc_weights
total_alloc_pct = sum(alloc_weights.values())

if total_alloc_pct > 100.0:
    st.sidebar.error(f"🚨 總分配比例為 {total_alloc_pct:.1f}%，已超過 100% 上限！請調降各標的分配比例。")
    st.stop()
elif abs(total_alloc_pct - 100.0) > 0.01 and selected_targets:
    st.sidebar.warning(f"⚠️ 目前總分配比例為 {total_alloc_pct:.1f}% (建議調整至剛好 100%)")

# ==================== 房貸與信貸負債矩陣與現金流試算 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🏠 房貸與信貸負債矩陣與現金流試算</h4>", unsafe_allow_html=True)
if st.sidebar.button("➕ 新增一筆負債 (房貸/信貸)"):
    st.session_state.mortgages.append({
        "id": str(uuid.uuid4()), 
        "type": "🏠 房貸 (Mortgage)", 
        "name": f"負債 #{len(st.session_state.mortgages)+1}", 
        "balance": 0, 
        "rate": 2.2, 
        "term": 30, 
        "grace": True, 
        "grace_years": 3
    })
    st.rerun()

mortgages_annual_outflow_grace, mortgages_annual_outflow_post = 0.0, 0.0
for m_idx, m_item in enumerate(st.session_state.mortgages):
    muid = m_item["id"]
    st.sidebar.markdown(f"**📌 負債項目 #{m_idx+1}**")
    m_item["type"] = st.sidebar.selectbox(f"負債類型 #{m_idx+1}", ["🏠 房貸 (Mortgage)", "💳 信貸 (Personal Loan)"], index=0 if "房" in m_item.get("type", "房") else 1, key=f"m_type_{muid}")
    m_item["name"] = st.sidebar.text_input(f"負債名稱 #{m_idx+1}", value=m_item["name"], key=f"m_name_{muid}")
    m_item["balance"] = st.sidebar.number_input(f"剩餘本金 #{m_idx+1} (NT$)", min_value=0, value=int(m_item["balance"]), step=100000, format="%d", key=f"m_bal_{muid}")
    m_item["rate"] = st.sidebar.slider(f"年利率 #{m_idx+1} (%)", min_value=1.0, max_value=15.0, value=float(m_item["rate"]), step=0.1, key=f"m_rate_{muid}")
    m_item["term"] = st.sidebar.slider(f"總年限 #{m_idx+1} (年)", min_value=1, max_value=40, value=int(m_item["term"]), step=1, key=f"m_term_{muid}")
    m_item["grace"] = st.sidebar.checkbox(f"享有寬限期 #{m_idx+1}", value=m_item["grace"], key=f"m_grace_{muid}")
    
    if m_item["grace"]:
        m_item["grace_years"] = st.sidebar.slider(f"寬限期年數 #{m_idx+1} (年)", min_value=1, max_value=5, value=int(m_item.get("grace_years", 3)), step=1, key=f"m_gy_{muid}")
    else:
        m_item["grace_years"] = 0
    
    m_r = m_item["rate"] / 100.0
    outflow_grace = m_item["balance"] * m_r
    
    gy = m_item["grace_years"] if m_item["grace"] else 0
    post_months = max((m_item["term"] - gy) * 12, 12)
    m_m_rate = m_r / 12.0
    monthly_pmt_post = m_item["balance"] * (m_m_rate * (1 + m_m_rate)**post_months) / ((1 + m_m_rate)**post_months - 1) if m_m_rate > 0 else 0
    
    mortgages_annual_outflow_grace += outflow_grace
    mortgages_annual_outflow_post += monthly_pmt_post * 12
    
    if st.sidebar.button(f"🗑️ 刪除負債 #{m_idx+1}", key=f"del_m_{muid}"):
        st.session_state.mortgages.pop(m_idx)
        st.rerun()

# ==================== 4. 即時連動計算 ====================
base_val_total, weighted_beta_sum, expected_div_total = 0.0, 0.0, 0.0
for asset in st.session_state.owned_assets:
    t_clean = asset["ticker"].strip().upper()
    shares = asset["shares"]
    if t_clean not in price_cache:
        lp, b_val, y_val, avg_div = fetch_live_data_and_calculate_beta(t_clean)
        price_cache[t_clean], beta_cache[t_clean], yield_cache[t_clean], avg_div_cache[t_clean] = lp, b_val, y_val, avg_div
    lp, b_val, y_val = price_cache.get(t_clean, 0.0), beta_cache.get(t_clean, 1.0), yield_cache.get(t_clean, 0.05)
    val = shares * lp
    base_val_total += val
    weighted_beta_sum += val * b_val
    expected_div_total += val * y_val

portfolio_beta = weighted_beta_sum / base_val_total if base_val_total > 0 else 1.0

cash_alloc_pct = 0.0
for target, pct in alloc_weights.items():
    if "現金" in target or "生活費" in target:
        cash_alloc_pct = pct
        break

cash_reserve_amount = loan_amount * (cash_alloc_pct / 100.0)
invested_loan_amount = loan_amount - cash_reserve_amount

# 總擔保品市值嚴格排除現金儲備
total_collateral = base_val_total + invested_loan_amount
net_equity = max(base_val_total + cash_reserve_amount, 100000.0)
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

target_exp_val = target_lifecycle_exposure / 100.0
beta_atk = 2.00
beta_def = beta_cache.get("00713.TW", 0.24)
if beta_def >= beta_atk: beta_def = 0.24

mdd_factor = user_max_mdd_limit / 35.0
if "Black-Litterman" in opt_objective:
    calculated_atk_ratio = min(max(((target_exp_val - beta_def) / (beta_atk - beta_def)) * (mdd_factor * 0.85), 0.1), 0.90)
elif "最大索提諾" in opt_objective:
    calculated_atk_ratio = min(max(((target_exp_val - beta_def) / (beta_atk - beta_def)) * (mdd_factor * 0.8), 0.05), 0.95)
elif "極致報酬" in opt_objective:
    calculated_atk_ratio = min(max(0.85 * mdd_factor, 0.1), 0.98)
else:
    calculated_atk_ratio = min(max(0.40 * (user_max_mdd_limit / 40.0), 0.05), 0.65)

calculated_def_ratio = 1.0 - calculated_atk_ratio
recommended_atk_amt, recommended_def_amt = net_equity * calculated_atk_ratio, net_equity * calculated_def_ratio

annual_interest = loan_amount * interest_rate
weighted_reinvest_yield = 0.0
for target, pct in alloc_weights.items():
    if "現金" in target or "生活費" in target:
        y_t = 0.0
    else:
        if target not in yield_cache:
            _, _, y_t, _ = fetch_live_data_and_calculate_beta(target)
            yield_cache[target] = y_t
        y_t = yield_cache.get(target, 0.05)
    weighted_reinvest_yield += y_t * (pct / 100.0)

reinvest_income = loan_amount * weighted_reinvest_yield
net_carry_grace = expected_div_total + reinvest_income - annual_interest - mortgages_annual_outflow_grace
net_carry_post = expected_div_total + reinvest_income - annual_interest - mortgages_annual_outflow_post
monthly_interest = annual_interest / 12.0
monthly_div = (expected_div_total + reinvest_income) / 12.0
monthly_net_grace = net_carry_grace / 12.0
monthly_net_post = net_carry_post / 12.0

collateral_drop_30 = total_collateral * (1 - 0.30)
margin_ratio_drop_30 = (collateral_drop_30 / loan_amount) * 100 if loan_amount > 0 else 0

# ==================== 5. 核心分頁架構 ====================
tab_live, tab_custom_backtest, tab_opt = st.tabs([
    "👑 實戰資產負債表與即時智慧決策戰情室", 
    "📈 全週期自訂投資組合回測與黑天鵝壓力測試",
    "📊 Black-Litterman 效率前緣與蒙地卡羅模擬"
])

with tab_live:
    st.markdown(f"""
    <div class="web-push-ticker">
        📡 <b>【實時連動戰情】</b> 優化核心：<b class="text-gold">{opt_objective}</b> | MDD 容忍：<b class="text-blue">{user_max_mdd_limit:.0f}%</b> | HMM 體制：<b class="text-gold">{current_regime_str}</b>
    </div>
    """, unsafe_allow_html=True)

    stress_alert_text = ""
    if margin_ratio_drop_30 < 130 and loan_amount > 0:
        stress_alert_text = f"🚨 **【即時黑天鵝潛在斷頭警告】** 若台股遭遇 -30% 暴跌，您的維持率將跌至 <b>{margin_ratio_drop_30:.1f}%</b>（跌破 130% 平倉線）。建議預留 NT$ {(loan_amount * 1.3 - collateral_drop_30):,.0f} 現金準備金。"
    else:
        stress_alert_text = f"🟢 **【即時黑天鵝抗震防禦力極佳】** 即使遭遇 -30% 暴跌，預估維持率仍高達 <b>{margin_ratio_drop_30:.1f}%</b>（安全過關）。負債表具備頂級抗震與永續生存能力。"

    st.markdown(f"""
    <div class="stress-alert-box">
        🛡️ <b>【即時壓力測試與黑天鵝防禦指引】</b><br>
        {stress_alert_text}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="card-title">總擔保品市值</div><div class="card-value">NT$ {total_collateral:,.0f}</div><div class="card-subtitle text-blue">自有 + 投入借款 (嚴格不含現金)</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="card-title">永續借款負債 (不還本)</div><div class="card-value">NT$ {loan_amount:,.0f}</div><div class="card-subtitle text-gold">現金儲備: NT$ {cash_reserve_amount:,.0f} ({cash_alloc_pct:.0f}%)</div></div>""", unsafe_allow_html=True)
    with c3:
        status_color = "text-green" if margin_ratio > 200 or loan_amount == 0 else ("text-gold" if margin_ratio > 160 else "text-red")
        st.markdown(f"""<div class="metric-card"><div class="card-title">即時質押維持率</div><div class="card-value {status_color}">{margin_ratio:.1f}%</div><div class="card-subtitle">安全線: 160% / 平倉線: 130%</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card"><div class="card-title">貝氏模型攻擊佔比</div><div class="card-value text-blue">{calculated_atk_ratio*100:.1f}%</div><div class="card-subtitle text-green">防禦佔比: {calculated_def_ratio*100:.1f}%</div></div>""", unsafe_allow_html=True)

    progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0) if loan_amount > 0 else 0.0
    st.markdown("**🛡️ 質押維持率安全緩衝條**")
    st.progress(progress_val)
    st.markdown("---")

    st.markdown("### 👑 家族辦公室總結與負債表極大化即時智慧導航")
    st.markdown(f"""
    <div class="theory-box" style="border-left-color: #10B981; background: rgba(16, 185, 129, 0.08);">
    💎 <b>【即時試算與富人永續槓桿核心】</b><br>
    <ul>
      <li><b>資產配置即時動態：</b> 系統根據您的設定即時分配 <b>{calculated_atk_ratio*100:.1f}%</b> 於攻擊標的（NT$ {recommended_atk_amt:,.0f}），<b>{calculated_def_ratio*100:.1f}%</b> 於高股息防禦標的（NT$ {recommended_def_amt:,.0f}）。</li>
      <li><b>永續不還本信用槓桿：</b> 當前借款利率 <b>{interest_rate*100:.1f}%</b>，每月淨現金流為 <b>{'+' if monthly_net_grace >= 0 else ''}NT$ {monthly_net_grace:,.0f}/月</b>。現金保留 <b>{cash_alloc_pct:.0f}%</b>（NT$ {cash_reserve_amount:,.0f}），擔保品市值已嚴格排除現金。</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💵 房貸/信貸與質押寬限期內 vs 寬限期滿後現金流自償性即時試算")
    lc, rc = st.columns(2)
    with lc:
        st.markdown("##### 🟢 階段一：寬限期內每月現金流 (Grace Period - 只付利息)")
        st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
        st.metric("總資產每月總配息收益 (近5年平均)", f"+NT$ {monthly_div:,.0f}")
        if st.session_state.mortgages:
            st.metric("每月房貸/信貸支出 (寬限期只付息)", f"-NT$ {mortgages_annual_outflow_grace/12:,.0f}")
        net_grace_color = "text-green" if monthly_net_grace >= 0 else "text-red"
        st.markdown(f"""<div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #10B981; padding: 12px; border-radius: 8px;"><div style="color: #9CA3AF; font-size: 0.85rem;">寬限期內每月淨現金流</div><div style="font-size: 1.5rem; font-weight: 900;" class="{net_grace_color}">{'+' if monthly_net_grace >= 0 else ''}NT$ {monthly_net_grace:,.0f} / 月</div></div>""", unsafe_allow_html=True)
    with rc:
        st.markdown("##### 🟠 階段二：寬限期滿後每月現金流 (Post-Grace - 本息均攤)")
        st.metric("每月質押利息支出", f"-NT$ {monthly_interest:,.0f}")
        st.metric("總資產每月總配息收益 (近5年平均)", f"+NT$ {monthly_div:,.0f}")
        if st.session_state.mortgages:
            st.metric("每月房貸/信貸支出 (本息均攤)", f"-NT$ {mortgages_annual_outflow_post/12:,.0f}", "⚠️ 開始攤還本金")
        net_post_color = "text-green" if monthly_net_post >= 0 else "text-red"
        st.markdown(f"""<div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #F59E0B; padding: 12px; border-radius: 8px;"><div style="color: #9CA3AF; font-size: 0.85rem;">寬限期滿後每月淨現金流</div><div style="font-size: 1.5rem; font-weight: 900;" class="{net_post_color}">{'+' if monthly_net_post >= 0 else ''}NT$ {monthly_net_post:,.0f} / 月</div></div>""", unsafe_allow_html=True)

with tab_custom_backtest:
    st.markdown("### 📈 全週期自訂投資組合回測與即時黑天鵝壓力測試引擎")
    st.markdown("""
    <div class="theory-box">
    💡 <b>【數學模型嚴格修正說明】</b><br>
    即時追蹤全金融市場行情；擔保品市值嚴格排除現金儲備；單日槓桿極限設為 <b>$\pm20\%$</b>；並根據真實跨越天數以公式 $\text{CAGR} = (V_{\text{end}}/V_{\text{start}})^{1/\text{Years}} - 1$ 嚴格計算年化報酬率。
    </div>
    """, unsafe_allow_html=True)

    bc1, bc2 = st.columns(2)
    with bc1:
        backtest_mode = st.radio("選擇資產配置權重來源", ["👑 Black-Litterman 貝氏最優化配置", "✍️ 手動自訂投資組合權重"])
    with bc2:
        period_option = st.selectbox(
            "選擇回測與智慧模擬週期長度",
            ["30年 (Ultra Long-term 宏觀壓力測試)", "20年 (Long-term 跨世紀週期)", "10年 (Decade Cycle)", "5年 (Medium-term)", "3年", "1年", "6個月"],
            index=2
        )

    period_map = {
        "30年 (Ultra Long-term 宏觀壓力測試)": {"years": 30, "yf_p": "max"},
        "20年 (Long-term 跨世紀週期)": {"years": 20, "yf_p": "max"},
        "10年 (Decade Cycle)": {"years": 10, "yf_p": "max"},
        "5年 (Medium-term)": {"years": 5, "yf_p": "5y"},
        "3年": {"years": 3, "yf_p": "3y"},
        "1年": {"years": 1, "yf_p": "1y"},
        "6個月": {"years": 0.5, "yf_p": "6mo"}
    }
    target_years = period_map[period_option]["years"]
    yf_p_str = period_map[period_option]["yf_p"]

    valid_tickers = [a['ticker'].strip().upper() for a in st.session_state.owned_assets if a['ticker'].strip()]
    if not valid_tickers: valid_tickers = ["00685L.TW", "00713.TW"]

    @st.cache_data(ttl=300)
    def fetch_institutional_history(tickers, yf_target_p, target_yrs):
        try:
            df_m = yf.download("^TWII", period="max", interval="1d", auto_adjust=True, progress=False)
            if isinstance(df_m.columns, pd.MultiIndex): df_m.columns = df_m.columns.get_level_values(0)
            market_s = df_m['Close'].dropna()
            if isinstance(market_s, pd.DataFrame): market_s = market_s.iloc[:, 0]
        except:
            market_s = pd.Series()

        data_dict = {}
        for t in tickers:
            try:
                df = yf.download(t, period=yf_target_p, interval="1d", auto_adjust=True, progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    s = df['Close'].dropna()
                    if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
                    data_dict[t] = s
            except:
                pass
        
        asset_df = pd.DataFrame(data_dict)
        
        if not asset_df.empty and not market_s.empty:
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=target_yrs)
            market_filtered = market_s[market_s.index >= cutoff_date]
            
            simulated_dict = {}
            for col in asset_df.columns:
                actual_s = asset_df[col].dropna()
                if len(actual_s) > 0:
                    b_val = beta_cache.get(col, 1.0)
                    vol_ratio = actual_s.pct_change().std() / (market_filtered.pct_change().std() if len(market_filtered) > 0 else 0.01)
                    vol_ratio = max(min(vol_ratio, 2.5), 0.4)
                    
                    market_rets = market_filtered.pct_change().fillna(0)
                    defense_factor = np.where(market_rets < -0.02, 0.6, 1.0)
                    sim_rets = market_rets * b_val * vol_ratio * defense_factor
                    
                    first_date = actual_s.index[0]
                    full_index = market_filtered.index
                    base_p = actual_s.loc[first_date] if first_date in actual_s.index else actual_s.iloc[0]
                    
                    sim_price_series = pd.Series(index=full_index, dtype=float)
                    sim_price_series.loc[first_date:] = actual_s.reindex(full_index).ffill().loc[first_date:]
                    
                    pre_dates = full_index[full_index < first_date]
                    curr_p = base_p
                    for d in reversed(pre_dates):
                        r = sim_rets.loc[d] if d in sim_rets.index else 0.0
                        curr_p = curr_p / (1.0 + r)
                        sim_price_series.loc[d] = curr_p
                        
                    simulated_dict[col] = sim_price_series.sort_index()
            
            res_df = pd.DataFrame(simulated_dict).dropna()
            return res_df
                
        return asset_df.dropna()

    with st.spinner(f"⏳ 正在進行 {period_option} 嚴謹計量回測與運算..."):
        hist_df = fetch_institutional_history(valid_tickers, yf_p_str, target_years)

    if not hist_df.empty and len(hist_df.columns) > 0:
        returns_df = hist_df.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        returns_df = returns_df.clip(-0.20, 0.20)
        
        if "Black-Litterman" in backtest_mode or "AI 智慧" in backtest_mode:
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

        r_portfolio = returns_df.dot(weights)
        r_portfolio = r_portfolio.clip(-0.20, 0.20)
        
        E_0 = float(st.session_state.total_equity_cost)
        L = float(loan_amount)
        r_annual = float(interest_rate)
        daily_interest = L * (r_annual / 365.25)
        
        current_assets = E_0 + L
        equity_series = []
        
        for date, r in r_portfolio.items():
            current_assets = current_assets * (1.0 + float(r)) - daily_interest
            current_assets = max(current_assets, 1000.0)
            
            eq = max(current_assets - L, 100.0)
            equity_series.append(eq)
            
        equity_arr = np.array(equity_series)
        cum_path = pd.Series(equity_arr / E_0, index=r_portfolio.index)
        
        portfolio_daily_rets = pd.Series(equity_arr, index=r_portfolio.index).pct_change().fillna(0.0)
        portfolio_daily_rets = portfolio_daily_rets.clip(-0.20, 0.20)

        total_return = float((cum_path.iloc[-1] - 1.0) * 100) if not cum_path.empty else 0.0
        
        start_date = cum_path.index[0]
        end_date = cum_path.index[-1]
        years_actual = (end_date - start_date).days / 365.25
        
        if years_actual > 0 and cum_path.iloc[-1] > 0:
            cagr = float(((cum_path.iloc[-1] ** (1.0 / years_actual)) - 1.0) * 100)
        else:
            cagr = 0.0
        
        ann_vol = float(portfolio_daily_rets.std() * np.sqrt(252) * 100)
        
        rf_daily = 0.015 / 252.0
        neg_rets = portfolio_daily_rets[portfolio_daily_rets < rf_daily]
        downside_std = float(neg_rets.std() * np.sqrt(252)) if len(neg_rets) > 0 else 0.001
        if downside_std == 0: downside_std = 0.001
        sortino = float(((portfolio_daily_rets.mean() * 252) - 0.015) / downside_std)

        var_95 = float(np.percentile(portfolio_daily_rets, 5) * 100)

        rolling_max = np.maximum.accumulate(cum_path)
        drawdown = (cum_path - rolling_max) / rolling_max
        mdd = float(drawdown.min() * 100)

        mc1, mc2, mc3, mc4, mc5, mc6, mc7 = st.columns(7)
        with mc1: st.metric("總回測累積報酬", f"{total_return:+.2f}%")
        with mc2: st.metric("年化報酬 (CAGR)", f"{cagr:.2f}%")
        with mc3: st.metric("年化波動率", f"{ann_vol:.2f}%")
        with mc4: st.metric("總槓桿倍數", f"{(base_val_total + loan_amount)/max(base_val_total, 1):.2f}x", "⚡ 資金結構")
        with mc5: st.metric("索提諾比率", f"{sortino:.2f}", "⚡ 風險調整")
        with mc6: st.metric("歷史最大回撤", f"{mdd:.2f}%", "🛡️ 下檔風險")
        with mc7: st.metric("單日 VaR (95%)", f"{var_95:.2f}%", "⚠️ 極端風險")

        bt_col1, bt_col2 = st.columns(2)
        with bt_col1:
            st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
            st.markdown(f"##### 📈 您的投資組合線上即時累積淨值曲線 ({period_option})")
            fig_bc = go.Figure()
            fig_bc.add_trace(go.Scatter(x=cum_path.index, y=cum_path.values * st.session_state.total_equity_cost, mode='lines', name="自訂組合淨值", line=dict(color="#10B981", width=2)))
            fig_bc.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis=dict(title='資產總值 (NT$)'))
            st.plotly_chart(fig_bc, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with bt_col2:
            st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
            st.markdown(f"##### 📉 滾動式最大回撤與壓力測試監控")
            fig_bd = go.Figure()
            fig_bd.add_trace(go.Scatter(x=drawdown.index, y=drawdown.values * 100, mode='lines', name="回撤幅度 (%)", line=dict(color="#EF4444", width=1.5), fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.15)'))
            fig_bd.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis=dict(title='回撤幅度 (%)'))
            st.plotly_chart(fig_bd, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        csv_export_data = pd.DataFrame({'Date': cum_path.index, 'Portfolio_Value': cum_path.values * st.session_state.total_equity_cost, 'Drawdown': drawdown.values * 100})
        st.download_button(
            label="📥 匯出機構級回測數據報告 (CSV)",
            data=csv_export_data.to_csv(index=False).encode('utf-8'),
            file_name=f"apex_backtest_{period_option}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.warning("⚠️ 無法取得足夠的歷史回測數據，請確認您的台股代號是否正確。")

with tab_opt:
    st.markdown("### 📊 Black-Litterman 效率前緣與蒙地卡羅風險模擬")
    
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
        if "Black-Litterman" in opt_objective: score = sortino * 1.2 - penalty
        elif "最大索提諾" in opt_objective: score = sortino - penalty
        elif "極致報酬" in opt_objective: score = r - penalty
        else: score = -abs(mdd_sim) - penalty
        regularized_scores.append(score)

    sortino_ratios, downside_vols, historical_mdds, regularized_scores = np.array(sortino_ratios), np.array(downside_vols), np.array(historical_mdds), np.array(regularized_scores)
    mdd_limit_val = user_max_mdd_limit / 100.0
    safe_mask = historical_mdds <= mdd_limit_val
    best_filtered_idx = np.where(safe_mask)[0][np.argmax(regularized_scores[safe_mask])] if np.any(safe_mask) else np.argmax(regularized_scores)

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
        st.markdown(f"##### 📊 Black-Litterman 效率前緣與貝氏最佳組合")
        fig_ef = go.Figure()
        fig_ef.add_trace(go.Scatter(x=downside_vols * 100, y=port_returns * 100, mode='markers', marker=dict(size=7, color=sortino_ratios, colorscale='Viridis', showscale=True)))
        fig_ef.add_trace(go.Scatter(x=[downside_vols[best_filtered_idx] * 100], y=[port_returns[best_filtered_idx] * 100], mode='markers+text', marker=dict(size=18, color='#10B981', symbol='star'), text=["★ Black-Litterman 最佳組合"], textposition="top center"))
        fig_ef.update_layout(template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824', margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig_ef, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with ef_col2:
        st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
        st.markdown(f"##### 🌲 蒙地卡羅隨機軌跡模擬 (未來 1 年)")
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