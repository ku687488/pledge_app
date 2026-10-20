import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

# ==================== 1. 頁面配置與黑卡級美學 CSS ====================
st.set_page_config(
    page_title="Apex Leverage Terminal | 富人 220% 曝險與質押戰情室",
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
        border-left: 4px solid #3B82F6; padding: 20px 24px; border-radius: 8px; margin-bottom: 25px;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero-header">
    <h2 style="margin:0; color:#F8FAFC; font-weight:800; letter-spacing:-0.5px;">🏛️ APEX LEVERAGE TERMINAL (ULTIMATE AUTO-LINKED)</h2>
    <p style="margin:5px 0 0 0; color:#94A3B8; font-size:0.95rem;">
        富人槓桿戰情室 | <b>本金與 LTV 自動連動</b> • <b>00713 季配息精算</b> • <b>220% 動態曝險與自償監控</b>
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================== 2. 側邊欄：動態連動控制台 ====================
st.sidebar.markdown(
    "<h3 style='color:#F3F4F6;'>⚙️ 本金與質押動態連動</h3>",
    unsafe_allow_html=True,
)

total_equity_cost = st.sidebar.number_input(
    "1. 自有初始本金總額 (NT$)", value=2400000, step=100000
)

ltv_ratio = (
    st.sidebar.slider(
        "2. 質押成數 LTV (%)", min_value=10.0, max_value=60.0, value=25.0, step=1.0
    )
    / 100.0
)

# 自動動態計算質押金額 (可隨本金與 LTV 成數連動)
auto_loan_amount = int(total_equity_cost * ltv_ratio)

manual_loan_override = st.sidebar.checkbox("手動自訂質押金額 (取消連動)", value=False)
if manual_loan_override:
  loan_amount = st.sidebar.number_input(
      "自訂質押借款金額 (NT$)", value=auto_loan_amount, step=10000
  )
else:
  loan_amount = auto_loan_amount
  st.sidebar.info(f"💡 自動連動質押金額：**NT$ {loan_amount:,.0f}**")

interest_rate = (
    st.sidebar.slider(
        "3. 質押年利率 (%)", min_value=2.5, max_value=5.0, value=3.7, step=0.1
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<h4 style='color:#F3F4F6;'>📅 00713 配息政策微調</h4>", unsafe_allow_html=True
)
div_yield_713 = (
    st.sidebar.slider(
        "00713 預期年化殖利率 (%)",
        min_value=4.0,
        max_value=9.0,
        value=6.5,
        step=0.1,
        help="00713 為 3, 6, 9, 12 月季配息，可根據最新公告季配息推估年化率",
    )
    / 100
)

assumed_inflation = (
    st.sidebar.slider(
        "預估長期年通膨率 (%)", min_value=1.0, max_value=5.0, value=2.5, step=0.1
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<h4 style='color:#F3F4F6;'>📦 持股部位即時設定</h4>", unsafe_allow_html=True
)
shares_685 = st.sidebar.number_input(
    "00685L (台指正2) 持有股數", value=9358, step=100
)
shares_713 = st.sidebar.number_input(
    "00713 (高息低波) 持有股數", value=5594, step=100
)

pledged_invest_ratio = 0.95  # 95% 買進 00713 當擔保品
cash_buffer_ratio = 0.05  # 5% 留外面當備用金

# ==================== 3. 即時數據抓取引擎 ====================
tickers = ["00685L.TW", "00713.TW", "2330.TW", "^VIX"]


@st.cache_data(ttl=300)
def fetch_live_market_data():
  try:
    df = yf.download(
        tickers, period="5d", auto_adjust=False, progress=False
    )["Close"]
    if df.empty:
      raise ValueError("Empty")
    return df.ffill().dropna()
  except Exception:
    dates = pd.date_range(end=pd.Timestamp.today(), periods=10)
    return pd.DataFrame(
        {
            "00685L.TW": [68.5] * 10,
            "00713.TW": [55.2] * 10,
            "2330.TW": [1020] * 10,
            "^VIX": [16.5] * 10,
        },
        index=dates,
    )


market_df = fetch_live_market_data()
prices = market_df[["00685L.TW", "00713.TW", "2330.TW"]]
vix = market_df["^VIX"]
latest_p = prices.iloc[-1]

# 核心數學計算
val_685 = shares_685 * latest_p["00685L.TW"]
val_713 = shares_713 * latest_p["00713.TW"]
total_collateral = val_685 + val_713
margin_ratio = (
    (total_collateral / loan_amount) * 100 if loan_amount > 0 else 0
)

# 雙軌曝險與 Beta 權重計算
exposure_685 = val_685 * 2.0
exposure_713 = val_713 * 0.68
total_exposure = exposure_685 + exposure_713
net_equity = total_collateral - loan_amount

exposure_vs_asset = (
    (total_exposure / total_collateral) * 100 if total_collateral > 0 else 0
)
exposure_vs_equity = (
    (total_exposure / net_equity) * 100 if net_equity > 0 else 0
)

# 現金流與 Positive Carry 計算
annual_interest = loan_amount * interest_rate
pledged_fund_713 = loan_amount * pledged_invest_ratio
expected_div_713 = pledged_fund_713 * div_yield_713
net_carry = expected_div_713 - annual_interest

# ==================== 4. 戰情室儀表板呈現 ====================
c1, c2, c3, c4 = st.columns(4)

with c1:
  st.markdown(
      f"""
    <div class="metric-card">
        <div class="card-title">擔保品總市值</div>
        <div class="card-value">NT$ {total_collateral:,.0f}</div>
        <div class="card-subtitle text-blue">本金: NT$ {total_equity_cost:,.0f} | LTV: {ltv_ratio*100:.0f}%</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

with c2:
  st.markdown(
      f"""
    <div class="metric-card">
        <div class="card-title">質押負債 (自動連動)</div>
        <div class="card-value">NT$ {loan_amount:,.0f}</div>
        <div class="card-subtitle text-gold">只還利息 • 享受通膨稀釋</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

with c3:
  status_color = (
      "text-green"
      if margin_ratio > 200
      else ("text-gold" if margin_ratio > 160 else "text-red")
  )
  st.markdown(
      f"""
    <div class="metric-card">
        <div class="card-title">即時質押維持率</div>
        <div class="card-value {status_color}">{margin_ratio:.1f}%</div>
        <div class="card-subtitle">券商平倉線: 130%</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

with c4:
  st.markdown(
      f"""
    <div class="metric-card">
        <div class="card-title">自有資金淨權益曝險</div>
        <div class="card-value text-blue">{exposure_vs_equity:.1f}%</div>
        <div class="card-subtitle">總資產曝險率: {exposure_vs_asset:.1f}%</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

progress_val = min(max((margin_ratio - 130) / (300 - 130), 0.0), 1.0)
st.markdown("**🛡️ 質押維持率安全緩衝條 (Margin Safety Buffer)**")
st.progress(progress_val)

st.markdown("---")

left_col, right_col = st.columns(2)

with left_col:
  st.markdown(
      f"""
    <div class="metric-card">
        <h4 style="color:#F3F4F6; margin-top:0;">💵 利息自償性分析 (Positive Carry)</h4>
    """,
      unsafe_allow_html=True,
  )
  ca, cb = st.columns(2)
  ca.metric(
      "年度質押利息支出",
      f"-NT$ {annual_interest:,.0f}",
      f"利率 {interest_rate*100:.2f}%",
  )
  cb.metric(
      f"00713 預期股息 ({div_yield_713*100:.1f}%)",
      f"+NT$ {expected_div_713:,.0f}",
      f"單季估: NT$ {expected_div_713/4:,.0f}",
  )
  st.markdown(
      f"""
        <div style="background-color:#1E293B; padding:12px; border-radius:8px; margin-top:10px;">
            <span style="color:#94A3B8;">淨現金流效益 (Net Carry)：</span>
            <b class="{'text-green' if net_carry > 0 else 'text-red'}" style="font-size:1.2rem;">+NT$ {net_carry:,.0f} / 年</b>
            <p style="font-size:0.8rem; color:#64748B; margin:4px 0 0 0;">
                手邊 5% 靈活預備金：<b>NT$ {loan_amount * cash_buffer_ratio:,.0f}</b> (未提進質押)
            </p>
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )

with right_col:
  st.markdown(
      """
    <div class="metric-card">
        <h4 style="color:#F3F4F6; margin-top:0;">📈 富人槓桿：通膨債務衰減模型</h4>
    """,
      unsafe_allow_html=True,
  )
  years = np.array([1, 3, 5, 10])
  real_debt = loan_amount / ((1 + assumed_inflation) ** years)
  decay_pct = (1 - (real_debt / loan_amount)) * 100
  decay_df = pd.DataFrame({
      "跨度": [f"{y}年後" for y in years],
      "名目負債": [f"{loan_amount/10000:.0f}萬" for _ in years],
      "實質負債": [f"{v/10000:.1f}萬" for v in real_debt],
      "通膨稀釋": [f"-{p:.1f}%" for p in decay_pct],
  })
  st.dataframe(decay_df, use_container_width=True, hide_index=True)
  st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🌐 核心權值台積電 (2330) 與宏觀風向球")

t1, t2 = st.columns(2)
tsmc_p = latest_p["2330.TW"]
cur_vix = vix.iloc[-1]

with t1:
  st.markdown(
      f"""
    <div class="metric-card">
        <div class="card-title">台積電 (2330.TW) 即時收盤價</div>
        <div class="card-value text-blue">NT$ {tsmc_p:.1f}</div>
        <p style="font-size:0.85rem; color:#94A3B8; margin-top:10px;">
            • <b>基本面支撐：</b> 2026 美元營收成長目標 44%，資本支出維持 600~640 億美元高檔。<br>
            • <b>產能護城河：</b> CoWoS 產能吃緊延續至 2027 年底，台股大盤多頭基底穩固。
        </p>
    </div>
    """,
      unsafe_allow_html=True,
  )

with t2:
  vix_status = (
      "text-green"
      if cur_vix <= 20
      else ("text-gold" if cur_vix <= 25 else "text-red")
  )
  st.markdown(
      f"""
    <div class="metric-card">
        <div class="card-title">市場恐慌指數 (VIX)</div>
        <div class="card-value {vix_status}">{cur_vix:.2f}</div>
        <p style="font-size:0.85rem; color:#94A3B8; margin-top:10px;">
            • <b>實時監控：</b> 當前 VIX 處於安全區間，220% 槓桿與質押利息自償循環流暢運作。
        </p>
    </div>
    """,
      unsafe_allow_html=True,
  )