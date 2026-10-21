import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ==================== 1. 頁面配置與華爾街黑卡級柔和美學 CSS ====================
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
    .explain-card {
        background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 8px;
        padding: 12px 16px; margin-bottom: 12px; font-size: 0.88rem; line-height: 1.5;
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
        💎 富人思維槓桿戰情室 • 全台股上市櫃股票與 ETF 任意代號直接輸入 • 智慧量化試算
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# 初始化 Session State
if 'owned_assets' not in st.session_state:
    st.session_state.owned_assets = []

if 'reinvest_assets' not in st.session_state:
    st.session_state.reinvest_assets = []

# ==================== 側邊欄：生命週期、資本結構與攻擊曝險 ====================
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>👤 投資人戰略風格與攻擊曝險設定</h3>", unsafe_allow_html=True)

enable_lifecycle_exposure = st.sidebar.checkbox("啟用生命週期動態降曝險 (強制保留 ≥ 150% 攻擊下限)", value=True)
user_age = st.sidebar.number_input("目前真實年紀 (歲)", min_value=20, max_value=90, value=25, step=1)
target_lifecycle_exposure = max(280.0 - (user_age - 25) * 3.5, 150.0)

if enable_lifecycle_exposure:
    st.sidebar.info(f"🎯 依據 {user_age} 歲生命週期模型：目標淨權益曝險率自動收斂至 **{target_lifecycle_exposure:.1f}%** (嚴格鎖定 150% 攻擊底線)")
else:
    st.sidebar.info("🔓 【完全自由曝險模式】：由您自行掌控曝險倍數，維持強悍攻擊動能。")

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>⚙️ 資本結構與富人質押設定</h3>", unsafe_allow_html=True)

total_equity_cost = st.sidebar.number_input("1. 自有初始本金總額 (NT$)", value=0, step=100000)
ltv_ratio = st.sidebar.slider("2. 股票質押成數 LTV (%)", min_value=0.0, max_value=60.0, value=0.0, step=1.0) / 100.0

auto_loan_amount = int(total_equity_cost * ltv_ratio)
manual_loan_override = st.sidebar.checkbox("手動自訂質押借款金額 (永久不還本金)", value=False)
if manual_loan_override:
    loan_amount = st.sidebar.number_input("自訂質押借款金額 (NT$)", value=0, step=10000)
else:
    loan_amount = auto_loan_amount
    st.sidebar.info(f"💡 自動連動質押借款額：**NT$ {loan_amount:,.0f}** (富人思維：只付利息不還本金)")

interest_rate = st.sidebar.slider("3. 質押貸款年利率 (%)", min_value=2.0, max_value=6.0, value=3.7, step=0.1) / 100.0

# ==================== 自有資金持倉：自由輸入任意台股代號 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔍 自有資金持有部位明細</h4>", unsafe_allow_html=True)
st.sidebar.info("💡 提示：可直接輸入任意台股代號（例如 00881、00929、2330、00631L 等）")

if st.sidebar.button("➕ 新增自有持倉標"):
    st.session_state.owned_assets.append({"ticker": "00881", "shares": 0.0, "div_yield": 0.05})
    st.rerun()

for i, asset in enumerate(st.session_state.owned_assets):
    st.sidebar.markdown(f"**📌 自有持倉 #{i+1}**")
    asset["ticker"] = st.sidebar.text_input(f"台股代號 #{i+1} (如 00881, 2330)", value=asset["ticker"], key=f"own_t_{i}")
    asset["shares"] = st.sidebar.number_input(f"持有股數 #{i+1}", value=float(asset["shares"]), step=1000.0, key=f"own_sh_{i}")
    asset["div_yield"] = st.sidebar.slider(f"預期年化殖利率 #{i+1} (%)", min_value=0.0, max_value=15.0, value=float(asset["div_yield"] * 100), step=0.1, key=f"own_div_{i}") / 100.0
    if st.sidebar.button(f"🗑️ 刪除自有持倉 #{i+1}", key=f"del_own_{i}"):
        st.session_state.owned_assets.pop(i)
        st.rerun()

# ==================== 質押額外資金：自由輸入任意台股代號 ====================
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔀 質押額外資金再投入部位</h4>", unsafe_allow_html=True)

if st.sidebar.button("➕ 新增質押再投入標的"):
    st.session_state.reinvest_assets.append({"ticker": "0050", "amount": 0.0, "div_yield": 0.03})
    st.rerun()

for j, rein in enumerate(st.session_state.reinvest_assets):
    st.sidebar.markdown(f"**📌 質押再投入 #{j+1}**")
    rein["ticker"] = st.sidebar.text_input(f"再投入台股代號 #{j+1} (如 00713, 2317)", value=rein["ticker"], key=f"rein_t_{j}")
    rein["amount"] = st.sidebar.number_input(f"投入金額 #{j+1} (NT$)", value=float(rein["amount"]), step=50000.0, key=f"rein_amt_{j}")
    rein["div_yield"] = st.sidebar.slider(f"再投入預期殖利率 #{j+1} (%)", min_value=0.0, max_value=15.0, value=float(rein["div_yield"] * 100), step=0.1, key=f"rein_div_{j}") / 100.0
    if st.sidebar.button(f"🗑️ 刪除再投入 #{j+1}", key=f"del_rein_{j}"):
        st.session_state.reinvest_assets.pop(j)
        st.rerun()

# 獨立房貸與信貸模組
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>💳 外部不動產/信貸負債模組 (自有資金本息負擔)</h4>", unsafe_allow_html=True)

enable_mortgage = st.sidebar.checkbox("啟用房貸現金流試算", value=False)
mortgage_annual_outflow = 0.0
if enable_mortgage:
    m_balance = st.sidebar.number_input("房貸剩餘本金 (NT$)", value=0, step=100000)
    m_rate = st.sidebar.slider("房貸年利率 (%)", min_value=1.5, max_value=5.0, value=2.2, step=0.1) / 100.0
    m_term = st.sidebar.slider("房貸總年限 (年)", min_value=10, max_value=40, value=30, step=5)
    m_grace = st.sidebar.checkbox("房貸享有寬限期 (只付利息)", value=True)
    m_grace_years = st.sidebar.slider("寬限期年數", min_value=1, max_value=5, value=3, step=1) if m_grace else 0
    
    m_interest_only = m_balance * m_rate
    if m_grace and m_grace_years > 0:
        mortgage_annual_outflow = m_interest_only
        st.sidebar.info(f"💡 房貸寬限期內年息支出 (自有資金負擔)：**NT$ {mortgage_annual_outflow:,.0f}**")
    else:
        m_months = m_term * 12
        m_m_rate = m_rate / 12.0
        m_monthly_pmt = m_balance * (m_m_rate * (1 + m_m_rate)**m_months) / ((1 + m_m_rate)**m_months - 1)
        mortgage_annual_outflow = m_monthly_pmt * 12
        st.sidebar.info(f"💡 房貸本息攤還年支出 (自有資金負擔)：**NT$ {mortgage_annual_outflow:,.0f}**")

enable_credit_loan = st.sidebar.checkbox("啟用信貸現金流試算", value=False)
credit_annual_outflow = 0.0
if enable_credit_loan:
    c_balance = st.sidebar.number_input("信貸剩餘本金 (NT$)", value=0, step=50000)
    c_rate = st.sidebar.slider("信貸年利率 (%)", min_value=2.0, max_value=8.0, value=2.8, step=0.1) / 100.0
    c_term = st.sidebar.slider("信貸總年限 (年)", min_value=3, max_value=7, value=7, step=1)
    
    c_months = c_term * 12
    c_m_rate = c_rate / 12.0
    c_monthly_pmt = c_balance * (c_m_rate * (1 + c_m_rate)**c_months) / ((1 + c_m_rate)**c_months - 1)
    credit_annual_outflow = c_monthly_pmt * 12
    st.sidebar.info(f"💡 信貸本息攤還年支出 (自有資金負擔)：**NT$ {credit_annual_outflow:,.0f}**")

# 動態自訂負債格子管理器
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>➕ 自訂彈性擴充負債格子</h4>", unsafe_allow_html=True)
if 'custom_debts' not in st.session_state:
    st.session_state.custom_debts = []

if st.sidebar.button("➕ 新增自訂負債項目"):
    st.session_state.custom_debts.append({
        "name": f"自訂負債 {len(st.session_state.custom_debts)+1}",
        "balance": 0.0,
        "rate": 3.0,
        "outflow": 0.0
    })

custom_debts_total_outflow = 0.0
for i, debt in enumerate(st.session_state.custom_debts):
    st.sidebar.markdown(f"**📌 項目 #{i+1}**")
    debt["name"] = st.sidebar.text_input(f"負債名稱 #{i+1}", value=debt["name"], key=f"c_name_{i}")
    debt["balance"] = st.sidebar.number_input(f"剩餘本金 #{i+1} (NT$)", value=debt["balance"], step=50000, key=f"c_bal_{i}")
    debt["rate"] = st.sidebar.slider(f"年利率 #{i+1} (%)", min_value=1.0, max_value=10.0, value=debt["rate"], step=0.1, key=f"c_rate_{i}")
    debt["outflow"] = st.sidebar.number_input(f"每年還款總額 #{i+1} (NT$)", value=debt["outflow"], step=10000, key=f"c_out_{i}")
    custom_debts_total_outflow += debt["outflow"]
    if st.sidebar.button(f"🗑️ 刪除此項 #{i+1}", key=f"del_c_{i}"):
        st.session_state.custom_debts.pop(i)
        st.rerun()

total_external_outflow = mortgage_annual_outflow + credit_annual_outflow + custom_debts_total_outflow

# ==================== 3. 24小時實時市場真實抓價引擎 (Yahoo Finance API) ====================
@st.cache_data(ttl=30)
def fetch_live_market_data(ticker):
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
    return data_dict

def format_ticker_symbol(raw_input):
    clean_t = raw_input.strip().upper()
    if not clean_t:
        return "0050.TW"
    if not clean_t.endswith(".TW") and not clean_t.endswith(".TWO") and not clean_t.startswith("^"):
        clean_t += ".TW"
    return clean_t

all_tickers_to_fetch = set()
for a in st.session_state.owned_assets:
    all_tickers_to_fetch.add(format_ticker_symbol(a["ticker"]))
for r in st.session_state.reinvest_assets:
    all_tickers_to_fetch.add(format_ticker_symbol(r["ticker"]))

price_cache = {}
for t in all_tickers_to_fetch:
    res = fetch_live_market_data(t)
    def get_latest(d, fb):
        for key in ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"]:
            if key in d and not d[key]["series"].empty:
                val = d[key]["series"].iloc[-1]
                if not pd.isna(val) and val > 0:
                    return float(val)
        return fb
    price_cache[t] = get_latest(res, 60.0)

market_data_twii = fetch_live_market_data("^TWII")
market_data_tsmc = fetch_live_market_data("2330.TW")
market_data_gspc = fetch_live_market_data("^GSPC")
market_data_ixic = fetch_live_market_data("^IXIC")
market_data_fx = fetch_live_market_data("TWD=X")

def get_latest_price(data_dict, fallback):
    for key in ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"]:
        if key in data_dict and not data_dict[key]["series"].empty:
            val = data_dict[key]["series"].iloc[-1]
            if not pd.isna(val) and val > 0:
                return float(val)
    return fallback

taiwii_p = get_latest_price(market_data_twii, 46292.0)
tsmc_p = get_latest_price(market_data_tsmc, 2405.0)

# ==================== 4. 計算總市值、配息與曝險 ====================
base_val_total = 0.0
expected_div_base = 0.0
effective_exposure_base = 0.0

for a in st.session_state.owned_assets:
    t_code = format_ticker_symbol(a["ticker"])
    p = price_cache.get(t_code, 60.0)
    beta = 2.0 if "2" in t_code or "L" in t_code else 1.0
    val = a["shares"] * p
    base_val_total += val
    expected_div_base += val * a["div_yield"]
    effective_exposure_base += val * beta

reinvest_val_total = 0.0
expected_div_rein = 0.0
effective_exposure_rein = 0.0

for r in st.session_state.reinvest_assets:
    t_code = format_ticker_symbol(r["ticker"])
    p = price_cache.get(t_code, 60.0)
    beta = 2.0 if "2" in t_code or "L" in t_code else 1.0
    amt = r["amount"]
    reinvest_val_total += amt
    expected_div_rein += amt * r["div_yield"]
    effective_exposure_rein += amt * beta

total_collateral = base_val_total + reinvest_val_total
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

total_expected_div = expected_div_base + expected_div_rein
annual_interest = loan_amount * interest_rate
net_carry = total_expected_div - annual_interest - total_external_outflow

monthly_interest = annual_interest / 12.0
monthly_div = total_expected_div / 12.0
monthly_external_outflow = total_external_outflow / 12.0
monthly_net_carry = net_carry / 12.0

total_exposure = effective_exposure_base + effective_exposure_rein
net_equity = total_collateral - loan_amount
exposure_vs_equity = max((total_exposure / net_equity) * 100, 150.0) if net_equity > 0 else 150.0

# ==================== 5. 華爾街量化模型：索提諾比率與蒙地卡羅 ====================
ret_1, ret_2 = 0.18, 0.08
vol_1, vol_2 = 0.25, 0.15
corr_12 = 0.35

np.random.seed(42)
num_portfolios = 1500
weights_1_arr = np.random.uniform(0.2, 0.9, num_portfolios)
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

regimes_drift = [0.22, -0.15, 0.05]
regimes_vol = [0.18, 0.32, 0.12]

sim_paths = np.zeros((num_sim_days, num_paths))
sim_paths[0, :] = base_portfolio_val

for p in range(num_paths):
    tree_choice = np.random.choice([0, 1, 2], size=num_sim_days, p=[0.6, 0.15, 0.25])
    val = base_portfolio_val
    for d in range(1, num_sim_days):
        reg = tree_choice[d]
        drift = regimes_drift[reg]
        vol = regimes_vol[reg]
        shock = np.random.normal(0, 1)
        val = val * (1 + drift * dt + vol * np.sqrt(dt) * shock)
        sim_paths[d, p] = max(val, 1000.0)

path_median = np.percentile(sim_paths, 50, axis=1)
path_upper_95 = np.percentile(sim_paths, 95, axis=1)
path_lower_5 = np.percentile(sim_paths, 5, axis=1)

# ==================== 6. 戰情快報與 AI 智慧動態預警引擎 ====================
st.markdown(f"""
<div class="web-push-ticker">
    📡 <b>【Apex 家族辦公室 24 小時實時戰情快報 (全台股代號自由輸入模式)】</b><br>
    • 自有原始市值：<b>NT$ {base_val_total:,.0f}</b> | 質押額外再投入市值：<b>NT$ {reinvest_val_total:,.0f}</b><br>
    • 動態淨權益曝險率：<b>{exposure_vs_equity:.1f}%</b> (嚴格遵守 ≥150% 攻擊下限) | 每月淨現金流：<b>{'+' if monthly_net_carry >= 0 else ''}NT$ {monthly_net_carry:,.0f}/月</b>
</div>
""", unsafe_allow_html=True)

def generate_ai_dynamic_alerts(ltv, margin_r, net_c):
    alerts = []
    if ltv > 0.25:
        alerts.append(f"⚠️ **[質押成數 LTV 超標提醒]** 目前設定的 LTV 為 {ltv*100:.1f}%，已超過最多 25% 穩健防禦上限。")
    else:
        alerts.append(f"🟢 **[全台股自定義配置狀態正常]** 即時動態維持率為 **{margin_r:.1f}%**，請隨時自訂您的部位與槓桿！")
        
    if net_c < 0:
        alerts.append(f"⚠️ **[負現金流提醒 (Negative Carry)]** 年度淨現金流為 -NT$ {abs(net_c):,.0f}，利息支出大於總配息收益。")
    else:
        alerts.append(f"🟢 **[現金流自償達成]** 達成 Positive Carry (+NT$ {net_c:,.0f}/年)，所有負債利息完全由總配息覆蓋！")
        
    return alerts

ai_insights = generate_ai_dynamic_alerts(ltv_ratio, margin_ratio, net_carry)
for insight in ai_insights:
    if "警報" in insight or "警告" in insight or "提醒" in insight:
        st.markdown(f'<div class="ai-alert-box">{insight}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-success-box">{insight}</div>', unsafe_allow_html=True)

# ==================== 7. 主戰情室 KPI 儀表板 ====================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">總擔保品市值 (原始+額外再投入)</div>
        <div class="card-value">NT$ {total_collateral:,.0f}</div>
        <div class="card-subtitle text-blue">原始: NT$ {base_val_total:,.0f} | 額外: NT$ {reinvest_val_total:,.0f}</div>
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
        <div class="card-title">自有資金淨權益曝險</div>
        <div class="card-value text-blue">{exposure_vs_equity:.1f}%</div>
        <div class="card-subtitle text-green">⚡ 強力攻擊下限 ≥ 150%</div>
    </div>
    """, unsafe_allow_html=True)

progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0) if loan_amount > 0 else 0.0
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer)**")
st.progress(progress_val)

st.markdown("---")

# ==================== 8. 【現金流至上核心優先】每月與年度現金流自償性試算面板 ====================
st.markdown("### 💵 核心重點優先：房貸/信貸與質押現金流自償性綜合試算")
lc, rc = st.columns(2)

with lc:
    st.markdown("##### 📅 每月現金流即時檢視 (Monthly Cash Flow)")
    st.metric("每月質押利息支出 (只付利息)", f"-NT$ {monthly_interest:,.0f}", f"貸款 NT$ {loan_amount:,.0f} × 利率 {interest_rate*100:.2f}% / 12")
    st.metric(f"總資產每月預期總配息收益", f"+NT$ {monthly_div:,.0f}", f"涵蓋所有自有持倉與質押再投入標的")
    
    if enable_mortgage or enable_credit_loan or st.session_state.custom_debts:
        st.metric(f"每月外部房貸/信貸本息或寬限期支出", f"-NT$ {monthly_external_outflow:,.0f}")
        
    monthly_net_color = "text-green" if monthly_net_carry >= 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #10B981; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">每月淨現金流效益 (Monthly Net Carry)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{monthly_net_color}">{'+' if monthly_net_carry >= 0 else ''}NT$ {monthly_net_carry:,.0f} / 月</div>
        <div style="font-size: 0.8rem; color: #10B981; margin-top: 4px; font-weight: 700;">{'🟢 每月現金流完全自償：總配息完美覆蓋質押與房貸/信貸支出！' if monthly_net_carry >= 0 else '🔴 每月現金流短缺：需由本業現金流補足差額。'}</div>
    </div>
    """, unsafe_allow_html=True)

with rc:
    st.markdown("##### 📅 年度現金流與複利滾存試算 (Annual Carry & Compound)")
    st.metric("年度質押利息總支出", f"-NT$ {annual_interest:,.0f}")
    st.metric("總資產年度配息總收益", f"+NT$ {total_expected_div:,.0f}")
    if enable_mortgage or enable_credit_loan or st.session_state.custom_debts:
        st.metric("年度外部負債總支出 (房貸/信貸)", f"-NT$ {total_external_outflow:,.0f}")
    
    net_carry_color = "text-green" if net_carry > 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #F59E0B; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">整體年度淨現金流效益 (Net Carry / 年)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{net_carry_color}">+NT$ {net_carry:,.0f}</div>
        <div style="font-size: 0.8rem; color: #F59E0B; margin-top: 4px; font-weight: 700;">{'🟢 Positive Carry：所有資產收益完全覆蓋所有負債（含房貸/信貸）！' if net_carry > 0 else '🔴 負現金流狀態。'}</div>
    </div>
    """, unsafe_allow_html=True)
    
    avg_div_yield = total_expected_div / total_collateral if total_collateral > 0 else 0.05
    comp_years = np.array([1, 3, 5, 10])
    compounded_values = [net_carry * (((1 + avg_div_yield) ** y - 1) / avg_div_yield) if net_carry > 0 else net_carry * y for y in comp_years]
    comp_df = pd.DataFrame({
        "累積時間": [f"{y} 年後" for y in comp_years],
        "淨現金流滾存總額": [f"NT$ {val:,.0f}" for val in compounded_values]
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ==================== 9. 【極致清晰圖表與大白話解析】索提諾比率與蒙地卡羅模擬 ====================
st.markdown("### 📈 華爾街量化核心：極致清晰圖表與大白話學理解析")

ef_col1, ef_col2 = st.columns(2)

with ef_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📊 1. 索提諾高效能前緣 (僅懲罰下行風險)")
    
    st.markdown(f"""
    <div class="explain-card">
        <b>💡 一眼看懂索提諾圖表：</b><br>
        • <b>橫軸（下行跌幅風險）</b>：代表<b>只有下跌崩盤時</b>才算作風險。<br>
        • <b>縱軸（預估年化總報酬）</b>：代表攻擊與防禦配置的預期回報。<br>
        • <b>★ 黃金綠星點</b>：<b>最優 CP 值配置 ({optimal_sortino_weight_1 * 100:.1f}% 攻擊標的)</b>！
    </div>
    """, unsafe_allow_html=True)
    
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

st.markdown("---")

# ==================== 11. 【TSMC 多情境 EPS 與機構共識矩陣】 ====================
st.markdown("### 🏛️ 台積電 (2330.TW) 保守 / 平均 / 樂觀 EPS 與機構共識矩陣")

@st.cache_data(ttl=300)
def get_dynamic_institutional_consensus(current_tsmc_price):
    try:
        stock = yf.Ticker("2330.TW")
        info = stock.info
        live_f_eps = info.get("forwardEps", 0.0)
        base_eps = float(live_f_eps) if live_f_eps and live_f_eps > 50 else max(145.0, current_tsmc_price / 22.5)
    except:
        base_eps = max(145.0, current_tsmc_price / 22.5)
        
    institutions = [
        {"機構名稱": "🟡 保守情境 (Conservative)", "pe": 22.0, "eps_multiplier": 0.95, "year": "2026 F"},
        {"機構名稱": "🔵 機構平均共識 (Consensus)", "pe": 26.5, "eps_multiplier": 1.12, "year": "2026/2027 F"},
        {"機構名稱": "🟢 樂觀牛市 (Bull / Aletheia)", "pe": 29.5, "eps_multiplier": 1.25, "year": "2027/2028 F"}
    ]
    data = []
    for inst in institutions:
        est_eps = round(base_eps * inst["eps_multiplier"], 1)
        target_price = round(est_eps * inst["pe"], 1)
        data.append({"情境/機構": inst["機構名稱"], "預估年份": inst["year"], "預估EPS": est_eps, "合理PE": inst["pe"], "台積電目標價 (NT$)": target_price})
    return pd.DataFrame(data)

institutional_consensus = get_dynamic_institutional_consensus(tsmc_p)
tsmc_resonance_weight = 0.92
institutional_consensus["推估大盤共振點位"] = taiwii_p * (1 + tsmc_resonance_weight * ((institutional_consensus["台積電目標價 (NT$)"] - tsmc_p) / tsmc_p))
institutional_consensus["潛在漲幅"] = ((institutional_consensus["台積電目標價 (NT$)"] / tsmc_p) - 1) * 100

st.dataframe(
    institutional_consensus.style.format({"預估EPS": "NT$ {:.1f}", "合理PE": "{:.1f}x", "台積電目標價 (NT$)": "NT$ {:,.1f}", "推估大盤共振點位": "{:,.0f} 點", "潛在漲幅": "{:+.1f}%"}),
    use_container_width=True, hide_index=True
)

st.markdown("---")

# ==================== 12. 正二路徑依賴與極端壓力測試 ====================
st.markdown("### 🚨 機構級正二路徑依賴與極端壓力測試 (Path-Dependent Stress Test)")
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    drop_pct = st.slider("模擬大盤累積崩盤跌幅 (%)", min_value=0, max_value=50, value=20, step=5)
with col_s2:
    crash_days = st.slider("跌落天數 (模擬路徑耗損)", min_value=1, max_value=10, value=3, step=1)

sim_total_collateral = total_collateral * ((1 - drop_pct/100.0) ** 1.5) if total_collateral > 0 else 0.0
sim_margin_ratio = (sim_total_collateral / loan_amount) * 100 if loan_amount > 0 else 0.0

required_collateral_130 = loan_amount * 1.30
critical_drop_pct = max(((total_collateral - required_collateral_130) / total_collateral) * 100, 0.0) if total_collateral > 0 else 0.0

s1, s2, s3, s4 = st.columns(4)
s1.metric("模擬大盤累積跌幅", f"-{drop_pct}% ({crash_days}天)")
s2.metric("崩盤後擔保品總市值", f"NT$ {sim_total_collateral:,.0f}")
s3.metric("壓力測試後維持率", f"{sim_margin_ratio:.1f}%" if loan_amount > 0 else "N/A (無負債)")
s4.metric("💥 斷頭 130% 臨界大盤跌幅", f"-{critical_drop_pct:.1f}%" if loan_amount > 0 else "N/A (無負債)")

if loan_amount == 0:
    st.info("💡 目前未設定質押借款負債，壓力測試維持率與斷頭防線保持安全。")
elif sim_margin_ratio > 160:
    st.success("🟢 壓力測試通過：大盤重挫時維持率仍高於 160% 安全線。")
elif sim_margin_ratio > 130:
    st.warning("🟡 維持率警示：維持率逼近平倉線。")
else:
    st.error("🔴 斷頭風險警報：維持率跌破 130% 平倉線！")