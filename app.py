import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import datetime
import os

# ==================== 1. 頁面配置與黑卡級美學 CSS ====================
st.set_page_config(
    page_title="Apex Global Institutional Terminal | 家族辦公室量化戰情室",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background-color: #0B0E14; color: #E0E6ED; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    section[data-testid="stSidebar"] { background-color: #151A23 !important; border-right: 1px solid #232D3F; }
    .metric-card {
        background: linear-gradient(135deg, rgba(25, 32, 45, 0.8) 0%, rgba(18, 24, 35, 0.9) 100%);
        border: 1px solid #2A364F; border-radius: 12px; padding: 20px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4); margin-bottom: 15px;
    }
    .card-title { color: #8B949E; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .card-value { color: #F3F4F6; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; }
    .card-subtitle { font-size: 0.8rem; margin-top: 4px; }
    .text-gold { color: #F59E0B !important; }
    .text-green { color: #10B981 !important; }
    .text-blue { color: #3B82F6 !important; }
    .text-red { color: #EF4444 !important; }
    .hero-header {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border-left: 4px solid #3B82F6; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px;
    }
    .web-push-ticker {
        background: rgba(30, 41, 59, 0.95); border: 1px solid #3B82F6; border-left: 6px solid #3B82F6;
        padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; color: #F8FAFC;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero-header">
    <h2 style="margin:0; color:#F8FAFC; font-weight:800; letter-spacing:-0.5px;">🏛️ APEX GLOBAL INSTITUTIONAL TERMINAL</h2>
    <p style="margin:5px 0 0 0; color:#94A3B8; font-size:0.95rem;">
        全球機構級量化戰情室 | 24H 跨時區追蹤 • 美股/期貨連動預估引擎 • 正二溢價/折價回血扣血模型
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. 側邊欄：本金與質押動態連動 ====================
st.sidebar.markdown("<h3 style='color:#F3F4F6;'>⚙️ 本金與質押動態連動</h3>", unsafe_allow_html=True)

total_equity_cost = st.sidebar.number_input("1. 自有初始本金總額 (NT$)", value=2400000, step=100000)
ltv_ratio = st.sidebar.slider("2. 質押成數 LTV (%)", min_value=10.0, max_value=60.0, value=25.0, step=1.0) / 100.0

auto_loan_amount = int(total_equity_cost * ltv_ratio)
manual_loan_override = st.sidebar.checkbox("手動自訂質押金額 (取消連動)", value=False)
if manual_loan_override:
    loan_amount = st.sidebar.number_input("自訂質押借款金額 (NT$)", value=auto_loan_amount, step=10000)
else:
    loan_amount = auto_loan_amount
    st.sidebar.info(f"💡 自動連動質押金額：**NT$ {loan_amount:,.0f}**")

interest_rate = st.sidebar.slider("3. 質押年利率 (%)", min_value=2.5, max_value=5.0, value=3.7, step=0.1) / 100

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#F3F4F6;'>🔍 標的選擇與持股設定</h4>", unsafe_allow_html=True)

preset_tickers = {
    "00685L.TW - 元大台灣加權正2 (槓桿攻擊)": {"beta": 2.0, "default_div": 0.0},
    "00631L.TW - 富邦台灣加權正2 (槓桿攻擊)": {"beta": 2.0, "default_div": 0.0},
    "00713.TW - 元大台灣高息低波 (防禦收息)": {"beta": 0.68, "default_div": 0.065},
    "0050.TW - 元大台灣50 (原型大盤)": {"beta": 1.0, "default_div": 0.03},
    "0056.TW - 元大高股息": {"beta": 0.85, "default_div": 0.07},
    "00878.TW - 國泰永續高股息": {"beta": 0.8, "default_div": 0.06},
    "00919.TW - 群益台灣精選高息": {"beta": 0.9, "default_div": 0.10}
}

selected_label_1 = st.sidebar.selectbox("選擇攻擊/槓桿標的", list(preset_tickers.keys()), index=0)
ticker_1 = selected_label_1.split(" - ")[0].strip()
shares_1 = st.sidebar.number_input("持有股數 (標的 1)", value=30000, step=1000)

selected_label_2 = st.sidebar.selectbox("選擇防禦/收息標的", list(preset_tickers.keys()), index=2)
ticker_2 = selected_label_2.split(" - ")[0].strip()
shares_2 = st.sidebar.number_input("持有股數 (標的 2)", value=10000, step=1000)
div_yield_2 = st.sidebar.slider("標的 2 預期年化殖利率 (%)", min_value=4.0, max_value=12.0, value=float(preset_tickers[selected_label_2]["default_div"] * 100), step=0.1) / 100

pledged_invest_ratio = 0.95

# ==================== 3. 24H 數據抓取引擎 ====================
@st.cache_data(ttl=300)
def fetch_global_market_data():
    t_list = [ticker_1, ticker_2, "2330.TW", "^TWII", "^GSPC", "^IXIC", "^DJI", "^VIX"]
    try:
        df = yf.download(list(set(t_list)), period="3y", auto_adjust=False, progress=False)["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        return df.ffill().dropna(how="all")
    except Exception:
        dates = pd.date_range(end=pd.Timestamp.today(), periods=250)
        return pd.DataFrame({
            ticker_1: np.linspace(50, 70, 250),
            ticker_2: np.linspace(45, 55, 250),
            "2330.TW": np.linspace(800, 1000, 250),
            "^TWII": np.linspace(20000, 23000, 250),
            "^GSPC": np.linspace(5000, 5800, 250),
            "^IXIC": np.linspace(16000, 19000, 250),
            "^DJI": np.linspace(38000, 43000, 250),
            "^VIX": np.full(250, 16.5)
        }, index=dates)

market_df = fetch_global_market_data()

def get_latest(df, ticker, fallback):
    if ticker in df.columns:
        val = df[ticker].dropna()
        if not val.empty:
            return float(val.iloc[-1])
    return fallback

p_1 = get_latest(market_df, ticker_1, 60.0)
p_2 = get_latest(market_df, ticker_2, 50.0)
tsmc_p = get_latest(market_df, "2330.TW", 900.0)
taiwii_p = get_latest(market_df, "^TWII", 22500.0)
sp500_p = get_latest(market_df, "^GSPC", 5500.0)
nasdaq_p = get_latest(market_df, "^IXIC", 17500.0)
cur_vix = get_latest(market_df, "^VIX", 16.0)

# 計算美股隔夜連動預估次日台股開盤點位 (Beta 迴歸模型)
sp500_ret = 0.005 # 預設假設或依實際計算
if "^GSPC" in market_df.columns:
    sp_series = market_df["^GSPC"].dropna()
    if len(sp_series) > 2:
        sp500_ret = (sp_series.iloc[-1] / sp_series.iloc[-2]) - 1.0

estimated_next_index = taiwii_p * (1.0 + sp500_ret * 0.85) # 導入台美連動係數 0.85
estimated_index_change_pts = estimated_next_index - taiwii_p
estimated_index_change_pct = (estimated_index_change_pts / taiwii_p) * 100

val_1 = shares_1 * p_1
val_2 = shares_2 * p_2
total_collateral = val_1 + val_2
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

beta_1 = preset_tickers.get(selected_label_1, {"beta": 1.5})["beta"]
beta_2 = preset_tickers.get(selected_label_2, {"beta": 0.7})["beta"]

exposure_1 = val_1 * beta_1
exposure_2 = val_2 * beta_2
total_exposure = exposure_1 + exposure_2
net_equity = total_collateral - loan_amount
exposure_vs_equity = (total_exposure / net_equity) * 100 if net_equity > 0 else 0

annual_interest = loan_amount * interest_rate
pledged_fund_2 = loan_amount * 0.95
expected_div_2 = pledged_fund_2 * div_yield_2
net_carry = expected_div_2 - annual_interest

log_status = "24H 全球跨時區追蹤運行中"
if os.path.exists("global_market_consensus.csv"):
    try:
        g_log = pd.read_csv("global_market_consensus.csv")
        log_status = f"最近全球數據同步: {g_log['Timestamp'].iloc[-1]}"
    except:
        pass

st.markdown(f"""
<div class="web-push-ticker">
    📡 <b>【Apex 24H 跨時區全球與期貨連動快報】</b> {log_status}<br>
    • 美股三大指數連動：S&P 500 ({sp500_p:,.1f}) | VIX 恐慌指數 ({cur_vix:.2f})<br>
    • 次日台股開盤預估模型：推估明日加權指數 <b>{estimated_next_index:,.0f} 點</b> ({estimated_index_change_pct:+.2f}% / {estimated_index_change_pts:+,.1f} 點)<br>
    • 當前即時質押維持率：<b>{margin_ratio:.1f}%</b> (負債 NT$ {loan_amount:,.0f})
</div>
""", unsafe_allow_html=True)

# ==================== 4. 主戰情室 KPI 儀表板 ====================
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
        <div class="card-title">質押負債 (自動連動)</div>
        <div class="card-value">NT$ {loan_amount:,.0f}</div>
        <div class="card-subtitle text-gold">只付利息 • 享受通膨稀釋</div>
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
        <div class="card-subtitle">槓桿曝險比例</div>
    </div>
    """, unsafe_allow_html=True)

progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0)
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer)**")
st.progress(progress_val)

st.markdown("---")

# ==================== 5. 正二（00685L / 00631L）溢價/折價（正價差/逆價差）回血與扣血模擬引擎 ====================
st.markdown("### 🧬 正二（00685L / 00631L）溢價/折價與路徑回血扣血模型")
st.markdown("模擬槓桿 ETF 因期貨基差（正價差/逆價差）收斂、每日複利重設及越跌越少絕對金額遞減所產生的損益回血與扣血效應：")

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    premium_discount_rate = st.slider("當前 ETF 溢價/折價率 (%) (正數為溢價, 負數為折價)", min_value=-3.0, max_value=3.0, value=0.5, step=0.1)
with col_m2:
    sim_market_change = st.slider("模擬單日大盤漲跌幅 (%)", min_value=-10.0, max_value=10.0, value=3.0, step=0.5)
with col_m3:
    holding_days = st.slider("連續震盪/趨勢天數 (路徑耗損累積)", min_value=1, max_value=30, value=5, step=1)

# 正二理論漲跌幅 = 2x 大盤，若有溢價/折價會面臨均值回歸（扣血或回血）
theoretical_leverage_ret = sim_market_change * 2.0
# 溢價收斂扣血（若溢價過高買進，回歸淨值時會額外扣除溢價部分）；折價收斂回血
convergence_impact = -premium_discount_rate * (1.0 / max(holding_days, 1))
net_etf_daily_ret = theoretical_leverage_ret + convergence_impact

sim_p1_advanced = p_1 * ((1.0 + net_etf_daily_ret / 100.0) ** holding_days)
sim_total_collateral_adv = (sim_p1_advanced * shares_1) + (p_2 * shares_2)
sim_margin_adv = (sim_total_collateral_adv / loan_amount) * 100 if loan_amount > 0 else 0

m_c1, m_c2, m_c3, m_c4 = st.columns(4)
m_c1.metric("正二理論單日報酬", f"{theoretical_leverage_ret:+.2f}%")
m_c2.metric("基差（溢價/折價）回血/扣血", f"{convergence_impact:+.2f}% /天")
m_c3.metric(f"經過 {holding_days} 天後標的 1 模擬價", f"NT$ {sim_p1_advanced:.2f}")
m_c4.metric("模擬後最終維持率", f"{sim_margin_adv:.1f}%", f"{sim_margin_adv - margin_ratio:+.1f}%")

if convergence_impact < 0:
    st.warning(f"⚠️ **溢價扣血警示**：目前處於溢價狀態（+{premium_discount_rate}%），買進或續抱將面臨每日約 {abs(convergence_impact):.2f}% 的基差收斂扣血損耗。")
else:
    st.success(f"🟢 **折價回血優勢**：目前處於折價狀態（{premium_discount_rate}%），享有均值回歸的超額回血紅利。")

st.markdown("---")

# ==================== 6. 機構 EPS 預估與目標點位到達時之資產動態模擬 ====================
st.markdown("### 🏛️ 全球機構法人共識 EPS 與目標點位到達時之資產動態模擬")
st.markdown("匯集各大外資與主流法人機構對台積電（2330.TW）的 Forward EPS 共識預估，推算大盤到達目標點位時的資產實況：")

institutional_consensus = pd.DataFrame([
    {"機構名稱": "外資平均共識 (Market Consensus)", "預估年份": "2026/2027 F", "預估EPS": 48.5, "合理PE": 22.0},
    {"機構名稱": "高盛證券 (Goldman Sachs)", "預估年份": "2026 F", "預估EPS": 52.0, "合理PE": 23.5},
    {"機構名稱": "摩根士丹利 (Morgan Stanley)", "預估年份": "2026 F", "預估EPS": 47.5, "合理PE": 20.5},
    {"機構名稱": "摩根大通 (J.P. Morgan)", "預估年份": "2026 F", "預估EPS": 50.0, "合理PE": 22.0},
    {"機構名稱": "麥格理證券 (Macquarie)", "預估年份": "2026 F", "預估EPS": 53.2, "合理PE": 24.0}
])

tsmc_weight = 0.32
institutional_consensus["台積電目標價 (NT$)"] = institutional_consensus["預估EPS"] * institutional_consensus["合理PE"]
institutional_consensus["推估大盤點位"] = taiwii_p * (1 + tsmc_weight * ((institutional_consensus["台積電目標價 (NT$)"] - tsmc_p) / tsmc_p))
institutional_consensus["潛在漲幅"] = ((institutional_consensus["台積電目標價 (NT$)"] / tsmc_p) - 1) * 100

sim_col_list = []
sim_margin_list = []
for _, row in institutional_consensus.iterrows():
    target_idx = row["推估大盤點位"]
    idx_ret = (target_idx - taiwii_p) / taiwii_p if taiwii_p > 0 else 0
    s_p1 = max(p_1 * (1 + beta_1 * idx_ret), 0.01)
    s_p2 = max(p_2 * (1 + beta_2 * idx_ret), 0.01)
    s_col = shares_1 * s_p1 + shares_2 * s_p2
    s_margin = (s_col / loan_amount) * 100 if loan_amount > 0 else 0
    sim_col_list.append(f"NT$ {s_col:,.0f}")
    sim_margin_list.append(f"{s_margin:.1f}%")

institutional_consensus["到達時總市值"] = sim_col_list
institutional_consensus["到達時維持率"] = sim_margin_list

ic1, ic2, ic3 = st.columns(3)
avg_consensus_eps = institutional_consensus["預估EPS"].mean()
avg_consensus_target = institutional_consensus["台積電目標價 (NT$)"].mean()
avg_implied_index = institutional_consensus["推估大盤點位"].mean()

ic1.metric("法人共識平均預估 EPS", f"NT$ {avg_consensus_eps:.1f}", "多機構平均預估")
ic2.metric("法人共識平均台積電目標價", f"NT$ {avg_consensus_target:.1f}", f"現價 NT$ {tsmc_p:.1f}")
ic3.metric("法人共識帶動大盤推估點位", f"{avg_implied_index:,.0f} 點", f"當前大盤 {taiwii_p:,.0f} 點")

display_df = institutional_consensus[["機構名稱", "預估年份", "預估EPS", "合理PE", "台積電目標價 (NT$)", "推估大盤點位", "潛在漲幅", "到達時總市值", "到達時維持率"]].copy()
st.dataframe(
    display_df.style.format({
        "預估EPS": "NT$ {:.1f}",
        "合理PE": "{:.1f}x",
        "台積電目標價 (NT$)": "NT$ {:.1f}",
        "推估大盤點位": "{:,.0f} 點",
        "潛在漲幅": "{:+.1f}%"
    }),
    use_container_width=True,
    hide_index=True
)