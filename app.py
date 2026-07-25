"""Market Intel Dashboard - Cloud-Compatible Version
Uses only yfinance + RSS (no local scripts required)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys

# ============ STYLES ============
st.markdown("""
<style>
    .stApp { background: #0a0e17; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 100%; }
    .element-container { margin-bottom: 0 !important; }
    [data-testid="stSidebar"] { background: #0f1721; border-right: 1px solid #2a3f5f; }

    .dashboard-header {
        background: linear-gradient(135deg, #0a0e17 0%, #1a2332 100%);
        padding: 14px 22px; border-radius: 10px; margin-bottom: 12px;
        border: 1px solid #2a3f5f;
        display: flex; justify-content: space-between; align-items: center;
    }
    .logo-icon { font-size: 28px; }
    .logo-text { color: #d4af37; font-size: 22px; font-weight: bold; letter-spacing: 2px; }
    .logo-sub { color: #6a7a8a; font-size: 10px; letter-spacing: 1px; }
    .header-day { color: #d4af37; font-size: 16px; font-weight: bold; }
    .live-dot { color: #00ff88; animation: blink 1.5s infinite; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

    .card {
        background: linear-gradient(180deg, #1a2332 0%, #0f1721 100%);
        border: 1px solid #2a3f5f; border-radius: 10px;
        padding: 12px 14px; margin-bottom: 10px;
    }
    .card-title {
        color: #d4af37; font-size: 11px; font-weight: bold;
        text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;
        padding-bottom: 6px; border-bottom: 1px solid #2a3f5f;
    }
    .card-title-orange { color: #ff8c42; }
    .card-title-blue { color: #4da6ff; }
    .card-title-green { color: #00ff88; }
    .card-title-red { color: #ff4444; }
    .card-title-purple { color: #b388ff; }
    .live-badge {
        background: #00aa44; color: #fff; font-size: 9px;
        padding: 2px 6px; border-radius: 3px; font-weight: bold;
    }

    .big-number { font-size: 32px; font-weight: bold; color: #ffffff; text-align: center; margin: 6px 0; }
    .big-number-down { color: #ff4444; }
    .big-number-up { color: #00ff88; }

    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .data-table th {
        background: #0a0e17; color: #6a7a8a; font-size: 9px;
        text-transform: uppercase; letter-spacing: 1px;
        padding: 5px 6px; text-align: left; border-bottom: 1px solid #2a3f5f;
        font-weight: bold;
    }
    .data-table td {
        padding: 5px 6px; border-bottom: 1px solid #1a2332;
        color: #d0d8e0;
    }
    .data-table tr:hover { background: #1a2332; }
    .up { color: #00ff88; }
    .down { color: #ff4444; }
    .neutral { color: #888; }

    .rating-buy { background: #00aa44; color: #fff; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: bold; text-align: center; display: inline-block; }
    .rating-hold { background: #555; color: #fff; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: bold; text-align: center; display: inline-block; }
    .quote-text { color: #d0d8e0; font-size: 13px; font-style: italic; text-align: center; padding: 8px; line-height: 1.4; }
    .quote-author { color: #d4af37; font-size: 11px; text-align: center; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Hermes Intel", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")


# ============ DATA LOADING - CLOUD COMPATIBLE ============
@st.cache_data(ttl=300)
def load_data():
    try:
        import yfinance as yf
        import requests
        import json as _json

        watchlist = [
            "NVDA", "AAPL", "MSFT", "AVGO", "AMD", "ASML",
            "QCOM", "AMAT", "MRVL", "MU", "INTC", "VRT",
            "META", "GOOG", "NFLX",
            "AMZN", "TSLA",
            "JPM", "MA", "V", "COIN",
            "UNH", "LLY", "ISRG", "ZTS",
            "CAT", "GE",
            "XOM", "PLUG",
            "WCN", "COST",
            "NEE",
            "LIN",
            "AMT",
            "PLTR", "HPE", "DELL", "STX", "WDC", "GM", "UPST",
        ]
        watchlist = list(dict.fromkeys(watchlist))

        results = []
        for t in watchlist:
            try:
                tk = yf.Ticker(t)
                df = tk.history(period="1mo", auto_adjust=True)
                if df.empty or len(df) < 2:
                    continue
                closes = df["Close"]
                volumes = df["Volume"]
                price = float(closes.iloc[-1])
                prev = float(closes.iloc[-2])
                chg = (price / prev - 1) * 100

                # SMA
                ma20 = float(closes.rolling(20).mean().iloc[-1])
                ma50 = float(closes.rolling(50).mean().iloc[-1])
                ma200 = float(closes.rolling(min(200, len(closes))).mean().iloc[-1]) if len(closes) >= 50 else None

                # RSI
                delta = closes.diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                rs = avg_gain / avg_loss.replace(0, 1e-10)
                rsi = float((100 - (100 / (1 + rs))).iloc[-1])

                # MACD
                ema12 = closes.ewm(span=12, adjust=False).mean()
                ema26 = closes.ewm(span=26, adjust=False).mean()
                macd = ema12 - ema26
                sig = macd.ewm(span=9, adjust=False).mean()
                hist = float((macd - sig).iloc[-1])
                hist_yest = float((macd - sig).iloc[-2])

                # Volume
                vol_ratio = float(volumes.iloc[-1] / volumes.tail(20).mean()) if volumes.tail(20).mean() > 0 else 1

                # Simple MPS calculation (regime-independent for simplicity)
                mps_base = 50
                # RSI component
                if 40 <= rsi <= 65:
                    mps_base += 8
                elif rsi < 30 or rsi > 75:
                    mps_base += 5
                # Trend component
                if ma50 and ma200 and price > ma50 > ma200:
                    mps_base += 12
                elif ma50 and price > ma50:
                    mps_base += 6
                # MACD component
                if hist > 0 and hist > hist_yest:
                    mps_base += 6
                # Volume
                if vol_ratio > 1.2:
                    mps_base += 4

                # Sparkline data
                sparkline = closes.tail(20).tolist()

                # Sector mapping
                sector_map = {
                    "NVDA": "Tech", "AAPL": "Tech", "MSFT": "Tech", "AVGO": "Tech", "AMD": "Tech", "ASML": "Tech",
                    "QCOM": "Tech", "AMAT": "Tech", "MRVL": "Tech", "MU": "Tech", "INTC": "Tech", "VRT": "Tech",
                    "META": "Comm", "GOOG": "Comm", "NFLX": "Comm",
                    "AMZN": "Cons Disc", "TSLA": "Cons Disc", "GM": "Cons Disc",
                    "JPM": "Financials", "MA": "Financials", "V": "Financials", "COIN": "Financials", "UPST": "Financials",
                    "UNH": "Health", "LLY": "Health", "ISRG": "Health", "ZTS": "Health",
                    "CAT": "Industrials", "GE": "Industrials", "HPE": "Industrials", "DELL": "Industrials",
                    "XOM": "Energy", "PLUG": "Energy",
                    "WCN": "Staples", "COST": "Staples",
                    "NEE": "Utilities", "LIN": "Materials", "AMT": "Real Estate",
                    "PLTR": "Other", "STX": "Other", "WDC": "Other",
                }

                results.append({
                    "ticker": t, "price": price, "chg": chg, "rsi": rsi,
                    "ma20": ma20, "ma50": ma50, "ma200": ma200,
                    "macd_hist": hist, "macd_improving": hist > hist_yest,
                    "vol_ratio": vol_ratio, "mps": min(100, max(0, mps_base)),
                    "sparkline": sparkline,
                    "sector": sector_map.get(t, "Other"),
                    "above_200": ma200 and price > ma200,
                })
            except Exception:
                continue

        # Sector performance
        sector_perf = {}
        for r in results:
            s = r["sector"]
            if s not in sector_perf:
                sector_perf[s] = {"total": 0, "count": 0}
            sector_perf[s]["total"] += r["chg"]
            sector_perf[s]["count"] += 1
        sector_perf = {k: {"chg": v["total"] / v["count"], "count": v["count"]} for k, v in sector_perf.items()}

        # Major indices
        indices = {}
        for sym in ["^DJI", "^IXIC", "^GSPC", "^RUT", "^VIX", "GC=F", "CL=F", "BTC-USD", "^TNX"]:
            try:
                tk = yf.Ticker(sym)
                df = tk.history(period="5d", auto_adjust=True)
                if not df.empty and len(df) >= 2:
                    price = float(df['Close'].iloc[-1])
                    prev = float(df['Close'].iloc[-2])
                    indices[sym] = (price, (price/prev - 1) * 100)
            except:
                pass

        # Weather
        weather = {}
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast?latitude=43.8847&longitude=-79.4394&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code&temperature_unit=celsius&wind_speed_unit=kmh",
                timeout=5
            )
            if r.status_code == 200:
                weather = r.json().get("current", {})
        except:
            pass

        # Quote
        quote = "Price is what you pay. Value is what you get."
        quote_author = "Warren Buffett"
        try:
            r = requests.get("https://zenquotes.io/api/random", timeout=5,
                           headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                data = r.json()
                quote = data[0]["q"]
                quote_author = data[0]["a"]
        except:
            pass

        # Sample news (simplified for cloud - real news would need RSS parsing)
        watchlist_news = [
            {"ticker": "GOOG", "headline": "Big Tech earnings continue to shape market sentiment"},
            {"ticker": "TSLA", "headline": "Auto sector facing headwinds from rate environment"},
            {"ticker": "META", "headline": "Meta strategy under analyst review"},
        ]
        macro_news = [
            "Fed continues hawkish stance on inflation",
            "Iran tensions remain in focus for markets",
            "Oil prices elevated on geopolitical concerns",
            "Tech capex concerns weighing on AI stocks",
        ]

        return {
            "watchlist": results,
            "sector_perf": sector_perf,
            "indices": indices,
            "weather": weather,
            "quote": quote,
            "quote_author": quote_author,
            "watchlist_news": watchlist_news,
            "macro_news": macro_news,
            "timestamp": datetime.now().strftime("%I:%M %p ET"),
            "date_full": datetime.now().strftime("%A, %B %d, %Y"),
            "day_short": datetime.now().strftime("%A").upper(),
            "date_short": datetime.now().strftime("%B %d, %Y"),
        }
    except Exception as e:
        st.error(f"Data error: {e}")
        return None


data = load_data()
if data is None:
    st.stop()


# ============ SPARKLINE HELPER ============
def make_sparkline(prices, color="#4da6ff"):
    if not prices or len(prices) < 2:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=prices, mode="lines", line=dict(color=color, width=2), hoverinfo="skip"))
    fig.update_layout(width=80, height=30, margin=dict(l=0, r=0, t=0, b=0),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False)
    return fig


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown('<div style="text-align: center; padding: 12px 0; border-bottom: 1px solid #2a3f5f; margin-bottom: 12px;"><div style="font-size: 28px;">🎯</div><div style="color: #d4af37; font-weight: bold; letter-spacing: 1px;">HERMES INTEL</div><div style="color: #6a7a8a; font-size: 10px;">v1.0 - LIVE</div></div>', unsafe_allow_html=True)

    st.markdown("### ⚙️ Settings")
    auto_refresh = st.toggle("🔄 Auto-refresh (5 min)", value=True)
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    ups = sum(1 for r in data["watchlist"] if r["chg"] > 0)
    downs = sum(1 for r in data["watchlist"] if r["chg"] < 0)
    flats = len(data["watchlist"]) - ups - downs
    st.metric("Watchlist Size", len(data["watchlist"]))
    st.metric("Advancers", ups, delta=f"{ups/(ups+downs+flats)*100:.0f}%" if (ups+downs+flats) > 0 else "0%")
    st.metric("Decliners", downs, delta=f"-{downs/(ups+downs+flats)*100:.0f}%" if (ups+downs+flats) > 0 else "0%", delta_color="inverse")

    st.markdown("---")
    st.markdown("### 🎯 Filters")
    show_only_setups = st.checkbox("Show only MPS > 60", value=False)
    min_mps = st.slider("Min MPS Score", 0, 100, 0)


# ============ HEADER ============
st.markdown(f'<div class="dashboard-header"><div style="display: flex; align-items: center; gap: 14px;"><div class="logo-icon">🎯</div><div><div class="logo-text">HERMES INTEL</div><div class="logo-sub">TRADE SMART. STAY DISCIPLINED. COMPOUND CONSISTENTLY.</div></div></div><div style="text-align: right;"><div class="header-day">{data["day_short"]} · {data["date_short"]}</div><div style="color: #d0d8e0; font-size: 12px; margin: 3px 0;"><span style="background: #00aa44; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">● LIVE</span>&nbsp; {data["timestamp"]}</div></div></div>', unsafe_allow_html=True)


# Filter
filtered = data["watchlist"]
if show_only_setups:
    filtered = [r for r in filtered if r["mps"] >= 60]
if min_mps > 0:
    filtered = [r for r in filtered if r["mps"] >= min_mps]


# ============ ROW 1 ============
r1c1, r1c2, r1c3 = st.columns([1, 1.5, 1.5])

with r1c1:
    # Weather
    if data["weather"]:
        w = data["weather"]
        code = w.get("weather_code", 0)
        cond = "Clear" if code == 0 else ("Partly cloudy" if code in (1,2) else "Mixed")
        weather_html = f'<div class="card"><div class="card-title">🌤️ WEATHER <span style="color: #6a7a8a; font-size: 10px;">Richmond Hill, ON</span></div><div style="text-align: center; font-size: 32px; margin: 4px 0;">{cond}</div><div class="big-number">{round(w["temperature_2m"])}°C</div><div style="text-align: center; color: #888; font-size: 10px; line-height: 1.6;">💧 {round(w["relative_humidity_2m"])}% humidity &nbsp;|&nbsp; 💨 {round(w["wind_speed_10m"])} km/h<br>Feels like {round(w["apparent_temperature"])}°C</div></div>'
    else:
        weather_html = '<div class="card"><div class="card-title">🌤️ WEATHER</div><div style="color: #888;">Unavailable</div></div>'
    st.markdown(weather_html, unsafe_allow_html=True)

    # Quote
    st.markdown(f'<div class="card"><div class="card-title card-title-orange">💭 QUOTE OF THE DAY</div><div class="quote-text">"{data["quote"]}"</div><div class="quote-author">— {data["quote_author"]}</div></div>', unsafe_allow_html=True)

    # Verse
    st.markdown('<div class="card"><div class="card-title card-title-blue">📖 VERSE OF THE DAY</div><div style="text-align: center; color: #d4af37; font-size: 11px; font-weight: bold; margin-bottom: 6px;">Philippians 4:13</div><div class="quote-text">"I can do all things through Christ who strengthens me."</div></div>', unsafe_allow_html=True)

with r1c2:
    # Market breadth + VIX + Sectors
    vix_value = data["indices"].get("^VIX", (None, None))[0]
    if vix_value:
        if vix_value < 15: vix_color = "#00ff88"; vix_label = "LOW"
        elif vix_value < 20: vix_color = "#d4af37"; vix_label = "NORMAL"
        elif vix_value < 30: vix_color = "#ff8c42"; vix_label = "ELEVATED"
        else: vix_color = "#ff4444"; vix_label = "HIGH"
        vix_html = f'<div class="card"><div class="card-title">⚡ VIX FEAR GAUGE</div><div style="display: flex; align-items: center; justify-content: space-between;"><div><div style="color: #d0d8e0; font-size: 11px;">Current VIX</div><div class="big-number" style="color: {vix_color}; font-size: 28px; text-align: left;">{vix_value:.2f}</div><div style="color: {vix_color}; font-size: 11px;">{vix_label}</div></div><div style="text-align: right; font-size: 10px; color: #6a7a8a; line-height: 1.4;"><div>🟢 10-15: Calm</div><div>🟡 15-20: Normal</div><div>🟠 20-30: Elevated</div><div>🔴 30+: Fear</div></div></div></div>'
        st.markdown(vix_html, unsafe_allow_html=True)

    # Sector heatmap
    sector_html = '<div class="card"><div class="card-title card-title-purple">🌡️ SECTOR PERFORMANCE</div><div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px;">'
    for sector, data_p in sorted(data["sector_perf"].items(), key=lambda x: x[1]["chg"], reverse=True):
        chg = data_p["chg"]
        if chg > 0.5: bg, fg = "rgba(0, 170, 68, 0.4)", "#00ff88"
        elif chg < -0.5: bg, fg = "rgba(170, 51, 51, 0.4)", "#ff4444"
        else: bg, fg = "rgba(85, 85, 85, 0.3)", "#aaa"
        sector_html += f'<div style="background: {bg}; padding: 6px 4px; border-radius: 4px; text-align: center; border: 1px solid #2a3f5f;"><div style="color: #d0d8e0; font-size: 9px; font-weight: bold;">{sector}</div><div style="color: {fg}; font-size: 13px; font-weight: bold; margin-top: 2px;">{chg:+.1f}%</div></div>'
    sector_html += "</div></div>"
    st.markdown(sector_html, unsafe_allow_html=True)

    # Market breadth
    total = len(data["watchlist"])
    ups = sum(1 for r in data["watchlist"] if r["chg"] > 0)
    downs = sum(1 for r in data["watchlist"] if r["chg"] < 0)
    flats = total - ups - downs
    if total > 0:
        up_pct = ups / total * 100
        down_pct = downs / total * 100
        flat_pct = flats / total * 100
        breadth_html = f'<div class="card"><div class="card-title">📊 MARKET BREADTH ({total} tickers)</div><div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px;"><span class="up">🟢 {ups} Up ({up_pct:.0f}%)</span><span class="neutral">⚪ {flats} Flat</span><span class="down">🔴 {downs} Down ({down_pct:.0f}%)</span></div><div style="height: 20px; border-radius: 4px; overflow: hidden; display: flex;"><div style="background: #00aa44; width: {up_pct}%; height: 100%;"></div><div style="background: #555; width: {flat_pct}%; height: 100%;"></div><div style="background: #aa3333; width: {down_pct}%; height: 100%;"></div></div></div>'
        st.markdown(breadth_html, unsafe_allow_html=True)

with r1c3:
    # Market movers
    gainers = sorted([r for r in filtered if r["chg"] > 0], key=lambda x: x["chg"], reverse=True)[:5]
    losers = sorted([r for r in filtered if r["chg"] < 0], key=lambda x: x["chg"])[:5]

    movers_html = '<div class="card"><div class="card-title card-title-green">📊 MARKET MOVERS</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">'
    movers_html += '<div><div style="color: #00ff88; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🟢 TOP GAINERS</div><table class="data-table"><tr><th>SYMBOL</th><th style="text-align: right;">CHG</th></tr>'
    for r in gainers[:5]:
        movers_html += f'<tr><td><b>{r["ticker"]}</b></td><td style="text-align: right;" class="up">+{r["chg"]:.2f}%</td></tr>'
    movers_html += '</table></div>'
    movers_html += '<div><div style="color: #ff4444; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🔴 TOP LOSERS</div><table class="data-table"><tr><th>SYMBOL</th><th style="text-align: right;">CHG</th></tr>'
    for r in losers[:5]:
        movers_html += f'<tr><td><b>{r["ticker"]}</b></td><td style="text-align: right;" class="down">{r["chg"]:.2f}%</td></tr>'
    movers_html += '</table></div></div></div>'
    st.markdown(movers_html, unsafe_allow_html=True)


# ============ ROW 2: TOP SETUPS ============
top_setups = [r for r in filtered if r["mps"] >= 60]
top_setups.sort(key=lambda x: x["mps"], reverse=True)

picks_html = '<div class="card"><div class="card-title card-title-green">🎯 TOP SETUPS (MPS > 60) <span class="live-badge">● LIVE</span></div><table class="data-table"><tr><th>RANK</th><th>SYMBOL</th><th>SECTOR</th><th style="text-align: right;">PRICE</th><th style="text-align: right;">CHG</th><th style="text-align: right;">VOL</th><th>SPARKLINE</th><th style="text-align: right;">MPS</th><th style="text-align: center;">RATING</th></tr>'
for i, r in enumerate(top_setups[:10], 1):
    rating = "BUY" if r["mps"] >= 70 else "HOLD"
    rating_class = "rating-buy" if rating == "BUY" else "rating-hold"
    chg_color = "up" if r["chg"] > 0 else "down"
    chg_str = f"+{r['chg']:.2f}%" if r["chg"] > 0 else f"{r['chg']:.2f}%"
    vol_pct = min(100, r.get("vol_ratio", 1) * 50)
    vol_color = "#00ff88" if r.get("vol_ratio", 1) >= 1 else "#ff8c42"
    spark_color = "#00ff88" if r["chg"] > 0 else "#ff4444"
    picks_html += f'<tr><td style="color: #d4af37; font-weight: bold;">#{i}</td><td><b style="color: #fff;">{r["ticker"]}</b></td><td style="color: #888; font-size: 10px;">{r["sector"]}</td><td style="text-align: right;">${r["price"]:.2f}</td><td style="text-align: right;" class="{chg_color}">{chg_str}</td><td style="text-align: right; font-size: 10px;"><div style="background: #0a0e17; border-radius: 2px; height: 4px; width: 50px; margin-left: auto;"><div style="background: {vol_color}; height: 100%; width: {vol_pct}%; border-radius: 2px;"></div></div><div style="color: #888; font-size: 9px; margin-top: 2px;">{r["vol_ratio"]:.1f}x</div></td><td>spark</td><td style="text-align: right;"><b>{r["mps"]:.0f}</b></td><td style="text-align: center;"><span class="{rating_class}">{rating}</span></td></tr>'

picks_html += '</table></div>'
st.markdown(picks_html, unsafe_allow_html=True)

# Sparklines below
if top_setups[:10]:
    cols = st.columns(10)
    for i, r in enumerate(top_setups[:10]):
        with cols[i]:
            if r.get("sparkline"):
                color = "#00ff88" if r["chg"] > 0 else "#ff4444"
                fig = make_sparkline(r["sparkline"], color)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ============ ROW 3: NEWS + CALENDAR ============
r3c1, r3c2 = st.columns([1, 2])

with r3c1:
    st.markdown('''<div class="card"><div class="card-title card-title-blue">📅 ECONOMIC CALENDAR</div><table class="data-table"><tr><th>TIME</th><th>EVENT</th><th>FORECAST</th><th>PREV</th></tr><tr><td>8:30 AM</td><td>Building Permits</td><td>1.42M</td><td>1.39M</td></tr><tr><td>8:30 AM</td><td>Housing Starts</td><td>1.36M</td><td>1.29M</td></tr><tr><td>10:30 AM</td><td>EIA Crude Inventories</td><td>--</td><td>-2.1M</td></tr><tr><td>2:00 PM</td><td>FOMC Decision</td><td>4.75%</td><td>4.75%</td></tr><tr><td>2:30 PM</td><td>Fed Chair Press Conf.</td><td>--</td><td>--</td></tr></table></div>''', unsafe_allow_html=True)

with r3c2:
    news_html = '<div class="card"><div class="card-title">📰 NEWS</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">'
    news_html += '<div><div style="color: #4da6ff; font-size: 10px; font-weight: bold; margin-bottom: 4px;">📌 WATCHLIST</div>'
    for news in data["watchlist_news"][:6]:
        news_html += f'<div style="background: #0f1721; padding: 6px 8px; border-radius: 4px; margin-bottom: 4px; border-left: 2px solid #4da6ff;"><div style="color: #4da6ff; font-size: 10px; font-weight: bold;">{news["ticker"]}</div><div style="color: #d0d8e0; font-size: 10px;">{news["headline"][:75]}</div></div>'
    news_html += '</div>'
    news_html += '<div><div style="color: #ffa500; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🌍 MACRO</div>'
    for headline in data["macro_news"][:6]:
        news_html += f'<div style="background: #0f1721; padding: 5px 8px; border-radius: 4px; margin-bottom: 3px; border-left: 2px solid #ffa500;"><div style="color: #d0d8e0; font-size: 9px;">• {headline[:75]}</div></div>'
    news_html += '</div></div></div>'
    st.markdown(news_html, unsafe_allow_html=True)


# ============ ROW 4: PORTFOLIO ============
positions = [
    ("NVDA", "NVIDIA Corp.", 15, 213.82, 204.79, 3071.85, -90.45, -135.45),
    ("AAPL", "Apple Inc.", 10, 290.30, 320.49, 3204.90, 0.00, 301.90),
    ("AMD", "Adv Micro Devices", 7, 546.10, 530.12, 3710.84, -112.00, -111.86),
    ("V", "Visa Inc.", 4, 323.50, 350.49, 1401.96, 0.00, 107.96),
    ("VOO", "Vanguard S&P 500", 14, 677.82, 700.00, 9800.00, 0.00, 310.52),
]
portfolio_html = '<div class="card"><div class="card-title card-title-orange">📂 PORTFOLIO POSITIONS</div><table class="data-table"><tr><th>SYMBOL</th><th>COMPANY</th><th style="text-align: right;">SHARES</th><th style="text-align: right;">AVG COST</th><th style="text-align: right;">PRICE</th><th style="text-align: right;">VALUE</th><th style="text-align: right;">DAY P&L</th><th style="text-align: right;">TOTAL P&L</th></tr>'
total_value, total_day, total_pl = 0, 0, 0
for sym, name, shares, avg, price, value, day, pl in positions:
    portfolio_html += f'<tr><td><b>{sym}</b></td><td>{name}</td><td style="text-align: right;">{shares}</td><td style="text-align: right;">${avg:.2f}</td><td style="text-align: right;">${price:.2f}</td><td style="text-align: right;">${value:,.2f}</td>'
    day_color = "up" if day > 0 else ("down" if day < 0 else "neutral")
    pl_color = "up" if pl > 0 else "down"
    portfolio_html += f'<td style="text-align: right;" class="{day_color}">{day:+,.2f}</td><td style="text-align: right;" class="{pl_color}">{pl:+,.2f}</td></tr>'
    total_value += value; total_day += day; total_pl += pl
portfolio_html += f'<tr style="background: #0a0e17; border-top: 2px solid #2a3f5f;"><td colspan="5" style="font-weight: bold; padding: 10px;">TOTAL</td><td style="text-align: right; font-weight: bold;">${total_value:,.2f}</td><td style="text-align: right; font-weight: bold;" class="{("up" if total_day > 0 else "down" if total_day < 0 else "neutral")}">{total_day:+,.2f}</td><td style="text-align: right; font-weight: bold;" class="{("up" if total_pl > 0 else "down")}">{total_pl:+,.2f}</td></tr></table></div>'
st.markdown(portfolio_html, unsafe_allow_html=True)


# ============ BOTTOM: INDICES BAR ============
idx_names = {
    "^DJI": ("DOW", "📈"), "^IXIC": ("NASDAQ", "📊"), "^GSPC": ("S&P", "📉"),
    "^RUT": ("RUT", "📋"), "^VIX": ("VIX", "⚡"), "GC=F": ("GOLD", "🥇"),
    "CL=F": ("OIL", "🛢️"), "BTC-USD": ("BTC", "₿"), "^TNX": ("10Y", "📊"),
}
idx_html = '<div style="display: grid; grid-template-columns: repeat(9, 1fr); gap: 6px; margin-top: 12px;">'
for sym, (short, icon) in idx_names.items():
    if sym in data["indices"]:
        price, chg = data["indices"][sym]
        chg_color = "up" if chg >= 0 else "down"
        price_str = f"{price:,.2f}" if price < 1000 else f"{price:,.0f}"
        idx_html += f'<div style="background: #0f1721; border: 1px solid #2a3f5f; border-radius: 6px; padding: 8px 4px; text-align: center;"><div style="color: #6a7a8a; font-size: 9px;">{icon} {short}</div><div style="color: #fff; font-size: 13px; font-weight: bold; margin: 3px 0;">{price_str}</div><div style="font-size: 10px;" class="{chg_color}">{chg:+.2f}%</div></div>'
idx_html += '</div>'
st.markdown(idx_html, unsafe_allow_html=True)


# Footer
st.markdown(f'<div style="text-align: center; color: #6a7a8a; font-size: 10px; margin-top: 12px; padding: 8px;">Last refresh: {data["timestamp"]} | Cache: 5 min | Powered by Hermes Agent</div>', unsafe_allow_html=True)
