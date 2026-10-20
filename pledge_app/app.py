import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import datetime

# ==================== 1. 頁面配置與黑卡級美學 CSS ====================
st.set_page_config(
    page_title="Apex Leverage Terminal | 家族辦公室量化戰情室",
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
    .alert-banner-red {
        background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-left: 6px solid #EF4444;
        padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; color: #FCA5A5; font-weight: 600;
    }
    .alert-banner-gold {
        background: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; border-left: 6px solid #F59E0B;
        padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; color: #FCD34D; font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero-header">
    <h2 style="margin:0; color:#F8FAFC; font-weight:800; letter-spacing:-0.5px;">🏛️ APEX FAMILY OFFICE TERMINAL</h2>
    <p style="margin:5px 0 0 0; color:#94A3B8; font-size:0.95rem;">
        私人家族辦公室極致量化戰情室 | 動態質押自償 • 機構級壓力測試 • 歷史回測與複利模擬
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. 側邊欄：動態控制台與自訂標的 ====================
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
st.sidebar.markdown("<h4 style='color:#F3F4F6;'>📦 動態自訂持股與代號設定</h4>", unsafe_allow_html=True)
ticker_1 = st.sidebar.text_input("攻擊/槓桿標的代號", value="00685L.TW")
shares_1 = st.sidebar.number_input("持有股數 (標的 1)", value=30000, step=1000)

ticker_2 = st.sidebar.text_input("防禦/收息標的代號", value="00713.TW")
shares_2 = st.sidebar.number_input("持有股數 (標的 2)", value=10000, step=1000)
div_yield_2 = st.sidebar.slider("標的 2 預期年化殖利率 (%)", min_value=4.0, max_value=9.0, value=6.5, step=0.1) / 100

pledged_invest_ratio = 0.95
cash_buffer_ratio = 0.05

# ==================== 3. 即時與歷史數據抓取 Engine ====================
base_tickers = [ticker_1, ticker_2, "2330.TW", "^VIX"]

@st.cache_data(ttl=300)
def fetch_live_and_history(t1, t2):
    t_list = list(set([t1, t2, "2330.TW", "^VIX"]))
    try:
        df = yf.download(t_list, period="3y", auto_adjust=False, progress=False)["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        return df.ffill().dropna(how="all")
    except Exception:
        dates = pd.date_range(end=pd.Timestamp.today(), periods=250)
        return pd.DataFrame({
            t1: np.linspace(50, 70, 250),
            t2: np.linspace(45, 55, 250),
            "2330.TW": np.linspace(800, 1000, 250),
            "^VIX": np.full(250, 16.5)
        }, index=dates)

market_df = fetch_live_and_history(ticker_1, ticker_2)

# 安全取得即時價格
def get_latest_price(df, ticker, fallback):
    if ticker in df.columns:
        val = df[ticker].dropna()
        if not val.empty:
            return float(val.iloc[-1])
    return fallback

p_1 = get_latest_price(market_df, ticker_1, 60.0)
p_2 = get_latest_price(market_df, ticker_2, 50.0)
tsmc_p = get_latest_price(market_df, "2330.TW", 900.0)
cur_vix = get_latest_price(market_df, "^VIX", 16.0)

# 核心即時數據計算
val_1 = shares_1 * p_1
val_2 = shares_2 * p_2
total_collateral = val_1 + val_2
margin_ratio = (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

# 假設標的1 Beta=2.0, 標的2 Beta=0.68
exposure_1 = val_1 * 2.0
exposure_2 = val_2 * 0.68
total_exposure = exposure_1 + exposure_2
net_equity = total_collateral - loan_amount

exposure_vs_asset = (total_exposure / total_collateral) * 100 if total_collateral > 0 else 0
exposure_vs_equity = (total_exposure / net_equity) * 100 if net_equity > 0 else 0

annual_interest = loan_amount * interest_rate
pledged_fund_2 = loan_amount * pledged_invest_ratio
expected_div_2 = pledged_fund_2 * div_yield_2
net_carry = expected_div_2 - annual_interest

# ==================== 4. 高亮度動態警報 Banner ====================
if margin_ratio < 140:
    st.markdown(f"""
    <div class="alert-banner-red">
        🚨 【危急警報】即時質押維持率已跌至 {margin_ratio:.1f}%！逼近 130% 平倉線，請立即注意斷頭風險並準備補充保證金！
    </div>
    """, unsafe_allow_html=True)
elif margin_ratio < 165:
    st.markdown(f"""
    <div class="alert-banner-gold">
        ⚠️ 【安全警示】即時維持率為 {margin_ratio:.1f}%，處於防禦警戒區間，請持續關注市場波動。
    </div>
    """, unsafe_allow_html=True)

# ==================== 5. 主戰情室 KPI 儀表板 ====================
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
        <div class="card-subtitle">總資產曝險率: {exposure_vs_asset:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0)
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer)**")
st.progress(progress_val)

st.markdown("---")

# ==================== 6. 極端壓力測試模擬器 (主畫面直接操作) ====================
st.markdown("### 🚨 機構級黑天鵝極端壓力測試 (Market Crash Stress Test)")
st.markdown("模擬大盤單日或短期急凍下跌時，對整體擔保品市值與維持率的實時衝擊：")

drop_pct = st.slider("模擬大盤崩盤跌幅 (%)", min_value=0, max_value=50, value=20, step=5)

sim_val_1 = val_1 * (1 - (drop_pct / 100.0) * 2.0)
sim_val_1 = max(sim_val_1, 0)
sim_val_2 = val_2 * (1 - (drop_pct / 100.0) * 0.68)
sim_total_collateral = sim_val_1 + sim_val_2
sim_margin_ratio = (sim_total_collateral / loan_amount) * 100 if loan_amount > 0 else 0

required_collateral_130 = loan_amount * 1.30
margin_call_gap = max(required_collateral_130 - sim_total_collateral, 0)

s1, s2, s3, s4 = st.columns(4)
s1.metric("大盤跌幅情境", f"-{drop_pct}%")
s2.metric("崩盤後擔保品總市值", f"NT$ {sim_total_collateral:,.0f}", f"-NT$ {total_collateral - sim_total_collateral:,.0f}")
s3.metric("壓力測試後維持率", f"{sim_margin_ratio:.1f}%", f"{sim_margin_ratio - margin_ratio:.1f}%")
s4.metric("需補繳保證金 (預防追繳)", f"NT$ {margin_call_gap:,.0f}", "安全 (無需補錢)" if margin_call_gap == 0 else "警報 (需動用預備金)")

if sim_margin_ratio > 160:
    st.success(f"🟢 **壓力測試通過！** 大盤重挫 {drop_pct}% 時，維持率仍高於 160% 安全警戒線。")
elif sim_margin_ratio > 130:
    st.warning(f"🟡 **維持率警示！** 大盤重挫 {drop_pct}% 時，維持率降至 {sim_margin_ratio:.1f}%，逼近平倉線。")
else:
    st.error(f"🔴 **斷頭風險警報！** 大盤重挫 {drop_pct}% 時，維持率跌破 130%！需補充保證金 NT$ {margin_call_gap:,.0f} 元！")

st.markdown("---")

# ==================== 7. 收納式區塊：歷史回測與 MDD ====================
with st.expander("📊 點擊展開：歷史資產走勢與最大回檔對比 (Historical Backtest & MDD)", expanded=False):
    if ticker_1 in market_df.columns and ticker_2 in market_df.columns:
        hist_returns = market_df[[ticker_1, ticker_2]].pct_change().dropna()
        port_daily_ret = hist_returns[ticker_1] * 0.45 + hist_returns[ticker_2] * 0.55
        cum_port = (1 + port_daily_ret).cumprod()
        cum_1 = (1 + hist_returns[ticker_1]).cumprod()
        cum_2 = (1 + hist_returns[ticker_2]).cumprod()

        chart_df = pd.DataFrame({
            "槓桿質押組合": cum_port,
            f"純 {ticker_1}": cum_1,
            f"純 {ticker_2}": cum_2
        }, index=hist_returns.index)

        st.line_chart(chart_df)

        def calc_mdd(cum_series):
            peak = cum_series.cummax()
            dd = (cum_series - peak) / peak
            return dd.min() * 100

        h1, h2, h3 = st.columns(3)
        h1.metric("槓桿質押組合最大回檔 (MDD)", f"{calc_mdd(cum_port):.2f}%")
        h2.metric(f"純 {ticker_1} 最大回檔", f"{calc_mdd(cum_1):.2f}%")
        h3.metric(f"純 {ticker_2} 最大回檔", f"{calc_mdd(cum_2):.2f}%")
    else:
        st.info("歷史回測資料載入中或代號無歷史數據。")

# ==================== 8. 收納式區塊：現金流自償性與複利模擬 ====================
with st.expander("💵 點擊展開：Positive Carry 現金流自償與股息複利滾存試算", expanded=False):
    lc, rc = st.columns(2)
    with lc:
        st.metric("年度質押利息支出", f"-NT$ {annual_interest:,.0f}", f"利率 {interest_rate*100:.2f}%")
        st.metric(f"標的 2 預期股息收益", f"+NT$ {expected_div_2:,.0f}", f"殖利率 {div_yield_2*100:.1f}%")
        st.markdown(f"<b class='{'text-green' if net_carry > 0 else 'text-red'}'>淨現金流效益 (Net Carry)：+NT$ {net_carry:,.0f} / 年</b>", unsafe_allow_html=True)
    with rc:
        comp_years = np.array([1, 3, 5, 10])
        compounded_values = [net_carry * (((1 + div_yield_2) ** y - 1) / div_yield_2) if net_carry > 0 else 0 for y in comp_years]
        comp_df = pd.DataFrame({
            "累積時間": [f"{y} 年後" for y in comp_years],
            "淨現金流複利滾存總額": [f"NT$ {val:,.0f}" for val in compounded_values]
        })
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

# ==================== 9. 收納式區塊：宏觀風向球與一鍵 CSV 匯出 ====================
with st.expander("📈 點擊展開：宏觀風向球 (台積電/VIX) 與資料報表匯出", expanded=False):
    m1, m2 = st.columns(2)
    with m1:
        st.metric("台積電 (2330.TW) 即時收盤價", f"NT$ {tsmc_p:.1f}")
        st.markdown("• **基本面支撐：** 營收與 CoWoS 產能吃緊延續，台股大盤多頭基底穩固。")
    with m2:
        vix_status = "text-green" if cur_vix <= 20 else ("text-gold" if cur_vix <= 25 else "text-red")
        st.markdown(f"<div class='card-value {vix_status}'>VIX: {cur_vix:.2f}</div>", unsafe_allow_html=True)
        st.markdown("• **市場情緒：** 實時監控恐慌指數，確保槓桿循環安全運行。")
    
    st.markdown("---")
    # 一鍵 CSV 匯出功能
    export_data = pd.DataFrame({
        "項目": ["自有本金", "質押負債", "擔保品總市值", "即時維持率", "模擬崩盤跌幅", "模擬壓力維持率", "淨現金流 Net Carry"],
        "數值": [total_equity_cost, loan_amount, total_collateral, f"{margin_ratio:.1f}%", f"-{drop_pct}%", f"{sim_margin_ratio:.1f}%", net_carry]
    })
    csv = export_data.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載完整家族辦公室量化資產報表 (CSV)",
        data=csv,
        file_name=f"apex_leverage_report_{datetime.date.today()}.csv",
        mime='text/csv',
    )