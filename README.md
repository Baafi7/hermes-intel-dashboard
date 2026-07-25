# Hermes Intel Dashboard

Live market intelligence dashboard built with Streamlit, wired to:
- yfinance (real-time prices)
- RSS feeds (Bloomberg + Investing.com)
- Custom MPS scoring system
- Macro regime detection
- IV signal analysis

## Features
- Sector heatmap with real-time performance
- Macro regime indicator (OIL_SPIKE, RISK_OFF, HAWKISH_FED, RISK_ON)
- Top setups with sparklines and volume bars
- Market breadth indicators
- VIX fear gauge
- Watchlist news feed
- Portfolio positions with sparklines
- Major indices bar (Dow, NASDAQ, S&P, Russell, VIX, Gold, Oil, BTC, 10Y)

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`
