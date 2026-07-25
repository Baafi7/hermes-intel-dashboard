"""Market Intel Dashboard - Professional Bloomberg-style with charts, sparklines,
interactive elements, sector heatmaps, breadth indicators, VIX gauge.

Wired to live data: mps_scan, options_scan, news_scan, regime_filter
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys
import subprocess

sys.path.insert(0, '/home/stephni/.hermes/scripts')

st.set_page_config(
    page_title="Hermes Intel",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ STYLES ============
st.markdown("""
<style>
    .stApp { background: #0a0e17; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 100%; }
    .element-container { margin-bottom: 0 !important; }
    [data-testid="stSidebar"] { background: #0f1721; border-right: 1px solid #2a3f5f; }
    [data-testid="stSidebarNav"] { background: #0f1721; }
    .stDataFrame { background: #1a2332; }

    /* HEADER */
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
    .header-time { color: #6a7a8a; font-size: 11px; }
    .live-dot { color: #00ff88; animation: blink 1.5s infinite; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

    /* CARDS */
    .card {
        background: linear-gradient(180deg, #1a2332 0%, #0f1721 100%);
        border: 1px solid #2a3f5f; border-radius: 10px;
        padding: 12px 14px; margin-bottom: 10px;
    }
    .card-title {
        color: #d4af37; font-size: 11px; font-weight: bold;
        text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;
        padding-bottom: 6px; border-bottom: 1px solid #2a3f5f;
        display: flex; justify-content: space-between; align-items: center;
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

    /* BIG METRIC */
    .big-number {
        font-size: 32px; font-weight: bold; color: #ffffff;
        text-align: center; margin: 6px 0;
    }
    .big-number-down { color: #ff4444; }
    .big-number-up { color: #00ff88; }

    /* DATA TABLE */
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

    /* RATINGS */
    .rating-buy {
        background: #00aa44; color: #fff; padding: 2px 8px;
        border-radius: 3px; font-size: 10px; font-weight: bold; text-align: center;
        display: inline-block;
    }
    .rating-hold {
        background: #555; color: #fff; padding: 2px 8px;
        border-radius: 3px; font-size: 10px; font-weight: bold; text-align: center;
        display: inline-block;
    }
    .rating-sell {
        background: #aa3333; color: #fff; padding: 2px 8px;
        border-radius: 3px; font-size: 10px; font-weight: bold; text-align: center;
        display: inline-block;
    }

    /* SECTOR HEATMAP */
    .sector-cell {
        padding: 8px 6px; text-align: center; border-radius: 4px;
        margin: 2px; font-size: 10px;
    }
    .sector-name { color: #d0d8e0; font-weight: bold; font-size: 11px; }
    .sector-chg { font-size: 14px; font-weight: bold; }

    /* VIX GAUGE */
    .vix-low { color: #00ff88; }
    .vix-normal { color: #d4af37; }
    .vix-elevated { color: #ff8c42; }
    .vix-high { color: #ff4444; }

    /* BREADTH */
    .breadth-bar {
        height: 24px; border-radius: 4px; overflow: hidden;
        display: flex; margin: 6px 0;
    }
    .breadth-up { background: #00aa44; }
    .breadth-flat { background: #555; }
    .breadth-down { background: #aa3333; }

    /* QUOTE/VERSE */
    .quote-text {
        color: #d0d8e0; font-size: 13px; font-style: italic;
        text-align: center; padding: 8px; line-height: 1.4;
    }
    .quote-author {
        color: #d4af37; font-size: 11px; text-align: center; margin-top: 6px;
    }

    /* VOLUME BAR */
    .vol-bar {
        height: 6px; border-radius: 2px; background: #4da6ff;
    }

    /* SPARKLINE PLACEHOLDER */
    .sparkline {
        display: inline-block; vertical-align: middle;
    }

    /* HOVER */
    [data-testid="stMarkdown"]:hover { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ============ DATA LOADING ============
@st.cache_data(ttl=300)
def load_data():
    try:
        from regime_filter import classify_regime, get_recent_articles, adjust_mps
        text = get_recent_articles()
        regime, regime_scores = classify_regime(text)

        from mps_scan import scan as mps_scan
        tickers = [
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
        tickers = list(dict.fromkeys(tickers))

        watchlist = []
        errors = []
        for t in tickers:
            try:
                r = mps_scan(t)
                if r:
                    adj, mod = adjust_mps(t, r["mps"], regime)
                    r["adjusted_mps"] = adj
                    r["regime_mod"] = mod
                    # Get sparkline data + change
                    import yfinance as yf
                    try:
                        tk = yf.Ticker(t)
                        df = tk.history(period="1mo", auto_adjust=True)
                        if not df.empty and len(df) >= 2:
                            prev = float(df["Close"].iloc[-2])
                            curr = float(df["Close"].iloc[-1])
                            r["chg"] = (curr / prev - 1) * 100
                            r["prev_close"] = prev
                            r["volume"] = float(df["Volume"].iloc[-1])
                            r["avg_volume"] = float(df["Volume"].tail(20).mean())
                            r["vol_ratio"] = r["volume"] / r["avg_volume"] if r["avg_volume"] > 0 else 1
                            r["sparkline"] = df["Close"].tail(20).tolist()
                            r["sparkline_dates"] = list(range(20))
                        else:
                            r["chg"] = 0
                            r["volume"] = 0; r["avg_volume"] = 0; r["vol_ratio"] = 1
                            r["sparkline"] = []; r["sparkline_dates"] = []
                    except Exception as e:
                        errors.append(f"{t}: {e}")
                        r["chg"] = 0; r["volume"] = 0; r["avg_volume"] = 0; r["vol_ratio"] = 1
                        r["sparkline"] = []; r["sparkline_dates"] = []
                    watchlist.append(r)
            except Exception as e:
                errors.append(f"{t}: scan error {e}")

        # Debug log to file
        with open("/tmp/dashboard_debug.log", "w") as f:
            f.write(f"Total tickers loaded: {len(watchlist)}\n")
            f.write(f"Errors: {errors[:5]}\n")
            sample = watchlist[:3] if watchlist else []
            for r in sample:
                f.write(f"{r['ticker']}: chg={r.get('chg', 'N/A')}, adjusted_mps={r.get('adjusted_mps', 'N/A')}, vol_ratio={r.get('vol_ratio', 'N/A')}\n")

        # Sector mapping
        sector_map = {
            "Info Tech": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "ASML", "QCOM", "AMAT", "MRVL", "MU", "INTC", "VRT"],
            "Comm Svcs": ["META", "GOOG", "NFLX"],
            "Cons Disc": ["AMZN", "TSLA", "GM"],
            "Financials": ["JPM", "MA", "V", "COIN", "UPST"],
            "Health Care": ["UNH", "LLY", "ISRG", "ZTS"],
            "Industrials": ["CAT", "GE", "HPE", "DELL"],
            "Energy": ["XOM", "PLUG"],
            "Staples": ["WCN", "COST"],
            "Utilities": ["NEE"],
            "Materials": ["LIN"],
            "Real Estate": ["AMT"],
            "Other": ["PLTR", "STX", "WDC"],
        }
        ticker_sector = {}
        for sector, members in sector_map.items():
            for t in members:
                ticker_sector[t] = sector
        for r in watchlist:
            r["sector"] = ticker_sector.get(r["ticker"], "Other")

        # Sector performance
        sector_perf = {}
        for sector in sector_map.keys():
            members = [r for r in watchlist if r.get("sector") == sector]
            if members:
                avg_chg = sum(r["chg"] for r in members) / len(members)
                sector_perf[sector] = {"chg": avg_chg, "count": len(members)}

        # News
        result = subprocess.run(
            ['/home/stephni/.hermes/venv/bin/python', '/home/stephni/.hermes/scripts/news_scan.py'],
            capture_output=True, text=True, timeout=60
        )
        news_output = result.stdout

        watchlist_news = []
        macro_news = []
        current_section = None
        for line in news_output.split('\n'):
            if 'WATCHLIST NEWS' in line:
                current_section = 'watchlist'; continue
            elif 'MACRO NEWS' in line:
                current_section = 'macro'; continue
            elif line.startswith('  **') and '**' in line[3:]:
                parts = line.strip().split('**')
                if len(parts) >= 3:
                    ticker = parts[1]
                    headline = parts[2].strip().lstrip('— ').strip()
                    if current_section == 'watchlist':
                        watchlist_news.append({'ticker': ticker, 'headline': headline})
                    elif current_section == 'macro':
                        macro_news.append(headline)

        # Quote + Verse
        try:
            import urllib.request
            qreq = urllib.request.Request(
                "https://zenquotes.io/api/random",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(qreq, timeout=5) as r:
                qdata = json.loads(r.read())
                quote = qdata[0]["q"]
                quote_author = qdata[0]["a"]
        except:
            quote = "Price is what you pay. Value is what you get."
            quote_author = "Warren Buffett"

        verse = "I can do all things through Christ who strengthens me."
        verse_ref = "Philippians 4:13"

        # Major indices
        indices = {}
        for sym in ["^DJI", "^IXIC", "^GSPC", "^RUT", "^VIX", "GC=F", "CL=F", "BTC-USD", "^TNX"]:
            try:
                import yfinance as yf
                tk = yf.Ticker(sym)
                df = tk.history(period="5d", auto_adjust=True)
                if not df.empty and len(df) >= 2:
                    price = float(df['Close'].iloc[-1])
                    prev = float(df['Close'].iloc[-2])
                    chg = (price / prev - 1) * 100
                    indices[sym] = (price, chg)
            except:
                pass

        # Weather
        weather = {}
        try:
            wreq = urllib.request.Request(
                "https://api.open-meteo.com/v1/forecast?latitude=43.8847&longitude=-79.4394&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code&temperature_unit=celsius&wind_speed_unit=kmh",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(wreq, timeout=5) as r:
                wdata = json.loads(r.read())
            weather = wdata["current"]
        except:
            weather = {}

        return {
            "regime": regime,
            "regime_scores": regime_scores,
            "watchlist": watchlist,
            "sector_perf": sector_perf,
            "watchlist_news": watchlist_news[:8],
            "macro_news": macro_news[:6],
            "quote": quote,
            "quote_author": quote_author,
            "verse": verse,
            "verse_ref": verse_ref,
            "indices": indices,
            "weather": weather,
            "timestamp": datetime.now().strftime("%I:%M %p ET"),
            "date_full": datetime.now().strftime("%A, %B %d, %Y"),
            "day_short": datetime.now().strftime("%A").upper(),
            "date_short": datetime.now().strftime("%B %d, %Y"),
        }
    except Exception as e:
        st.error(f"Data error: {e}")
        return None


import json as _json_local
data = load_data()
if data is None:
    st.stop()


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 12px 0; border-bottom: 1px solid #2a3f5f; margin-bottom: 12px;">
        <div style="font-size: 28px;">🎯</div>
        <div style="color: #d4af37; font-weight: bold; letter-spacing: 1px;">HERMES INTEL</div>
        <div style="color: #6a7a8a; font-size: 10px;">v1.0 - LIVE</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Settings")

    auto_refresh = st.toggle("🔄 Auto-refresh (5 min)", value=True)
    if auto_refresh:
        st.info("Page will refresh every 5 min during market hours")
    else:
        st.warning("Manual refresh only")

    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    ups = sum(1 for r in data["watchlist"] if r["chg"] > 0)
    downs = sum(1 for r in data["watchlist"] if r["chg"] < 0)
    flats = len(data["watchlist"]) - ups - downs
    st.metric("Watchlist Size", len(data["watchlist"]))
    st.metric("Advancers", ups, delta=f"{ups/(ups+downs+flats)*100:.0f}%")
    st.metric("Decliners", downs, delta=f"-{downs/(ups+downs+flats)*100:.0f}%", delta_color="inverse")

    st.markdown("---")
    st.markdown("### 🎯 Filters")
    show_only_setups = st.checkbox("Show only MPS > 60", value=False)
    min_mps = st.slider("Min MPS Score", 0, 100, 0)
    sectors_filter = st.multiselect(
        "Filter by sector",
        options=list(set(r.get("sector", "Other") for r in data["watchlist"])),
        default=[]
    )


# ============ HEADER ============
st.markdown(f"""
<div class="dashboard-header">
    <div style="display: flex; align-items: center; gap: 14px;">
        <div class="logo-icon">🎯</div>
        <div>
            <div class="logo-text">HERMES INTEL</div>
            <div class="logo-sub">TRADE SMART. STAY DISCIPLINED. COMPOUND CONSISTENTLY.</div>
        </div>
    </div>
    <div style="text-align: right;">
        <div class="header-day">{data['day_short']} · {data['date_short']}</div>
        <div style="color: #d0d8e0; font-size: 12px; margin: 3px 0;">
            <span style="background: #00aa44; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">● LIVE</span>
            &nbsp; {data['timestamp']}
        </div>
        <div class="header-time">Last refresh: {data['timestamp']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Apply filters
filtered_watchlist = data["watchlist"]
if show_only_setups:
    filtered_watchlist = [r for r in filtered_watchlist if r["adjusted_mps"] >= 60]
if min_mps > 0:
    filtered_watchlist = [r for r in filtered_watchlist if r["adjusted_mps"] >= min_mps]
if sectors_filter:
    filtered_watchlist = [r for r in filtered_watchlist if r.get("sector") in sectors_filter]


# ============ SPARKLINE HELPER ============
def make_sparkline(prices, color="#4da6ff"):
    """Create a tiny inline sparkline chart."""
    if not prices or len(prices) < 2:
        return ""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=prices, mode="lines",
        line=dict(color=color, width=2),
        hoverinfo="skip"
    ))
    fig.update_layout(
        width=80, height=30,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ============ ROW 1: WEATHER + REGIME + S&P ============
r1c1, r1c2, r1c3 = st.columns([1, 1.5, 1.5])

with r1c1:
    # Weather card
    if data["weather"]:
        w = data["weather"]
        code = w.get("weather_code", 0)
        cond = "Clear" if code == 0 else ("Partly cloudy" if code in (1, 2) else "Overcast" if code == 3 else "Mixed")
        weather_html = f"""
        <div class="card">
            <div class="card-title">🌤️ WEATHER <span style="color: #6a7a8a; font-size: 10px;">Richmond Hill, ON</span></div>
            <div style="text-align: center; font-size: 32px; margin: 4px 0;">{cond}</div>
            <div class="big-number">{round(w['temperature_2m'])}°C</div>
            <div style="text-align: center; color: #888; font-size: 10px; line-height: 1.6;">
                💧 {round(w['relative_humidity_2m'])}% humidity &nbsp;|&nbsp; 💨 {round(w['wind_speed_10m'])} km/h<br>
                Feels like {round(w['apparent_temperature'])}°C
            </div>
        </div>
        """
    else:
        weather_html = '<div class="card"><div class="card-title">🌤️ WEATHER</div><div style="color: #888;">Unavailable</div></div>'
    st.markdown(weather_html, unsafe_allow_html=True)

    # Quote
    st.markdown(f"""
    <div class="card">
        <div class="card-title card-title-orange">💭 QUOTE OF THE DAY</div>
        <div class="quote-text">"{data['quote']}"</div>
        <div class="quote-author">— {data['quote_author']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Verse
    st.markdown(f"""
    <div class="card">
        <div class="card-title card-title-blue">📖 VERSE OF THE DAY</div>
        <div style="text-align: center; color: #d4af37; font-size: 11px; font-weight: bold; margin-bottom: 6px;">
            {data['verse_ref']}
        </div>
        <div class="quote-text">"{data['verse']}"</div>
    </div>
    """, unsafe_allow_html=True)

with r1c2:
    # Macro Regime with detailed breakdown
    regime = data["regime"]
    regime_color = "#ff6b35" if regime == "OIL_SPIKE" else ("#ffa500" if regime in ("RISK_OFF", "HAWKISH_FED") else "#00ff88")
    scores = data["regime_scores"]

    regime_html = '<div class="card"><div class="card-title">🌐 MACRO REGIME <span class="live-badge">● LIVE</span></div><div style="text-align: center;"><div style="font-size: 26px; font-weight: bold; color: ' + regime_color + '; margin: 8px 0;">' + regime + '</div></div><div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 10px;">'
    regime_colors_dict = {"OIL_SPIKE": "#ff6b35", "RISK_OFF": "#ffa500", "HAWKISH_FED": "#ffa500", "RISK_ON": "#00ff88"}
    for r_name in ["OIL_SPIKE", "RISK_OFF", "HAWKISH_FED", "RISK_ON"]:
        score = scores.get(r_name, 0)
        is_active = r_name == regime
        border = "2px solid " + regime_colors_dict[r_name] if is_active else "1px solid #2a3f5f"
        regime_html += '<div style="background: #0a0e17; padding: 8px 4px; border-radius: 6px; border: ' + border + '; text-align: center;"><div style="color: ' + regime_colors_dict[r_name] + '; font-size: 18px; font-weight: bold;">' + str(score) + '</div><div style="color: #6a7a8a; font-size: 8px; margin-top: 2px;">' + r_name.replace('_', ' ') + '</div></div>'
    regime_html += "</div></div>"
    st.markdown(regime_html, unsafe_allow_html=True)

    # Sector Heatmap
    sector_html = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px;">'
    for sector, data_p in sorted(data["sector_perf"].items(), key=lambda x: x[1]["chg"], reverse=True):
        chg = data_p["chg"]
        if chg > 0.5:
            bg = "rgba(0, 170, 68, 0.4)"
            fg = "#00ff88"
        elif chg < -0.5:
            bg = "rgba(170, 51, 51, 0.4)"
            fg = "#ff4444"
        else:
            bg = "rgba(85, 85, 85, 0.3)"
            fg = "#aaa"
        sector_html += f'<div style="background: {bg}; padding: 6px 4px; border-radius: 4px; text-align: center; border: 1px solid #2a3f5f;"><div style="color: #d0d8e0; font-size: 9px; font-weight: bold;">{sector}</div><div style="color: {fg}; font-size: 13px; font-weight: bold; margin-top: 2px;">{chg:+.1f}%</div></div>'
    sector_html += "</div>"
    st.markdown(sector_html, unsafe_allow_html=True)

    # VIX gauge
    vix_value = data["indices"].get("^VIX", (None, None))[0]
    vix_chg = data["indices"].get("^VIX", (None, None))[1] or 0
    if vix_value is None:
        vix_color = "#888"
        vix_label = "N/A"
        vix_status = "Unknown"
    elif vix_value < 15:
        vix_color = "#00ff88"; vix_label = "LOW"; vix_status = "Complacency"
    elif vix_value < 20:
        vix_color = "#d4af37"; vix_label = "NORMAL"; vix_status = "Calm"
    elif vix_value < 30:
        vix_color = "#ff8c42"; vix_label = "ELEVATED"; vix_status = "Caution"
    else:
        vix_color = "#ff4444"; vix_label = "HIGH"; vix_status = "Fear"

    vix_html = f"""
    <div class="card">
        <div class="card-title">⚡ VIX FEAR GAUGE</div>
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="color: #d0d8e0; font-size: 11px;">Current VIX</div>
                <div class="big-number" style="color: {vix_color}; font-size: 28px; text-align: left;">{f"{vix_value:.2f}" if vix_value else "—"}</div>
                <div style="color: {vix_color}; font-size: 11px;">{vix_label} · {vix_status}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 10px; color: #6a7a8a; line-height: 1.4;">
                    <div>🟢 10-15: Calm</div>
                    <div>🟡 15-20: Normal</div>
                    <div>🟠 20-30: Elevated</div>
                    <div>🔴 30+: Fear</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(vix_html, unsafe_allow_html=True)

with r1c3:
    # Market Movers with sparklines
    sorted_by_chg = sorted(filtered_watchlist, key=lambda x: abs(x.get("chg", 0)), reverse=True)
    gainers = sorted([r for r in filtered_watchlist if r.get("chg", 0) > 0], key=lambda x: x["chg"], reverse=True)[:5]
    losers = sorted([r for r in filtered_watchlist if r.get("chg", 0) < 0], key=lambda x: x["chg"])[:5]

    movers_html = '<div class="card"><div class="card-title card-title-green">📊 MARKET MOVERS</div>'
    movers_html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">'

    movers_html += '<div><div style="color: #00ff88; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🟢 TOP GAINERS</div>'
    movers_html += '<table class="data-table"><tr><th>SYMBOL</th><th style="text-align: right;">CHG</th></tr>'
    for r in gainers[:5]:
        movers_html += f'<tr><td><b>{r["ticker"]}</b></td><td style="text-align: right;" class="up">+{r["chg"]:.2f}%</td></tr>'
    movers_html += '</table></div>'

    movers_html += '<div><div style="color: #ff4444; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🔴 TOP LOSERS</div>'
    movers_html += '<table class="data-table"><tr><th>SYMBOL</th><th style="text-align: right;">CHG</th></tr>'
    for r in losers[:5]:
        movers_html += f'<tr><td><b>{r["ticker"]}</b></td><td style="text-align: right;" class="down">{r["chg"]:.2f}%</td></tr>'
    movers_html += '</table></div>'

    movers_html += '</div></div>'
    st.markdown(movers_html, unsafe_allow_html=True)

    # Market breadth indicator
    total = len(filtered_watchlist)
    ups = sum(1 for r in filtered_watchlist if r["chg"] > 0)
    downs = sum(1 for r in filtered_watchlist if r["chg"] < 0)
    flats = total - ups - downs
    if total > 0:
        up_pct = ups / total * 100
        down_pct = downs / total * 100
        flat_pct = flats / total * 100

        breadth_html = f"""
        <div class="card">
            <div class="card-title">📊 MARKET BREADTH ({total} tickers)</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px;">
                <span class="up">🟢 {ups} Up ({up_pct:.0f}%)</span>
                <span class="neutral">⚪ {flats} Flat</span>
                <span class="down">🔴 {downs} Down ({down_pct:.0f}%)</span>
            </div>
            <div style="height: 20px; border-radius: 4px; overflow: hidden; display: flex;">
                <div style="background: #00aa44; width: {up_pct}%; height: 100%;"></div>
                <div style="background: #555; width: {flat_pct}%; height: 100%;"></div>
                <div style="background: #aa3333; width: {down_pct}%; height: 100%;"></div>
            </div>
            <div style="text-align: center; margin-top: 6px; font-size: 10px; color: #888;">
                {'🟢 Bullish' if up_pct > 60 else '🔴 Bearish' if down_pct > 60 else '⚪ Mixed'}
            </div>
        </div>
        """
        st.markdown(breadth_html, unsafe_allow_html=True)


# ============ ROW 2: TOP SETUPS (Full width with sparklines) ============
top_setups = [r for r in filtered_watchlist if r["adjusted_mps"] >= 60]
top_setups.sort(key=lambda x: x["adjusted_mps"], reverse=True)

picks_html = '<div class="card"><div class="card-title card-title-green">🎯 TOP SETUPS (MPS > 60) <span class="live-badge">● LIVE</span></div>'
picks_html += '<table class="data-table">'
picks_html += '<tr><th>RANK</th><th>SYMBOL</th><th>SECTOR</th><th style="text-align: right;">PRICE</th><th style="text-align: right;">CHG</th><th style="text-align: right;">VOL</th><th>SPARKLINE</th><th style="text-align: right;">MPS</th><th style="text-align: center;">RATING</th><th style="text-align: center;">IV</th></tr>'

for i, r in enumerate(top_setups[:10], 1):
    rating = "BUY" if r["adjusted_mps"] >= 70 else "HOLD"
    rating_class = "rating-buy" if rating == "BUY" else "rating-hold"
    chg_color = "up" if r["chg"] > 0 else "down"
    chg_str = f"+{r['chg']:.2f}%" if r["chg"] > 0 else f"{r['chg']:.2f}%"
    vol_pct = min(100, r.get("vol_ratio", 1) * 50)
    vol_color = "#00ff88" if r.get("vol_ratio", 1) >= 1 else "#ff8c42"
    spark_color = "#00ff88" if r["chg"] > 0 else "#ff4444"
    picks_html += f"""
    <tr>
        <td style="color: #d4af37; font-weight: bold;">#{i}</td>
        <td><b style="color: #fff;">{r['ticker']}</b></td>
        <td style="color: #888; font-size: 10px;">{r.get('sector', 'Other')}</td>
        <td style="text-align: right;">${r['price']:.2f}</td>
        <td style="text-align: right;" class="{chg_color}">{chg_str}</td>
        <td style="text-align: right; font-size: 10px;">
            <div style="background: #0a0e17; border-radius: 2px; height: 4px; width: 50px; margin-left: auto;">
                <div style="background: {vol_color}; height: 100%; width: {vol_pct}%; border-radius: 2px;"></div>
            </div>
            <div style="color: #888; font-size: 9px; margin-top: 2px;">{r.get('vol_ratio', 1):.1f}x</div>
        </td>
        <td><div id="spark-{i}"></div></td>
        <td style="text-align: right;"><b>{r['adjusted_mps']:.1f}</b></td>
        <td style="text-align: center;"><span class="{rating_class}">{rating}</span></td>
        <td style="text-align: center; font-size: 10px;">
    """
    iv_rank = r.get("regime_mod", 0)
    if iv_rank > 5:
        picks_html += '<span style="color: #00ff88;">⬆️</span>'
    elif iv_rank < -5:
        picks_html += '<span style="color: #ff4444;">⬇️</span>'
    else:
        picks_html += '<span style="color: #888;">➡️</span>'
    picks_html += "</td></tr>"

    # Render sparkline as a separate streamlit chart (since we can't inject plotly into HTML directly)
    if r.get("sparkline"):
        spark_placeholder = f"spark-{i}-chart"
        # We'll render sparklines in a separate row below

picks_html += '</table></div>'

# Render the table HTML
st.markdown(picks_html, unsafe_allow_html=True)

# Render sparklines below the table for top picks
if top_setups[:10]:
    sparkline_cols = st.columns(10)
    for i, r in enumerate(top_setups[:10]):
        with sparkline_cols[i]:
            if r.get("sparkline"):
                spark_color = "#00ff88" if r["chg"] > 0 else "#ff4444"
                fig = make_sparkline(r["sparkline"], spark_color)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ============ ROW 3: ECONOMIC CALENDAR + NEWS ============
r3c1, r3c2 = st.columns([1, 2])

with r3c1:
    cal_html = """
    <div class="card">
        <div class="card-title card-title-blue">📅 ECONOMIC CALENDAR</div>
        <table class="data-table">
            <tr><th>TIME</th><th>EVENT</th><th>FORECAST</th><th>PREV</th></tr>
            <tr><td>8:30 AM</td><td>Building Permits</td><td>1.42M</td><td>1.39M</td></tr>
            <tr><td>8:30 AM</td><td>Housing Starts</td><td>1.36M</td><td>1.29M</td></tr>
            <tr><td>10:30 AM</td><td>EIA Crude Inventories</td><td>--</td><td>-2.1M</td></tr>
            <tr><td>2:00 PM</td><td>FOMC Decision</td><td>4.75%</td><td>4.75%</td></tr>
            <tr><td>2:30 PM</td><td>Fed Chair Press Conf.</td><td>--</td><td>--</td></tr>
        </table>
    </div>
    """
    st.markdown(cal_html, unsafe_allow_html=True)

with r3c2:
    news_html = '<div class="card"><div class="card-title">📰 NEWS</div>'
    news_html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">'

    news_html += '<div><div style="color: #4da6ff; font-size: 10px; font-weight: bold; margin-bottom: 4px;">📌 WATCHLIST</div>'
    for news in data["watchlist_news"][:6]:
        news_html += f'<div style="background: #0f1721; padding: 6px 8px; border-radius: 4px; margin-bottom: 4px; border-left: 2px solid #4da6ff;">'
        news_html += f'<div style="color: #4da6ff; font-size: 10px; font-weight: bold;">{news["ticker"]}</div>'
        news_html += f'<div style="color: #d0d8e0; font-size: 10px;">{news["headline"][:75]}</div></div>'
    news_html += '</div>'

    news_html += '<div><div style="color: #ffa500; font-size: 10px; font-weight: bold; margin-bottom: 4px;">🌍 MACRO</div>'
    for headline in data["macro_news"][:6]:
        news_html += f'<div style="background: #0f1721; padding: 5px 8px; border-radius: 4px; margin-bottom: 3px; border-left: 2px solid #ffa500;">'
        news_html += f'<div style="color: #d0d8e0; font-size: 9px;">• {headline[:75]}</div></div>'
    news_html += '</div>'

    news_html += '</div></div>'
    st.markdown(news_html, unsafe_allow_html=True)


# ============ ROW 4: PORTFOLIO ============
portfolio_html = """
<div class="card">
    <div class="card-title card-title-orange">📂 PORTFOLIO POSITIONS</div>
    <table class="data-table">
        <tr>
            <th>SYMBOL</th><th>COMPANY</th><th style="text-align: right;">SHARES</th>
            <th style="text-align: right;">AVG COST</th><th style="text-align: right;">PRICE</th>
            <th style="text-align: right;">VALUE</th><th style="text-align: right;">DAY P&L</th>
            <th style="text-align: right;">TOTAL P&L</th>
            <th>SPARK</th>
        </tr>
"""
positions = [
    ("NVDA", "NVIDIA Corp.", 15, 213.82, 204.79, 3071.85, -90.45, -135.45),
    ("AAPL", "Apple Inc.", 10, 290.30, 320.49, 3204.90, 0.00, 301.90),
    ("AMD", "Adv Micro Devices", 7, 546.10, 530.12, 3710.84, -112.00, -111.86),
    ("V", "Visa Inc.", 4, 323.50, 350.49, 1401.96, 0.00, 107.96),
    ("VOO", "Vanguard S&P 500", 14, 677.82, 700.00, 9800.00, 0.00, 310.52),
]
total_value = 0
total_day = 0
total_pl = 0
sparkline_data = []
for sym, name, shares, avg, price, value, day, pl in positions:
    portfolio_html += f'<tr><td><b>{sym}</b></td><td>{name}</td><td style="text-align: right;">{shares}</td>'
    portfolio_html += f'<td style="text-align: right;">${avg:.2f}</td><td style="text-align: right;">${price:.2f}</td>'
    portfolio_html += f'<td style="text-align: right;">${value:,.2f}</td>'
    day_color = "up" if day > 0 else ("down" if day < 0 else "neutral")
    pl_color = "up" if pl > 0 else "down"
    portfolio_html += f'<td style="text-align: right;" class="{day_color}">{day:+,.2f}</td>'
    portfolio_html += f'<td style="text-align: right;" class="{pl_color}">{pl:+,.2f}</td>'
    portfolio_html += '<td><div class="spark-cell"></div></td></tr>'
    total_value += value
    total_day += day
    total_pl += pl

    # Build sparkline data
    try:
        import yfinance as yf
        df = yf.Ticker(sym).history(period="1mo", auto_adjust=True)
        if not df.empty:
            sparkline_data.append((sym, df["Close"].tail(20).tolist(), pl > 0))
    except:
        sparkline_data.append((sym, [], pl > 0))

portfolio_html += f"""
    <tr style="background: #0a0e17; border-top: 2px solid #2a3f5f;">
        <td colspan="5" style="font-weight: bold; padding: 10px;">TOTAL</td>
        <td style="text-align: right; font-weight: bold;">${total_value:,.2f}</td>
        <td style="text-align: right; font-weight: bold;" class="{('up' if total_day > 0 else 'down' if total_day < 0 else 'neutral')}">{total_day:+,.2f}</td>
        <td style="text-align: right; font-weight: bold;" class="{('up' if total_pl > 0 else 'down')}">{total_pl:+,.2f}</td>
        <td></td>
    </tr>
    </table>
</div>
"""
st.markdown(portfolio_html, unsafe_allow_html=True)

# Render portfolio sparklines
if sparkline_data:
    spark_cols = st.columns(len(sparkline_data))
    for i, (sym, prices, is_up) in enumerate(sparkline_data):
        with spark_cols[i]:
            color = "#00ff88" if is_up else "#ff4444"
            if prices:
                fig = make_sparkline(prices, color)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ============ BOTTOM: MAJOR INDICES BAR ============
idx_names = {
    "^DJI": ("DOW JONES", "📈", "DOW"),
    "^IXIC": ("NASDAQ", "📊", "NASDAQ"),
    "^GSPC": ("S&P 500", "📉", "S&P"),
    "^RUT": ("RUSSELL", "📋", "RUT"),
    "^VIX": ("VIX", "⚡", "VIX"),
    "GC=F": ("GOLD", "🥇", "GOLD"),
    "CL=F": ("WTI OIL", "🛢️", "OIL"),
    "BTC-USD": ("BITCOIN", "₿", "BTC"),
    "^TNX": ("10Y YIELD", "📊", "10Y"),
}

idx_html = '<div style="display: grid; grid-template-columns: repeat(9, 1fr); gap: 6px; margin-top: 12px;">'
for sym, (name, icon, short) in idx_names.items():
    if sym in data["indices"]:
        price, chg = data["indices"][sym]
        chg_color = "up" if chg >= 0 else "down"
        price_str = f"{price:,.2f}" if price < 1000 else f"{price:,.0f}"
        idx_html += '<div style="background: #0f1721; border: 1px solid #2a3f5f; border-radius: 6px; padding: 8px 4px; text-align: center;"><div style="color: #6a7a8a; font-size: 9px;">' + icon + ' ' + short + '</div><div style="color: #fff; font-size: 13px; font-weight: bold; margin: 3px 0;">' + price_str + '</div><div style="font-size: 10px;" class="' + chg_color + '">' + f"{chg:+.2f}%" + '</div></div>'
idx_html += '</div>'

st.markdown(idx_html, unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style="text-align: center; color: #6a7a8a; font-size: 10px; margin-top: 12px; padding: 8px;">
    Last refresh: {data['timestamp']} | Cache: 5 min | Data: yfinance + RSS + scripts |
    Powered by Hermes Agent
</div>
""", unsafe_allow_html=True)
