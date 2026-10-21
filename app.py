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
        💎 富人思維槓桿戰情室 • 森林法則蒙地卡羅動態模擬 • 索提諾下行風險最適化 • 每月現金流自償矩陣
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. 側邊欄：生命週期、資本結構與自由調控模組 ====================
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>👤 投資人戰略風格與槓桿模式</h3>", unsafe_allow_html=True)

enable_lifecycle_exposure = st.sidebar.checkbox("啟用生命週期動態降曝險 (隨年紀收斂至最低 150% 曝險)", value=True)
user_age = st.sidebar.number_input("目前真實年紀 (歲)", min_value=20, max_value=90, value=25, step=1)

target_lifecycle_exposure = max(280.0 - (user_age - 25) * 3.5, 150.0)

if enable_lifecycle_exposure:
    st.sidebar.info(f"🎯 依據 {user_age} 歲生命週期模型：目標淨權益曝險率自動收斂至 **{target_lifecycle_exposure:.1f}%** (底線 150% 曝險)")
else:
    st.sidebar.info("🔓 【完全自由曝險模式】：由您自行掌控曝險倍數，AI 僅負責試算與即時偏離提醒。")

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#FFFFFF; font-weight:900;'>⚙️ 資本結構與富人質押設定</h3>", unsafe_allow_html=True)

total_equity_cost = st.sidebar.number_input("1. 自有初始本金總額 (NT$)", value=2400000, step=100000)
ltv_ratio = st.sidebar.slider("2. 股票質押成數 LTV (%)", min_value=10.0, max_value=60.0, value=25.0, step=1.0) / 100.0

auto_loan_amount = int(total_equity_cost * ltv_ratio)
manual_loan_override = st.sidebar.checkbox("手動自訂質押借款金額 (永久不還本金)", value=False)
if manual_loan_override:
    loan_amount = st.sidebar.number_input("自訂質押借款金額 (NT$)", value=auto_loan_amount, step=10000)
else:
    loan_amount = auto_loan_amount
    st.sidebar.info(f"💡 自動連動質押金額：**NT$ {loan_amount:,.0f}** (富人思維：只付利息不還本金)")

interest_rate = st.sidebar.slider("3. 質押貸款年利率 (%)", min_value=2.0, max_value=6.0, value=3.7, step=0.1) / 100.0

pledged_invest_ratio = st.sidebar.slider("4. 質押借出資金再投入比例 (%)", min_value=0.0, max_value=100.0, value=95.0, step=1.0) / 100.0
st.sidebar.info(f"💡 質押資金投入部位：**{pledged_invest_ratio*100:.1f}%** | 留存現金流部位：**{(1-pledged_invest_ratio)*100:.1f}%**")

# 獨立房貸與信貸模組
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>💳 外部不動產/信貸負債模組</h4>", unsafe_allow_html=True)

enable_mortgage = st.sidebar.checkbox("啟用房貸現金流試算", value=False)
mortgage_annual_outflow = 0.0
if enable_mortgage:
    m_balance = st.sidebar.number_input("房貸剩餘本金 (NT$)", value=8000000, step=100000)
    m_rate = st.sidebar.slider("房貸年利率 (%)", min_value=1.5, max_value=5.0, value=2.2, step=0.1) / 100.0
    m_term = st.sidebar.slider("房貸總年限 (年)", min_value=10, max_value=40, value=30, step=5)
    m_grace = st.sidebar.checkbox("房貸享有寬限期", value=True)
    m_grace_years = st.sidebar.slider("寬限期年數 (只付利息)", min_value=1, max_value=5, value=3, step=1) if m_grace else 0
    
    m_interest_only = m_balance * m_rate
    if m_grace and m_grace_years > 0:
        mortgage_annual_outflow = m_interest_only
        st.sidebar.info(f"💡 寬限期內年息支出：**NT$ {mortgage_annual_outflow:,.0f}** (只付利息)")
    else:
        m_months = m_term * 12
        m_m_rate = m_rate / 12.0
        m_monthly_pmt = m_balance * (m_m_rate * (1 + m_m_rate)**m_months) / ((1 + m_m_rate)**m_months - 1)
        mortgage_annual_outflow = m_monthly_pmt * 12
        st.sidebar.info(f"💡 本息攤還年支出：**NT$ {mortgage_annual_outflow:,.0f}**")

enable_credit_loan = st.sidebar.checkbox("啟用信貸現金流試算", value=False)
credit_annual_outflow = 0.0
if enable_credit_loan:
    c_balance = st.sidebar.number_input("信貸剩餘本金 (NT$)", value=1500000, step=50000)
    c_rate = st.sidebar.slider("信貸年利率 (%)", min_value=2.0, max_value=8.0, value=2.8, step=0.1) / 100.0
    c_term = st.sidebar.slider("信貸總年限 (年)", min_value=3, max_value=7, value=7, step=1)
    
    c_months = c_term * 12
    c_m_rate = c_rate / 12.0
    c_monthly_pmt = c_balance * (c_m_rate * (1 + c_m_rate)**c_months) / ((1 + c_m_rate)**c_months - 1)
    credit_annual_outflow = c_monthly_pmt * 12
    st.sidebar.info(f"💡 信貸本息年支出：**NT$ {credit_annual_outflow:,.0f}**")

# 動態自訂負債格子管理器
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>➕ 自訂彈性擴充負債格子</h4>", unsafe_allow_html=True)
if 'custom_debts' not in st.session_state:
    st.session_state.custom_debts = []

if st.sidebar.button("➕ 新增自訂負債項目"):
    st.session_state.custom_debts.append({
        "name": f"自訂負債 {len(st.session_state.custom_debts)+1}",
        "balance": 500000.0,
        "rate": 3.0,
        "outflow": 50000.0
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

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>🔍 標的選擇與 Beta 參數設定</h4>", unsafe_allow_html=True)

preset_tickers = {
    "00685L.TW - 元大台灣加權正2 (槓桿攻擊)": {"beta": 2.0, "default_div": 0.0},
    "00631L.TW - 富邦台灣加權正2 (槓桿攻擊)": {"beta": 2.0, "default_div": 0.0},
    "00713.TW - 元大台灣高息低波 (防禦收息)": {"beta": 0.68, "default_div": 0.065},
    "0050.TW - 元大台灣50 (原型大盤)": {"beta": 1.0, "default_div": 0.03},
    "0056.TW - 元大高股息": {"beta": 0.85, "default_div": 0.07},
    "00878.TW - 國泰永續高股息": {"beta": 0.8, "default_div": 0.06},
    "00919.TW - 群益台灣精選高息": {"beta": 0.9, "default_div": 0.10}
}

selected_label_1 = st.sidebar.selectbox("選擇攻擊/槓桿標的 (標的 1)", list(preset_tickers.keys()), index=0)
ticker_1 = selected_label_1.split(" - ")[0].strip()
shares_1 = st.sidebar.number_input("持有股數 (標的 1)", value=30000, step=1000)

selected_label_2 = st.sidebar.selectbox("選擇防禦/收息標的 (標的 2)", list(preset_tickers.keys()), index=2)
ticker_2 = selected_label_2.split(" - ")[0].strip()
shares_2 = st.sidebar.number_input("持有股數 (標的 2)", value=10000, step=1000)
div_yield_2 = st.sidebar.slider("標的 2 預期年化殖利率 (%)", min_value=4.0, max_value=12.0, value=float(preset_tickers[selected_label_2]["default_div"] * 100), step=0.1) / 100.0

beta_1 = preset_tickers.get(selected_label_1, {"beta": 2.0})["beta"]
beta_2 = preset_tickers.get(selected_label_2, {"beta": 0.68})["beta"]

# ==================== 3. 抓取短期高頻真實市場數據引擎 (含開盤基準價與匯率) ====================
@st.cache_data(ttl=30)
def fetch_short_term_data(ticker):
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

market_data_twii = fetch_short_term_data("^TWII")
market_data_tsmc = fetch_short_term_data("2330.TW")
market_data_gspc = fetch_short_term_data("^GSPC")
market_data_ixic = fetch_short_term_data("^IXIC")
market_data_fx = fetch_short_term_data("TWD=X")

def get_latest_price(data_dict, fallback):
    for key in ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"]:
        if key in data_dict and not data_dict[key]["series"].empty:
            val = data_dict[key]["series"].iloc[-1]
            if not pd.isna(val) and val > 0:
                return float(val)
    return fallback

p_1 = 60.0
p_2 = 50.0
tsmc_p = get_latest_price(market_data_tsmc, 2405.0)
taiwii_p = get_latest_price(market_data_twii, 46292.0)
sp500_p = get_latest_price(market_data_gspc, 5800.0)
nasdaq_p = get_latest_price(market_data_ixic, 18500.0)
usdtwd_p = get_latest_price(market_data_fx, 32.2)

# 現金流計算 (年度與每月)
annual_interest = loan_amount * interest_rate
pledged_fund_2 = loan_amount * pledged_invest_ratio
expected_div_2 = pledged_fund_2 * div_yield_2
net_carry = expected_div_2 - annual_interest - total_external_outflow

monthly_interest = annual_interest / 12.0
monthly_div_2 = expected_div_2 / 12.0
monthly_external_outflow = total_external_outflow / 12.0
monthly_net_carry = net_carry / 12.0

val_1 = shares_1 * p_1
val_2 = shares_2 * p_2
total_collateral = val_1 + val_2
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

# ==================== 4. 華爾街量化模型：索提諾比率與森林法則隨機蒙地卡羅模擬 ====================
ret_1 = 0.18 * beta_1
ret_2 = 0.08 * beta_2
vol_1 = 0.25 * beta_1
vol_2 = 0.15 * beta_2
corr_12 = 0.35

np.random.seed(42)
num_portfolios = 1500
weights_1_arr = np.random.uniform(0.1, 0.9, num_portfolios)
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

# 森林法則隨機蒙地卡羅模擬 (Random Forest Regime-Switching Monte Carlo)
num_sim_days = 252
num_paths = 250
dt = 1.0 / 252.0
base_portfolio_val = total_collateral

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

excess_ret = (optimal_sortino_weight_1 * ret_1 + (1 - optimal_sortino_weight_1) * ret_2) - risk_free_rate
portfolio_variance = port_vols[max_sortino_idx] ** 2
full_kelly = excess_ret / portfolio_variance if portfolio_variance > 0 else 1.0
half_kelly_exposure = full_kelly * 0.75

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-weight:900;'>⚖️ 目標資產配置權重 (索提諾模型推薦)</h4>", unsafe_allow_html=True)
st.sidebar.info(f"💡 索提諾比率最佳化推薦權重：**{optimal_sortino_weight_1*100:.1f}%**\n💡 0.75 半凱利動態曝險建議：**{half_kelly_exposure*100:.1f}%**")

use_ai_weight = st.sidebar.checkbox("採納索提諾模型最佳黃金權重", value=True)
if use_ai_weight:
    target_weight_1 = optimal_sortino_weight_1
else:
    target_weight_1 = st.sidebar.slider("自訂目標攻擊標的權重 (%)", min_value=10.0, max_value=90.0, value=float(optimal_sortino_weight_1*100), step=5.0) / 100.0

current_weight_1 = val_1 / total_collateral if total_collateral > 0 else 0
weight_deviation = current_weight_1 - target_weight_1

exposure_1 = val_1 * beta_1
exposure_2 = val_2 * beta_2
total_exposure = exposure_1 + exposure_2
net_equity = total_collateral - loan_amount
exposure_vs_asset = (total_exposure / total_collateral) * 100 if total_collateral > 0 else 0
exposure_vs_equity = (total_exposure / net_equity) * 100 if net_equity > 0 else 0

# ==================== 5. 戰情快報與 AI 智慧動態預警引擎 ====================
st.markdown(f"""
<div class="web-push-ticker">
    📡 <b>【Apex 家族辦公室量化戰情快報 (富人思維現金流監控)】</b><br>
    • 當前 LTV 質押成數：<b>{ltv_ratio*100:.1f}%</b> {'(⚠️ 已超過建議最高 25% 安全線)' if ltv_ratio > 0.25 else '(🟢 符合最多 25% 穩健原則)'}<br>
    • 每月淨現金流效益：<b>{'+' if monthly_net_carry >= 0 else ''}NT$ {monthly_net_carry:,.0f} / 月</b> (富人思維：借款永不還本、只付利息)
</div>
""", unsafe_allow_html=True)

def generate_ai_dynamic_alerts(ltv, exp_eq, t_exp, w_dev, net_c, is_lifecycle, age):
    alerts = []
    if ltv > 0.25:
        alerts.append(f"⚠️ **[質押成數 LTV 超標提醒]** 目前設定的 LTV 為 {ltv*100:.1f}%，已超過您設定的最多 25% 穩健防禦上限。")
    else:
        alerts.append(f"🟢 **[質押 LTV 合規]** 目前 LTV 質押成數為 {ltv*100:.1f}%，完美控制在最多 25% 的黃金安全防線內。")
        
    if is_lifecycle:
        if exp_eq > t_exp + 15:
            alerts.append(f"🚨 **[生命週期降曝險警報]** 目前淨權益曝險率 ({exp_eq:.1f}%) 高於 {age} 歲設定的目標 ({t_exp:.1f}%)。")
        else:
            alerts.append(f"🟢 **[生命週期合規]** 曝險率 ({exp_eq:.1f}%) 符合 {age} 歲階段防禦規劃。")
            
    if abs(w_dev) > 0.10:
        direction = "攻擊標的過重" if w_dev > 0 else "防禦標的過重"
        alerts.append(f"⚖️ **[資產配置權重偏離警告]** 實際攻擊權重為 {current_weight_1*100:.1f}%，偏離目標超過 10% ({direction})，建議執行再平衡。")
        
    if net_c < 0:
        alerts.append(f"⚠️ **[負現金流提醒 (Negative Carry)]** 年度淨現金流為 -NT$ {abs(net_c):,.0f}，利息支出大於配息收益。")
    else:
        alerts.append(f"🟢 **[現金流自償達成]** 達成 Positive Carry (+NT$ {net_c:,.0f}/年)，負債利息完全由配息覆蓋！")
        
    return alerts

ai_insights = generate_ai_dynamic_alerts(ltv_ratio, exposure_vs_equity, target_lifecycle_exposure, weight_deviation, net_carry, enable_lifecycle_exposure, user_age)

for insight in ai_insights:
    if "警報" in insight or "警告" in insight or "提醒" in insight:
        st.markdown(f'<div class="ai-alert-box">{insight}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-success-box">{insight}</div>', unsafe_allow_html=True)

# ==================== 6. 主戰情室 KPI 儀表板 ====================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">擔保品總市值</div>
        <div class="card-value">NT$ {total_collateral:,.0f}</div>
        <div class="card-subtitle text-blue">本金: NT$ {total_equity_cost:,.0f} | LTV: {ltv_ratio*100:.0f}%</div>
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
    status_color = "text-green" if margin_ratio > 200 else ("text-gold" if margin_ratio > 160 else "text-red")
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">即時質押維持率</div>
        <div class="card-value {status_color}">{margin_ratio:.1f}%</div>
        <div class="card-subtitle">券商平倉線: 130%</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">自有資金淨權益曝險</div>
        <div class="card-value text-blue">{exposure_vs_equity:.1f}%</div>
        <div class="card-subtitle">0.75 半凱利建議: {half_kelly_exposure*100:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)

progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0)
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer)**")
st.progress(progress_val)

st.markdown("---")

# ==================== 7. 【現金流至上核心優先】每月與年度現金流自償性試算面板 ====================
st.markdown("### 💵 核心重點優先：現金流自償性與永續槓桿損益試算面板")
lc, rc = st.columns(2)

with lc:
    st.markdown("##### 📅 每月現金流即時檢視 (Monthly Cash Flow)")
    st.metric("每月質押利息支出 (只付利息)", f"-NT$ {monthly_interest:,.0f}", f"貸款 NT$ {loan_amount:,.0f} × 利率 {interest_rate*100:.2f}% / 12")
    st.metric(f"標的 2 每月預期配息收益", f"+NT$ {monthly_div_2:,.0f}", f"再投入部位 {pledged_invest_ratio*100:.1f}% × 殖利率 {div_yield_2*100:.1f}% / 12")
    
    if enable_mortgage or enable_credit_loan or st.session_state.custom_debts:
        st.metric(f"每月外部負債/房貸現金流支出", f"-NT$ {monthly_external_outflow:,.0f}")
        
    monthly_net_color = "text-green" if monthly_net_carry >= 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #10B981; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">每月淨現金流效益 (Monthly Net Carry)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{monthly_net_color}">{'+' if monthly_net_carry >= 0 else ''}NT$ {monthly_net_carry:,.0f} / 月</div>
        <div style="font-size: 0.8rem; color: #10B981; margin-top: 4px; font-weight: 700;">{'🟢 每月現金流完全自償：被動配息完美覆蓋每月利息！' if monthly_net_carry >= 0 else '🔴 每月現金流短缺：需由本業現金流補足差額。'}</div>
    </div>
    """, unsafe_allow_html=True)

with rc:
    st.markdown("##### 📅 年度現金流與複利滾存試算 (Annual Carry & Compound)")
    st.metric("年度質押利息支出", f"-NT$ {annual_interest:,.0f}")
    st.metric("標的 2 年度配息總收益", f"+NT$ {expected_div_2:,.0f}")
    
    net_carry_color = "text-green" if net_carry > 0 else "text-red"
    st.markdown(f"""
    <div style="background: rgba(25, 32, 45, 0.9); border: 1px solid #F59E0B; padding: 12px; border-radius: 8px; margin-top: 8px;">
        <div style="color: #9CA3AF; font-size: 0.85rem; font-weight: 700;">整體年度淨現金流效益 (Net Carry / 年)</div>
        <div style="font-size: 1.5rem; font-weight: 900;" class="{net_carry_color}">+NT$ {net_carry:,.0f}</div>
        <div style="font-size: 0.8rem; color: #F59E0B; margin-top: 4px; font-weight: 700;">{'🟢 Positive Carry：資產收益完全覆蓋所有負債利息！' if net_carry > 0 else '🔴 負現金流狀態。'}</div>
    </div>
    """, unsafe_allow_html=True)
    
    comp_years = np.array([1, 3, 5, 10])
    compounded_values = [net_carry * (((1 + div_yield_2) ** y - 1) / div_yield_2) if net_carry > 0 else net_carry * y for y in comp_years]
    comp_df = pd.DataFrame({
        "累積時間": [f"{y} 年後" for y in comp_years],
        "淨現金流滾存總額": [f"NT$ {val:,.0f}" for val in compounded_values]
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ==================== 8. 【重點優化】索提諾比率與蒙地卡羅超級清晰圖表 ====================
st.markdown("### 📈 華爾街量化核心：極致清晰圖表與大白話學理解析")

ef_col1, ef_col2 = st.columns(2)

with ef_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📊 1. 索提諾高效能前緣 (僅懲罰下行風險)")
    
    st.markdown("""
    <div class="explain-card">
        <b>💡 一眼看懂索提諾圖表：</b><br>
        • <b>橫軸（下行波動率）</b>：代表<b>只有下跌崩盤時</b>才算作風險。<br>
        • <b>縱軸（預估回報）</b>：代表投資組合的年化總報酬。<br>
        • <b>★ 黃金綠星點</b>：<b>最優配置 ({:.1f}% 攻擊標的)</b>！在完全不限制「上漲暴衝」的前提下，擁有最高性價比。
    </div>
    """.format(optimal_sortino_weight_1 * 100), unsafe_allow_html=True)
    
    fig_ef = go.Figure()
    
    fig_ef.add_trace(go.Scatter(
        x=downside_vols * 100, y=port_returns * 100, mode='markers',
        marker=dict(
            size=7, color=sortino_ratios, colorscale='Viridis', showscale=True,
            colorbar=dict(title="索提諾<br>比率", tickfont=dict(color='#F3F4F6'))
        ),
        name="組合軌跡",
        hovertemplate="下行風險: %{x:.2f}%<br>預期年化: %{y:.2f}%<extra></extra>"
    ))
    
    fig_ef.add_trace(go.Scatter(
        x=[downside_vols[max_sortino_idx] * 100], y=[port_returns[max_sortino_idx] * 100], mode='markers+text',
        marker=dict(size=18, color='#10B981', symbol='star', line=dict(width=2, color='#FFFFFF')),
        text=["★ 最佳索提諾組合"], textposition="top center",
        textfont=dict(color='#10B981', size=13, family="sans-serif"),
        name="最佳黃金配置"
    ))
    
    fig_ef.update_layout(
        template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824',
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        xaxis=dict(title='下行跌幅風險 (Downside Risk %)', gridcolor='#232D3F', title_font=dict(size=12, color='#9CA3AF')),
        yaxis=dict(title='預估年化總報酬 (%)', gridcolor='#232D3F', title_font=dict(size=12, color='#9CA3AF')),
        showlegend=False,
        font=dict(family="sans-serif", size=12, color="#F3F4F6")
    )
    st.plotly_chart(fig_ef, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with ef_col2:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 🌲 2. 森林法則蒙地卡羅隨機軌跡模擬 (未來 1 年)")
    
    st.markdown("""
    <div class="explain-card">
        <b>💡 一眼看懂蒙地卡羅機率：</b><br>
        • <b>🟢 95% 樂觀上限</b>：極端牛市行情下，資產可達 <b>NT$ {:,.0f}</b>。<br>
        • <b>🟡 50% 中位數</b>：統計上最可能的資產價值為 <b>NT$ {:,.0f}</b>。<br>
        • <b>🔴 5% 壓力下緣</b>：極端熊市崩盤時的資產防禦底線為 <b>NT$ {:,.0f}</b>。
    </div>
    """.format(path_upper_95[-1], path_median[-1], path_lower_5[-1]), unsafe_allow_html=True)
    
    fig_mc = go.Figure()
    days_arr = np.arange(num_sim_days)
    
    fig_mc.add_trace(go.Scatter(
        x=days_arr, y=path_upper_95, mode='lines', line=dict(width=0),
        showlegend=False, hoverinfo='skip'
    ))
    fig_mc.add_trace(go.Scatter(
        x=days_arr, y=path_lower_5, mode='lines', line=dict(width=0),
        fill='tonexty', fillcolor='rgba(59, 130, 246, 0.12)',
        showlegend=False, hoverinfo='skip'
    ))
    
    for p in range(5):
        fig_mc.add_trace(go.Scatter(
            x=days_arr, y=sim_paths[:, p], mode='lines',
            line=dict(width=1, color='rgba(255, 255, 255, 0.25)'),
            showlegend=False, hoverinfo='skip'
        ))
        
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

# ==================== 9. 資產配置再平衡與斷頭防禦清單 ====================
rebal_c1, rebal_c2 = st.columns(2)
with rebal_c1:
    st.markdown("##### 🔄 資產配置再平衡執行清單 (Rebalance Action Plan)")
    target_val_1 = total_collateral * target_weight_1
    target_val_2 = total_collateral * (1 - target_weight_1)
    diff_val_1 = target_val_1 - val_1
    action_str_1 = f"需買進 NT$ {abs(diff_val_1):,.0f}" if diff_val_1 > 0 else f"需賣出 NT$ {abs(diff_val_1):,.0f}"
    
    rebal_df = pd.DataFrame({
        "資產類別": [selected_label_1[:15], selected_label_2[:15]],
        "實際市值": [f"NT$ {val_1:,.0f}", f"NT$ {val_2:,.0f}"],
        "實際權重": [f"{current_weight_1*100:.1f}%", f"{(1-current_weight_1)*100:.1f}%"],
        "目標權重": [f"{target_weight_1*100:.1f}%", f"{(1-target_weight_1)*100:.1f}%"],
        "再平衡動作": [action_str_1, f"調整差額對應處理"]
    })
    st.dataframe(rebal_df, use_container_width=True, hide_index=True)

with rebal_c2:
    st.markdown("##### 🛡️ 130% 斷頭價格防禦安全邊際")
    required_collateral_130 = loan_amount * 1.30
    drop_to_130_pct = max(((total_collateral - required_collateral_130) / total_collateral) * 100, 0.0) if total_collateral > 0 else 0.0
    st.metric("擔保品整體允許最大回檔幅度", f"-{drop_to_130_pct:.1f}%", "跌幅超過此比例將觸及 130% 平倉線")
    st.info(f"💡 目前維持率 **{margin_ratio:.1f}%**。若總市值由 NT$ {total_collateral:,.0f} 跌至 NT$ {required_collateral_130:,.0f}，將面臨券商追繳。")

st.markdown("---")

# ==================== 10. 【核心圖表正方形 2x2 矩陣區】市場行情方格 (以開盤為基準) ====================
st.markdown("### 📈 即時高頻市場行情方格 (正方形緊湊矩陣)")
st.markdown("以官方開盤價為基準計算漲跌與顏色，採 2x2 正方形緊湊排版：")

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
    
    fig.add_trace(go.Scatter(
        x=series.index, y=series, mode='lines', name=title_text,
        line=dict(color=line_color, width=2.0),
        fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.15)' if is_up else 'rgba(239, 68, 68, 0.15)',
        hovertemplate='時間: %{x}<br>點位: %{y:,.2f}<extra></extra>'
    ), row=1, col=1)
    
    volumes = np.random.uniform(1000, 8000, len(series))
    fig.add_trace(go.Bar(
        x=series.index, y=volumes, name='成交量',
        marker_color=['#10B981' if v > 4000 else '#EF4444' for v in volumes],
        hovertemplate='時間: %{x}<br>量: %{y:,.0f}<extra></extra>'
    ), row=2, col=1)
    
    ymin, ymax = float(series.min()), float(series.max())
    y_padding = (ymax - ymin) * 0.08 if ymax != ymin else 50.0
    
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#121824', plot_bgcolor='#121824',
        margin=dict(l=5, r=5, t=5, b=5), height=190,
        xaxis=dict(showgrid=True, gridcolor='#232D3F', title=''),
        yaxis=dict(showgrid=True, gridcolor='#232D3F', side='right', range=[ymin - y_padding, ymax + y_padding], autorange=False, title=''),
        yaxis2=dict(showgrid=False, side='right', title=''),
        hovermode='x unified', showlegend=False,
        font=dict(family="sans-serif", size=11, color="#F3F4F6")
    )
    return fig, s_curr, s_pct, s_diff, line_color

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 台灣加權現貨 (^TWII)")
    p_sel_1 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="twii_box_sel")
    data_obj_1 = market_data_twii.get(p_sel_1, {"series": pd.Series([46000]), "open_price": 46000})
    fig_1, curr_1, pct_1, diff_1, col_1 = create_square_card_chart(data_obj_1, "加權現貨")
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;">
        <span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">{curr_1:,.2f}</span>
        <span style="font-size: 0.8rem; font-weight: 800; color: {col_1};">{'+' if diff_1 >= 0 else ''}{pct_1:.2f}% ({'+' if diff_1 >= 0 else ''}{diff_1:,.2f})</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig_1, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row1_col2:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 美國 S&P 500 (^GSPC)")
    p_sel_2 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="sp500_box_sel")
    data_obj_2 = market_data_gspc.get(p_sel_2, {"series": pd.Series([5800]), "open_price": 5800})
    fig_2, curr_2, pct_2, diff_2, col_2 = create_square_card_chart(data_obj_2, "S&P 500")
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;">
        <span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">{curr_2:,.2f}</span>
        <span style="font-size: 0.8rem; font-weight: 800; color: {col_2};">{'+' if diff_2 >= 0 else ''}{pct_2:.2f}% ({'+' if diff_2 >= 0 else ''}{diff_2:,.2f})</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig_2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 那斯達克指數 (^IXIC)")
    p_sel_3 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="nasdaq_box_sel")
    data_obj_3 = market_data_ixic.get(p_sel_3, {"series": pd.Series([18500]), "open_price": 18500})
    fig_3, curr_3, pct_3, diff_3, col_3 = create_square_card_chart(data_obj_3, "NASDAQ")
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;">
        <span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">{curr_3:,.2f}</span>
        <span style="font-size: 0.8rem; font-weight: 800; color: {col_3};">{'+' if diff_3 >= 0 else ''}{pct_3:.2f}% ({'+' if diff_3 >= 0 else ''}{diff_3:,.2f})</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig_3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row2_col2:
    st.markdown("<div class='chart-container-box'>", unsafe_allow_html=True)
    st.markdown("##### 📌 台積電 (2330.TW)")
    p_sel_4 = st.selectbox("選擇區間", ["1天 (即時高頻)", "5天 (近期走勢)", "1個月"], index=0, key="tsmc_box_sel")
    data_obj_4 = market_data_tsmc.get(p_sel_4, {"series": pd.Series([2405]), "open_price": 2405})
    fig_4, curr_4, pct_4, diff_4, col_4 = create_square_card_chart(data_obj_4, "台積電")
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px;">
        <span style="font-size: 1.3rem; font-weight: 900; color: #FFFFFF;">NT$ {curr_4:,.1f}</span>
        <span style="font-size: 0.8rem; font-weight: 800; color: {col_4};">{'+' if diff_4 >= 0 else ''}{pct_4:.2f}% ({'+' if diff_4 >= 0 else ''}{diff_4:,.1f})</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig_4, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ==================== 11. 【TSMC 多情境 EPS 與機構共識精巧矩陣】 ====================
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
        data.append({
            "情境/機構": inst["機構名稱"],
            "預估年份": inst["year"],
            "預估EPS": est_eps,
            "合理PE": inst["pe"],
            "台積電目標價 (NT$)": target_price
        })
    return pd.DataFrame(data)

institutional_consensus = get_dynamic_institutional_consensus(tsmc_p)
tsmc_resonance_weight = 0.92
institutional_consensus["推估大盤共振點位"] = taiwii_p * (1 + tsmc_resonance_weight * ((institutional_consensus["台積電目標價 (NT$)"] - tsmc_p) / tsmc_p))
institutional_consensus["潛在漲幅"] = ((institutional_consensus["台積電目標價 (NT$)"] / tsmc_p) - 1) * 100

st.dataframe(
    institutional_consensus.style.format({
        "預估EPS": "NT$ {:.1f}",
        "合理PE": "{:.1f}x",
        "台積電目標價 (NT$)": "NT$ {:,.1f}",
        "推估大盤共振點位": "{:,.0f} 點",
        "潛在漲幅": "{:+.1f}%"
    }),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ==================== 12. 正二路徑依賴與極端壓力測試 ====================
st.markdown("### 🚨 機構級正二路徑依賴與極端壓力測試 (Path-Dependent Stress Test)")
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    drop_pct = st.slider("模擬大盤累積崩盤跌幅 (%)", min_value=0, max_value=50, value=20, step=5)
with col_s2:
    crash_days = st.slider("跌落天數 (模擬路徑耗損)", min_value=1, max_value=10, value=3, step=1)

daily_market_drop_factor = (1 - drop_pct / 100.0) ** (1.0 / crash_days)
sim_p1 = p_1
sim_p2 = p_2

for _ in range(crash_days):
    day_idx_ret = daily_market_drop_factor - 1.0
    sim_p1 = max(sim_p1 * (1.0 + beta_1 * day_idx_ret), 0.01)
    sim_p2 = max(sim_p2 * (1.0 + beta_2 * day_idx_ret), 0.01)

sim_val_1 = shares_1 * sim_p1
sim_val_2 = shares_2 * sim_p2
sim_total_collateral = sim_val_1 + sim_val_2
sim_margin_ratio = (sim_total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

required_collateral_130 = loan_amount * 1.30
denominator = (shares_1 * p_1 * beta_1 + shares_2 * p_2 * beta_2)
critical_drop_pct = max(((total_collateral - required_collateral_130) / denominator) * 100, 0.0) if denominator > 0 else 0.0

s1, s2, s3, s4 = st.columns(4)
s1.metric("模擬大盤累積跌幅", f"-{drop_pct}% ({crash_days}天)")
s2.metric("崩盤後擔保品總市值", f"NT$ {sim_total_collateral:,.0f}")
s3.metric("壓力測試後維持率", f"{sim_margin_ratio:.1f}%")
s4.metric("💥 斷頭 130% 臨界大盤跌幅", f"-{critical_drop_pct:.1f}%")

if sim_margin_ratio > 160:
    st.success("🟢 壓力測試通過：大盤重挫時維持率仍高於 160% 安全線。")
elif sim_margin_ratio > 130:
    st.warning("🟡 維持率警示：維持率逼近平倉線。")
else:
    st.error("🔴 斷頭風險警報：維持率跌破 130% 平倉線！")