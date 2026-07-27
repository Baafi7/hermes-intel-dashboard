"""Market Intel Dashboard - Cloud-Compatible Version
Uses only yfinance + RSS (no local scripts required)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
import sys
import json
import os
from pathlib import Path

# Convert UTC to Eastern Time
try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except ImportError:
    ET = timezone.utc

# ============ TRADE JOURNAL DATA ============
TRADES_FILE = Path.home() / ".hermes" / "trades.json"

def load_trades():
    """Load trades from JSON file."""
    if TRADES_FILE.exists():
        try:
            return json.loads(TRADES_FILE.read_text())
        except Exception:
            return []
    return []


def save_trades(trades):
    """Save trades to JSON file."""
    TRADES_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRADES_FILE.write_text(json.dumps(trades, indent=2))
    ET = timezone.utc

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

    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; table-layout: fixed; }
    .data-table th {
        background: #0a0e17; color: #6a7a8a; font-size: 9px;
        text-transform: uppercase; letter-spacing: 1px;
        padding: 5px 4px; text-align: left; border-bottom: 1px solid #2a3f5f;
        font-weight: bold; word-wrap: break-word;
    }
    .data-table td {
        padding: 5px 4px; border-bottom: 1px solid #1a2332;
        color: #d0d8e0; word-wrap: break-word; vertical-align: middle;
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

st.set_page_config(page_title="Hermes Intel", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")


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

        # Per-ticker data with full error handling
        # Use batch download for speed (single API call for all tickers)
        try:
            tickers_str = " ".join(watchlist)
            data = yf.download(tickers_str, period="1mo", group_by="ticker", auto_adjust=True, progress=False, threads=True)
        except Exception:
            data = None

        results = []
        if data is not None and not data.empty:
            for t in watchlist:
                try:
                    # Extract this ticker's data
                    if len(watchlist) > 1 and t in data.columns.get_level_values(0):
                        closes = data[t]["Close"].dropna()
                        volumes = data[t]["Volume"].dropna()
                    else:
                        closes = data["Close"].dropna()
                        volumes = data["Volume"].dropna()

                    if closes is None or len(closes) < 2:
                        continue
                    price = float(closes.iloc[-1])
                    prev = float(closes.iloc[-2])
                    chg = (price / prev - 1) * 100

                    # SMA - safe
                    ma20 = float(closes.rolling(min(20, len(closes))).mean().iloc[-1]) if len(closes) >= 5 else price
                    ma50 = float(closes.rolling(min(50, len(closes))).mean().iloc[-1]) if len(closes) >= 10 else None
                    ma200 = float(closes.rolling(min(200, len(closes))).mean().iloc[-1]) if len(closes) >= 50 else None

                    # RSI - safe
                    try:
                        delta = closes.diff()
                        gain = delta.clip(lower=0)
                        loss = -delta.clip(upper=0)
                        avg_gain = gain.ewm(alpha=1/14, min_periods=min(14, len(gain)), adjust=False).mean()
                        avg_loss = loss.ewm(alpha=1/14, min_periods=min(14, len(loss)), adjust=False).mean()
                        rs = avg_gain / avg_loss.replace(0, 1e-10)
                        rsi = float((100 - (100 / (1 + rs))).iloc[-1])
                        rsi = max(0, min(100, rsi))
                    except Exception:
                        rsi = 50

                    # MACD
                    try:
                        ema12 = closes.ewm(span=12, adjust=False).mean()
                        ema26 = closes.ewm(span=26, adjust=False).mean()
                        macd = ema12 - ema26
                        sig = macd.ewm(span=9, adjust=False).mean()
                        hist = float((macd - sig).iloc[-1])
                        hist_yest = float((macd - sig).iloc[-2]) if len(macd) >= 2 else hist
                    except Exception:
                        hist = 0
                        hist_yest = 0

                    # Volume
                    try:
                        vol_ratio = float(volumes.iloc[-1] / volumes.tail(min(20, len(volumes))).mean()) if len(volumes) >= 5 else 1
                    except Exception:
                        vol_ratio = 1

                    # MPS
                    mps_base = 50
                    if 40 <= rsi <= 65:
                        mps_base += 8
                    elif rsi < 30 or rsi > 75:
                        mps_base += 5
                    if ma50 is not None and ma200 is not None and price > ma50 > ma200:
                        mps_base += 12
                    elif ma50 is not None and price > ma50:
                        mps_base += 6
                    if hist > 0 and hist > hist_yest:
                        mps_base += 6
                    if vol_ratio > 1.2:
                        mps_base += 4

                    sparkline = closes.tail(min(20, len(closes))).tolist()

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
                        "above_200": ma200 is not None and price > ma200,
                    })
                except Exception:
                    continue

        # Sector performance - only count tickers with valid chg data
        sector_perf = {}
        for r in results:
            s = r["sector"]
            if s not in sector_perf:
                sector_perf[s] = {"total": 0.0, "count": 0}
            if r.get("chg") is not None and not (r["chg"] != r["chg"]):  # filter NaN
                sector_perf[s]["total"] += r["chg"]
                sector_perf[s]["count"] += 1
        sector_perf = {}
        for k, v in sector_perf.items():
            if v["count"] > 0:
                sector_perf[k] = {"chg": v["total"] / v["count"], "count": v["count"]}

        # Major indices - filter NaN values
        indices = {}
        for sym in ["^DJI", "^IXIC", "^GSPC", "^RUT", "^VIX", "GC=F", "CL=F", "BTC-USD", "^TNX"]:
            try:
                tk = yf.Ticker(sym)
                df = tk.history(period="5d", auto_adjust=True)
                if df is not None and not df.empty and len(df) >= 2:
                    closes = df['Close'].dropna()
                    if len(closes) >= 2:
                        price = float(closes.iloc[-1])
                        prev = float(closes.iloc[-2])
                        if price == price and prev == prev and prev != 0:  # filter NaN, div by zero
                            indices[sym] = (price, (price/prev - 1) * 100)
            except Exception:
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
            "timestamp": datetime.now(ET).strftime("%I:%M %p ET"),
            "date_full": datetime.now(ET).strftime("%A, %B %d, %Y"),
            "day_short": datetime.now(ET).strftime("%A").upper(),
            "date_short": datetime.now(ET).strftime("%B %d, %Y"),
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
    valid_filtered = [r for r in filtered if r.get("chg") is not None and r["chg"] == r["chg"]]
    gainers = sorted([r for r in valid_filtered if r["chg"] > 0], key=lambda x: x["chg"], reverse=True)[:5]
    losers = sorted([r for r in valid_filtered if r["chg"] < 0], key=lambda x: x["chg"])[:5]

    movers_html = '<div class="card"><div class="card-title card-title-green">📊 MARKET MOVERS</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">'
    if gainers:
        movers_html += '<div><div style="color: #00ff88; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🟢 TOP GAINERS</div><table class="data-table"><tr><th>SYMBOL</th><th style="text-align: right;">CHG</th></tr>'
        for r in gainers[:5]:
            movers_html += f'<tr><td><b>{r["ticker"]}</b></td><td style="text-align: right;" class="up">+{r["chg"]:.2f}%</td></tr>'
        movers_html += '</table></div>'
    else:
        movers_html += '<div><div style="color: #888; font-size: 10px; margin-bottom: 4px;">No gainers</div></div>'

    if losers:
        movers_html += '<div><div style="color: #ff4444; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🔴 TOP LOSERS</div><table class="data-table"><tr><th>SYMBOL</th><th style="text-align: right;">CHG</th></tr>'
        for r in losers[:5]:
            movers_html += f'<tr><td><b>{r["ticker"]}</b></td><td style="text-align: right;" class="down">{r["chg"]:.2f}%</td></tr>'
        movers_html += '</table></div>'
    else:
        movers_html += '<div><div style="color: #888; font-size: 10px; margin-bottom: 4px;">No losers</div></div>'

    movers_html += '</div></div>'
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


# ============ ROW 3.5: WATCHLIST HEATMAP ============
st.markdown('<div class="card"><div class="card-title card-title-red">🔥 WATCHLIST HEATMAP</div><div style="font-size: 10px; color: #6a7a8a; margin-bottom: 10px;">All 41 watchlist tickers · color = % change · size = momentum intensity</div>', unsafe_allow_html=True)

# Build heatmap grid - 9 columns on desktop, responsive on mobile
heatmap_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(85px, 1fr)); gap: 4px;">'
valid_watchlist = [r for r in data["watchlist"] if r.get("chg") is not None and r["chg"] == r["chg"]]
# Sort by change (worst to best for visual)
valid_watchlist.sort(key=lambda x: x["chg"])

for r in valid_watchlist:
    chg = r["chg"]
    # Color intensity based on magnitude
    if chg >= 3:
        bg = "rgba(0, 255, 136, 0.35)"
        fg = "#00ff88"
        border = "#00ff88"
    elif chg >= 1.5:
        bg = "rgba(0, 200, 100, 0.25)"
        fg = "#00dd77"
        border = "#00cc66"
    elif chg >= 0.5:
        bg = "rgba(0, 170, 80, 0.15)"
        fg = "#88dd99"
        border = "#0a8044"
    elif chg > -0.5:
        bg = "rgba(85, 85, 85, 0.15)"
        fg = "#cccccc"
        border = "#444"
    elif chg > -1.5:
        bg = "rgba(170, 70, 70, 0.15)"
        fg = "#dd8888"
        border = "#803333"
    elif chg > -3:
        bg = "rgba(200, 60, 60, 0.25)"
        fg = "#ff6666"
        border = "#cc3333"
    else:
        bg = "rgba(255, 50, 50, 0.35)"
        fg = "#ff4444"
        border = "#ff4444"

    chg_str = f"{chg:+.1f}"
    # Size based on volatility (more volatile = larger)
    abs_chg = abs(chg)
    if abs_chg >= 3:
        padding = "10px 4px"
        ticker_size = "13px"
        chg_size = "14px"
    elif abs_chg >= 1.5:
        padding = "8px 4px"
        ticker_size = "12px"
        chg_size = "13px"
    else:
        padding = "6px 4px"
        ticker_size = "11px"
        chg_size = "11px"

    heatmap_html += f'<div style="background: {bg}; border: 1px solid {border}; border-radius: 4px; padding: {padding}; text-align: center;"><div style="color: #fff; font-weight: bold; font-size: {ticker_size};" title="{r["ticker"]} - {r["sector"]}">{r["ticker"]}</div><div style="color: {fg}; font-size: {chg_size}; font-weight: bold; margin-top: 2px;">{chg_str}%</div></div>'

heatmap_html += '</div></div>'
st.markdown(heatmap_html, unsafe_allow_html=True)


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
idx_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 6px; margin-top: 12px;">'
for sym, (short, icon) in idx_names.items():
    if sym in data["indices"]:
        price, chg = data["indices"][sym]
        chg_color = "up" if chg >= 0 else "down"
        price_str = f"{price:,.2f}" if price < 1000 else f"{price:,.0f}"
        idx_html += f'<div style="background: #0f1721; border: 1px solid #2a3f5f; border-radius: 6px; padding: 8px 4px; text-align: center; min-width: 0; overflow: hidden;"><div style="color: #6a7a8a; font-size: 9px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{icon} {short}</div><div style="color: #fff; font-size: 13px; font-weight: bold; margin: 3px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{price_str}</div><div style="font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" class="{chg_color}">{chg:+.2f}%</div></div>'
idx_html += '</div>'
st.markdown(idx_html, unsafe_allow_html=True)


# ============ TRADE JOURNAL ============
st.markdown('<div class="card"><div class="card-title card-title-green">📊 TRADE JOURNAL <span class="live-badge">● TRACKING</span></div>', unsafe_allow_html=True)

trades = load_trades()
tab_entry, tab_open, tab_history, tab_stats = st.tabs(["➕ NEW TRADE", "📂 OPEN POSITIONS", "📜 HISTORY", "📈 STATS"])

with tab_entry:
    st.markdown('<div style="font-size: 11px; color: #6a7a8a; margin-bottom: 12px;">Log a new trade. Mark as "Open" to track, or add exit price to close it.</div>', unsafe_allow_html=True)

    e1, e2, e3 = st.columns(3)
    with e1:
        new_ticker = st.text_input("Ticker", key="new_ticker", placeholder="e.g. NVDA").upper()
        new_direction = st.selectbox("Direction", ["LONG", "SHORT"], key="new_direction")
        new_strategy = st.selectbox("Strategy", [
            "LONG_PUT", "LONG_CALL", "LONG_STRADDLE", "PUT_SPREAD",
            "CALL_SPREAD", "IRON_CONDOR", "STOCK_LONG", "STOCK_SHORT",
            "SWING_TRADE", "OTHER"
        ], key="new_strategy")
    with e2:
        new_entry = st.number_input("Entry Price", min_value=0.0, step=0.01, key="new_entry", format="%.2f")
        new_shares = st.number_input("Contracts/Shares", min_value=1, step=1, key="new_shares", value=1)
        new_date = st.date_input("Entry Date", key="new_date", value=datetime.now(ET).date())
    with e3:
        new_exit = st.number_input("Exit Price (leave 0 if open)", min_value=0.0, step=0.01, key="new_exit", format="%.2f", value=0.0)
        new_target = st.number_input("Target Price", min_value=0.0, step=0.01, key="new_target", format="%.2f", value=0.0)
        new_stop = st.number_input("Stop Price", min_value=0.0, step=0.01, key="new_stop", format="%.2f", value=0.0)

    new_notes = st.text_input("Notes (regime, setup, catalyst)", key="new_notes", placeholder="e.g. RSI divergence + oil spike regime")

    e4, e5 = st.columns([1, 4])
    with e4:
        if st.button("💾 SAVE TRADE", use_container_width=True):
            if not new_ticker or new_entry <= 0:
                st.error("Ticker and entry price required")
            else:
                new_trade = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "ticker": new_ticker,
                    "direction": new_direction,
                    "strategy": new_strategy,
                    "entry": new_entry,
                    "exit": new_exit if new_exit > 0 else None,
                    "shares": new_shares,
                    "target": new_target if new_target > 0 else None,
                    "stop": new_stop if new_stop > 0 else None,
                    "open_date": str(new_date),
                    "close_date": str(datetime.now(ET).date()) if new_exit > 0 else None,
                    "notes": new_notes or "",
                }
                trades.append(new_trade)
                save_trades(trades)
                st.success(f"✅ Saved {new_ticker} {new_strategy}")
                st.rerun()

    with e5:
        if st.button("📋 LOAD SAMPLE TRADES (for testing)"):
            sample_trades = [
                {"id": "1001", "ticker": "NVDA", "direction": "LONG", "strategy": "SWING_TRADE", "entry": 178.50, "exit": 192.30, "shares": 15, "target": 200.0, "stop": 170.0, "open_date": "2026-06-15", "close_date": "2026-07-08", "notes": "AI capex theme"},
                {"id": "1002", "ticker": "XOM", "direction": "LONG", "strategy": "STOCK_LONG", "entry": 142.00, "exit": 156.89, "shares": 10, "target": 165.0, "stop": 138.0, "open_date": "2026-06-20", "close_date": "2026-07-22", "notes": "Iran oil beneficiary"},
                {"id": "1003", "ticker": "INTC", "direction": "LONG", "strategy": "LONG_PUT", "entry": 7.10, "exit": 0.50, "shares": 1, "target": 14.0, "stop": 3.50, "open_date": "2026-07-10", "close_date": "2026-07-15", "notes": "IV crush - theta decayed"},
                {"id": "1004", "ticker": "AMAT", "direction": "LONG", "strategy": "PUT_SPREAD", "entry": 4.20, "exit": 9.80, "shares": 1, "target": 12.0, "stop": 0.0, "open_date": "2026-07-08", "close_date": "2026-07-18", "notes": "Credit spread - direction wrong but premium saved it"},
                {"id": "1005", "ticker": "TSLA", "direction": "SHORT", "strategy": "LONG_PUT", "entry": 8.40, "exit": 22.10, "shares": 1, "target": 0.0, "stop": 0.0, "open_date": "2026-07-15", "close_date": "2026-07-23", "notes": "Earnings miss - put exploded"},
                {"id": "1006", "ticker": "COIN", "direction": "LONG", "strategy": "LONG_STRADDLE", "entry": 18.50, "exit": 4.20, "shares": 1, "target": 30.0, "stop": 5.0, "open_date": "2026-07-18", "close_date": "2026-07-22", "notes": "IV crushed - no big move"},
                {"id": "1007", "ticker": "META", "direction": "LONG", "strategy": "SWING_TRADE", "entry": 510.00, "exit": 495.00, "shares": 10, "target": 550.0, "stop": 495.0, "open_date": "2026-07-08", "close_date": "2026-07-15", "notes": "Stopped out - strategy diffusion"},
                {"id": "1008", "ticker": "AVGO", "direction": "LONG", "strategy": "LONG_PUT", "entry": 4.55, "exit": 0.08, "shares": 1, "target": 0.0, "stop": 0.0, "open_date": "2026-06-25", "close_date": "2026-07-10", "notes": "Expired worthless - $64 ITM cushion"},
                {"id": "1009", "ticker": "INTC", "direction": "LONG", "strategy": "STOCK_LONG", "entry": 95.00, "exit": None, "shares": 5, "target": 110.0, "stop": 88.0, "open_date": "2026-07-22", "close_date": None, "notes": "Bounce candidate - awaiting confirmation"},
                {"id": "1010", "ticker": "WDC", "direction": "LONG", "strategy": "PUT_SPREAD", "entry": 6.50, "exit": None, "shares": 1, "target": 15.0, "stop": 0.0, "open_date": "2026-07-23", "close_date": None, "notes": "BULL_BIAS signal - fat premium"},
            ]
            save_trades(sample_trades)
            st.success("✅ Loaded 10 sample trades")
            st.rerun()

with tab_open:
    open_trades = [t for t in trades if t.get("exit") is None]
    if not open_trades:
        st.markdown('<div style="text-align: center; color: #888; padding: 20px;">No open positions. Add a trade in the NEW TRADE tab.</div>', unsafe_allow_html=True)
    else:
        open_html = '<table class="data-table"><tr><th>TICKER</th><th>STRATEGY</th><th>ENTRY</th><th>SHARES</th><th>TARGET</th><th>STOP</th><th>OPENED</th><th>NOTES</th></tr>'
        for t in open_trades:
            open_html += f'<tr><td><b>{t["ticker"]}</b></td><td style="font-size: 9px;">{t["strategy"]}</td><td>${t["entry"]:.2f}</td><td>{t["shares"]}</td><td>${t.get("target", 0):.2f}</td><td>${t.get("stop", 0):.2f}</td><td style="font-size: 10px;">{t.get("open_date", "")}</td><td style="font-size: 10px; color: #888;">{t.get("notes", "")[:30]}</td></tr>'
        open_html += '</table>'
        st.markdown(open_html, unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 16px; padding: 12px; background: #0f1721; border-radius: 6px;"><div style="color: #d4af37; font-weight: bold; margin-bottom: 8px;">CLOSE A TRADE</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            close_ticker = st.selectbox("Position to close", [t["ticker"] + " (" + t["strategy"] + ")" for t in open_trades], key="close_ticker")
        with c2:
            close_price = st.number_input("Exit Price", min_value=0.0, step=0.01, key="close_price", format="%.2f")
        with c3:
            st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
            if st.button("CLOSE", use_container_width=True):
                for t in trades:
                    if t.get("exit") is None and (t["ticker"] + " (" + t["strategy"] + ")") == close_ticker:
                        t["exit"] = close_price
                        t["close_date"] = str(datetime.now(ET).date())
                        save_trades(trades)
                        st.success(f"✅ Closed {t['ticker']} at ${close_price}")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab_history:
    closed_trades = [t for t in trades if t.get("exit") is not None]
    if not closed_trades:
        st.markdown('<div style="text-align: center; color: #888; padding: 20px;">No closed trades yet.</div>', unsafe_allow_html=True)
    else:
        history_html = '<table class="data-table"><tr><th>DATE</th><th>TICKER</th><th>STRATEGY</th><th>ENTRY</th><th>EXIT</th><th>SHARES</th><th style="text-align: right;">P&L</th><th style="text-align: right;">%</th><th>NOTES</th></tr>'
        for t in closed_trades:
            entry = t["entry"]
            exit_p = t["exit"]
            shares = t["shares"]
            if t["strategy"] in ["STOCK_LONG", "STOCK_SHORT", "SWING_TRADE"]:
                pnl = (exit_p - entry) * shares if t["direction"] == "LONG" else (entry - exit_p) * shares
                pct = (exit_p / entry - 1) * 100 if t["direction"] == "LONG" else (entry / exit_p - 1) * 100
            else:
                pnl = (exit_p - entry) * shares * 100
                pct = (exit_p / entry - 1) * 100 if entry > 0 else 0

            pnl_color = "up" if pnl > 0 else "down" if pnl < 0 else "neutral"
            pnl_str = f"{pnl:+,.0f}" if abs(pnl) >= 100 else f"{pnl:+,.2f}"
            history_html += f'<tr><td style="font-size: 10px;">{t.get("close_date", "")[:10]}</td><td><b>{t["ticker"]}</b></td><td style="font-size: 9px;">{t["strategy"]}</td><td>${entry:.2f}</td><td>${exit_p:.2f}</td><td>{shares}</td><td style="text-align: right;" class="{pnl_color}">{pnl_str}</td><td style="text-align: right;" class="{pnl_color}">{pct:+.1f}%</td><td style="font-size: 9px; color: #888;">{t.get("notes", "")[:30]}</td></tr>'
        history_html += '</table>'
        st.markdown(history_html, unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 16px; padding: 12px; background: #0f1721; border-radius: 6px;"><div style="color: #ff8c42; font-weight: bold; margin-bottom: 8px;">DELETE A TRADE</div>', unsafe_allow_html=True)
        d1, d2 = st.columns([3, 1])
        with d1:
            del_choice = st.selectbox("Trade to delete", [f'{t["ticker"]} {t["strategy"]} - {t.get("close_date", t.get("open_date", ""))[:10]}' for t in closed_trades], key="del_choice")
        with d2:
            if st.button("🗑️ DELETE", use_container_width=True):
                for t in trades:
                    if f'{t["ticker"]} {t["strategy"]} - {t.get("close_date", t.get("open_date", ""))[:10]}' == del_choice:
                        trades.remove(t)
                        save_trades(trades)
                        st.success("✅ Deleted")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab_stats:
    closed_trades = [t for t in trades if t.get("exit") is not None]
    if not closed_trades:
        st.markdown('<div style="text-align: center; color: #888; padding: 20px;">Close some trades to see stats.</div>', unsafe_allow_html=True)
    else:
        wins = []
        losses = []
        total_pnl = 0
        for t in closed_trades:
            entry = t["entry"]
            exit_p = t["exit"]
            shares = t["shares"]
            if t["strategy"] in ["STOCK_LONG", "STOCK_SHORT", "SWING_TRADE"]:
                pnl = (exit_p - entry) * shares if t["direction"] == "LONG" else (entry - exit_p) * shares
            else:
                pnl = (exit_p - entry) * shares * 100

            total_pnl += pnl
            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(pnl)

        total = len(closed_trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total * 100) if total > 0 else 0
        avg_win = sum(wins) / win_count if win_count else 0
        avg_loss = sum(losses) / loss_count if loss_count else 0
        profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) < 0 else float('inf')
        best_trade = max(wins) if wins else 0
        worst_trade = min(losses) if losses else 0

        stats_html = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px;">'
        stats = [
            ("🎯 WIN RATE", f"{win_rate:.0f}%", "#00ff88" if win_rate >= 50 else "#ff4444"),
            ("TOTAL P&L", f"${total_pnl:+,.0f}", "#00ff88" if total_pnl > 0 else "#ff4444"),
            ("WINS", f"{win_count}", "#00ff88"),
            ("LOSSES", f"{loss_count}", "#ff4444"),
            ("AVG WIN", f"${avg_win:,.0f}", "#00ff88"),
            ("AVG LOSS", f"${avg_loss:,.0f}", "#ff4444"),
            ("BEST TRADE", f"${best_trade:,.0f}", "#00ff88"),
            ("WORST TRADE", f"${worst_trade:,.0f}", "#ff4444"),
            ("PROFIT FACTOR", f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞", "#00ff88" if profit_factor > 1 else "#ff4444"),
            ("TOTAL TRADES", f"{total}", "#4da6ff"),
        ]
        for label, value, color in stats:
            stats_html += f'<div style="background: #0a0e17; border: 1px solid #2a3f5f; border-radius: 6px; padding: 10px; text-align: center;"><div style="color: #6a7a8a; font-size: 9px; margin-bottom: 4px;">{label}</div><div style="color: {color}; font-size: 18px; font-weight: bold;">{value}</div></div>'
        stats_html += '</div>'
        st.markdown(stats_html, unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 16px;"><div style="color: #d4af37; font-weight: bold; margin-bottom: 8px;">📊 PERFORMANCE BY STRATEGY</div>', unsafe_allow_html=True)
        strategy_stats = {}
        for t in closed_trades:
            strat = t["strategy"]
            if strat not in strategy_stats:
                strategy_stats[strat] = {"wins": 0, "losses": 0, "pnl": 0, "count": 0}
            entry = t["entry"]
            exit_p = t["exit"]
            shares = t["shares"]
            if t["strategy"] in ["STOCK_LONG", "STOCK_SHORT", "SWING_TRADE"]:
                pnl = (exit_p - entry) * shares if t["direction"] == "LONG" else (entry - exit_p) * shares
            else:
                pnl = (exit_p - entry) * shares * 100

            strategy_stats[strat]["pnl"] += pnl
            strategy_stats[strat]["count"] += 1
            if pnl > 0:
                strategy_stats[strat]["wins"] += 1
            else:
                strategy_stats[strat]["losses"] += 1

        strat_html = '<table class="data-table"><tr><th>STRATEGY</th><th>TRADES</th><th>WINS</th><th>LOSSES</th><th>WIN RATE</th><th>TOTAL P&L</th></tr>'
        for strat, s in sorted(strategy_stats.items(), key=lambda x: x[1]["pnl"], reverse=True):
            wr = (s["wins"] / s["count"] * 100) if s["count"] > 0 else 0
            pnl_color = "up" if s["pnl"] > 0 else "down"
            strat_html += f'<tr><td><b>{strat}</b></td><td>{s["count"]}</td><td class="up">{s["wins"]}</td><td class="down">{s["losses"]}</td><td>{wr:.0f}%</td><td class="{pnl_color}">${s["pnl"]:+,.0f}</td></tr>'
        strat_html += '</table></div>'
        st.markdown(strat_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# Footer
st.markdown(f'<div style="text-align: center; color: #6a7a8a; font-size: 10px; margin-top: 12px; padding: 8px;">Last refresh: {data["timestamp"]} | Cache: 5 min | Powered by Hermes Agent</div>', unsafe_allow_html=True)
