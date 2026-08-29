import streamlit as st
import requests
import plotly.graph_objects as go

# ------------------------------------
# Page Configuration
# ------------------------------------
st.set_page_config(
    page_title="AI Financial Intelligence",
    layout="wide"
)

# ------------------------------------
# Custom CSS
# ------------------------------------
st.markdown("""
<style>
.metric-card {
    background: #1a1d29;
    border: 1px solid #2d3142;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    text-align: left;
}
.metric-label {
    font-size: 13px;
    color: #8b8fa3;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 26px;
    font-weight: 600;
    color: #f5f5f7;
}
.badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
}
.badge-buy { background: #143d2b; color: #4ade80; }
.badge-hold { background: #3d3413; color: #facc15; }
.badge-sell { background: #3d1414; color: #f87171; }
.section-card {
    background: #1a1d29;
    border: 1px solid #2d3142;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.section-title {
    font-size: 16px;
    font-weight: 600;
    color: #f5f5f7;
    margin-bottom: 10px;
}
.risk-box {
    background: #3d2913;
    border-left: 3px solid #f59e0b;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    color: #fcd34d;
    font-size: 14px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("AI Financial Intelligence")
st.markdown("##### Multi-Agent Stock Analysis Platform")
st.divider()

# ------------------------------------
# Sidebar
# ------------------------------------
st.sidebar.title("Settings")

exchange = st.sidebar.selectbox("Exchange", ["NSE", "BSE", "NASDAQ"])
raw_ticker = st.sidebar.text_input("Stock symbol or company name", "")
analyze = st.sidebar.button("Analyze", use_container_width=True)

if analyze and not raw_ticker.strip():
    st.sidebar.warning("Please enter a stock symbol or company name.")
    analyze = False

API_URL = "https://ai-financial-intelligence.onrender.com/analyze"

# ------------------------------------
# Helpers
# ------------------------------------
def fmt_currency(val, symbol="₹"):
    if val is None:
        return "—"
    if val >= 1e12:
        return f"{symbol}{val/1e12:.2f}T"
    if val >= 1e7:
        return f"{symbol}{val/1e7:.2f}Cr"
    return f"{symbol}{val:,.2f}"


def badge_class(rec_text: str) -> str:
    rec_text = (rec_text or "").lower()
    if "buy" in rec_text:
        return "badge-buy"
    if "sell" in rec_text:
        return "badge-sell"
    return "badge-hold"


def metric_card(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------
# Analyze
# ------------------------------------
if analyze:
    with st.spinner(f"Analyzing {raw_ticker}..."):
        try:
            response = requests.post(
                API_URL,
                json={"ticker": raw_ticker, "exchange": exchange},
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend. Make sure uvicorn is running on port 8000.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("The backend took too long to respond. Try again.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"Backend returned an error: {e}")
            st.stop()
        except ValueError:
            st.error("Backend returned invalid JSON.")
            st.stop()

    if result.get("error"):
        st.error(f"Analysis failed: {result['error']}")
        st.stop()

    market = result.get("market", {})
    technical = result.get("technical", {})
    research = result.get("research", {})
    advisor = result.get("advisor", {})
    report = result.get("report", {})

    # --------------------------------
    # Header row: ticker + recommendation badge
    # --------------------------------
    rec_text = advisor.get("recommendation", "")
    rec_word = "Buy" if "buy" in rec_text.lower() else "Sell" if "sell" in rec_text.lower() else "Hold"

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {result.get('ticker', raw_ticker.upper())}")
    with col2:
        st.markdown(f'<div class="badge {badge_class(rec_text)}">{rec_word}</div>', unsafe_allow_html=True)

    st.write("")

    # --------------------------------
    # Metric cards
    # --------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Current price", fmt_currency(market.get("current_price")))
    with c2:
        metric_card("Market cap", fmt_currency(market.get("market_cap")))
    with c3:
        pe = market.get("pe_ratio")
        metric_card("P/E ratio", f"{pe:.2f}" if pe else "—")
    with c4:
        trend = technical.get("trend", "—")
        metric_card("Trend", trend.capitalize() if isinstance(trend, str) else "—")

    st.write("")

    # --------------------------------
    # Price chart
    # --------------------------------
    history = market.get("history", [])
    if history:
        dates = [h["date"] for h in history]
        closes = [h["close"] for h in history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=closes, mode="lines", fill="tozeroy",
            line=dict(color="#4ade80", width=2),
            fillcolor="rgba(74, 222, 128, 0.08)",
        ))
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, color="#8b8fa3"),
            yaxis=dict(showgrid=True, gridcolor="#2d3142", color="#8b8fa3"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------
    # Technical + Research side by side
    # --------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Technical analysis</div>', unsafe_allow_html=True)
        if technical.get("error"):
            st.write(technical["error"])
        else:
            st.write(f"SMA 20: **{technical.get('sma_20', '—')}**")
            st.write(f"SMA 50: **{technical.get('sma_50', '—')}**")
            st.write(f"Latest close: **{technical.get('latest_close', '—')}**")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-title">Research summary</div>', unsafe_allow_html=True)
        sources = research.get("sources_used", 0)
        if sources > 0:
            st.write(research.get("summary", ""))
            st.caption(f"Based on {sources} retrieved source(s)")
        else:
            st.info("No recent news coverage found for this ticker via available data sources. The recommendation above is based on technical indicators only.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------
    # Advisor recommendation
    # --------------------------------
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">AI recommendation</div>', unsafe_allow_html=True)
    st.write(rec_text if rec_text else "No recommendation available.")
    key_risk = advisor.get("key_risk")
    if key_risk:
        st.markdown(f'<div class="risk-box">Key risk: {key_risk}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------
    # Final report
    # --------------------------------
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Final report</div>', unsafe_allow_html=True)
    report_text = report.get("final", "No report available") if isinstance(report, dict) else str(report)
    st.markdown(report_text)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Raw price history"):
        st.json(history)

else:
    st.info("Enter a stock symbol or company name in the sidebar and click Analyze to get started.")
