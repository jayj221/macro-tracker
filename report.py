import datetime
import os
import yfinance as yf
import requests

TODAY = datetime.date.today()

ASSETS = {
    "TLT":  ("US 20Y Treasury Bonds", "Bonds"),
    "GLD":  ("Gold ETF", "Commodities"),
    "USO":  ("Crude Oil ETF", "Commodities"),
    "UUP":  ("US Dollar Index", "Currency"),
    "DBC":  ("Commodities Basket", "Commodities"),
    "VNQ":  ("Real Estate (REIT)", "Real Estate"),
    "HYG":  ("High Yield Bonds", "Credit"),
    "EEM":  ("Emerging Markets", "Equities"),
    "IWM":  ("Russell 2000 (Small Cap)", "Equities"),
    "XLF":  ("Financials Sector", "Equities"),
}

FRED_SERIES = {
    "DGS10": "10Y Treasury Yield",
    "DGS2":  "2Y Treasury Yield",
    "T10Y2Y": "Yield Curve (10Y-2Y)",
    "FEDFUNDS": "Fed Funds Rate",
    "CPIAUCSL": "CPI (Inflation)",
    "UNRATE": "Unemployment Rate",
}


def fetch_asset(symbol: str) -> dict | None:
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="6mo")
        if hist.empty:
            return None
        if hasattr(hist.index, "tz") and hist.index.tz is not None:
            hist.index = hist.index.tz_convert(None)
        close = hist["Close"]
        c = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        chg = round((c - prev) / prev * 100, 2)
        chg_1m = round((c / float(close.iloc[-21]) - 1) * 100, 2) if len(close) >= 21 else None
        chg_3m = round((c / float(close.iloc[-63]) - 1) * 100, 2) if len(close) >= 63 else None
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1])
        return {
            "symbol": symbol,
            "price": round(c, 2),
            "chg_1d": chg,
            "chg_1m": chg_1m,
            "chg_3m": chg_3m,
            "above_sma50": c > sma50,
            "above_sma200": c > sma200,
            "trend": "Uptrend" if c > sma50 > sma200 else "Downtrend" if c < sma50 < sma200 else "Mixed",
        }
    except Exception as e:
        print(f"[MacroTracker] {symbol} error: {e}")
        return None


def fetch_fred(series_id: str, api_key: str) -> float | None:
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit=1"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        val = obs[0]["value"] if obs else None
        return round(float(val), 3) if val and val != "." else None
    except Exception:
        return None


def risk_regime(assets: dict) -> str:
    tlt = assets.get("TLT")
    hyg = assets.get("HYG")
    eem = assets.get("EEM")
    uup = assets.get("UUP")
    if not tlt or not hyg:
        return "Unknown"
    bond_up = tlt["above_sma50"]
    credit_up = hyg["above_sma50"]
    em_up = eem["above_sma50"] if eem else False
    dollar_up = uup["above_sma50"] if uup else False
    if credit_up and em_up and not dollar_up:
        return "🟢 Risk-On"
    if bond_up and dollar_up and not credit_up:
        return "🔴 Risk-Off"
    return "🟡 Neutral / Transitioning"


def build_report(assets: dict, fred_data: dict) -> str:
    regime = risk_regime(assets)
    yield_curve = fred_data.get("T10Y2Y")
    yc_signal = "🔴 Inverted (recession risk)" if yield_curve and yield_curve < 0 else \
                "🟡 Flat" if yield_curve and yield_curve < 0.5 else \
                "🟢 Normal" if yield_curve else "N/A"

    lines = [
        f"# 🌍 Macro Tracker — {TODAY}",
        "",
        "> Daily macroeconomic indicators dashboard | Data: yfinance + FRED",
        "",
        "---",
        "",
        "## 1. Macro Regime",
        "",
        "| Indicator | Value | Signal |",
        "|-----------|-------|--------|",
        f"| Risk Regime | {regime} | — |",
    ]

    for sid, label in FRED_SERIES.items():
        val = fred_data.get(sid)
        val_str = f"{val}%" if val else "N/A"
        if sid == "T10Y2Y":
            lines.append(f"| {label} | {val_str} | {yc_signal} |")
        else:
            lines.append(f"| {label} | {val_str} | — |")

    lines += [
        "",
        "---",
        "",
        "## 2. Asset Performance",
        "",
        "| Asset | Name | Price | 1D | 1M | 3M | SMA50 | SMA200 | Trend |",
        "|-------|------|-------|----|----|-----|-------|--------|-------|",
    ]

    by_category = {}
    for sym, (name, cat) in ASSETS.items():
        by_category.setdefault(cat, []).append((sym, name))

    for cat, items in sorted(by_category.items()):
        for sym, name in items:
            a = assets.get(sym)
            if not a:
                continue
            chg1m = f"{a['chg_1m']:+.1f}%" if a["chg_1m"] is not None else "N/A"
            chg3m = f"{a['chg_3m']:+.1f}%" if a["chg_3m"] is not None else "N/A"
            s50 = "✅" if a["above_sma50"] else "❌"
            s200 = "✅" if a["above_sma200"] else "❌"
            trend_emoji = "📈" if a["trend"] == "Uptrend" else "📉" if a["trend"] == "Downtrend" else "➡️"
            lines.append(
                f"| {sym} | {name} | ${a['price']} | {a['chg_1d']:+.2f}% "
                f"| {chg1m} | {chg3m} | {s50} | {s200} | {trend_emoji} {a['trend']} |"
            )

    lines += [
        "",
        "---",
        "",
        "## 3. Macro Narrative",
        "",
    ]

    tlt = assets.get("TLT")
    gld = assets.get("GLD")
    uso = assets.get("USO")
    uup = assets.get("UUP")

    if tlt:
        bond_str = "Bonds are in an uptrend — flight-to-safety bid present." if tlt["trend"] == "Uptrend" \
            else "Bonds in downtrend — rate pressure or risk-on rotation."
        lines.append(f"**Bonds (TLT):** {bond_str}")
        lines.append("")
    if gld:
        gold_str = "Gold is trending up — inflation hedge demand or USD weakness." if gld["trend"] == "Uptrend" \
            else "Gold under pressure — dollar strength or low inflation expectations."
        lines.append(f"**Gold (GLD):** {gold_str}")
        lines.append("")
    if uso:
        oil_str = "Crude oil trending up — supply constraints or demand recovery." if uso["trend"] == "Uptrend" \
            else "Oil in downtrend — demand concerns or supply glut."
        lines.append(f"**Oil (USO):** {oil_str}")
        lines.append("")
    if uup:
        usd_str = "Dollar strengthening — risk-off, rate differentials favour USD." if uup["trend"] == "Uptrend" \
            else "Dollar weakening — potential tailwind for commodities and EM."
        lines.append(f"**US Dollar (UUP):** {usd_str}")
        lines.append("")

    if yield_curve is not None:
        lines += [
            f"**Yield Curve ({yield_curve:+.3f}%):** {yc_signal} — "
            + ("Monitor closely; historically precedes slowdown within 12-18 months." if yield_curve < 0
               else "Flat curve warrants caution on duration." if yield_curve < 0.5
               else "Normal slope — no immediate recession signal."),
            "",
        ]

    lines += [
        "---",
        "",
        f"*Macro Tracker | {TODAY} | Data: yfinance · FRED (St. Louis Fed)*",
    ]
    return "\n".join(lines)


def main():
    print(f"[MacroTracker] Generating report for {TODAY}...")
    fred_api_key = os.getenv("FRED_API_KEY", "")

    assets = {}
    for sym in ASSETS:
        print(f"[MacroTracker] Fetching {sym}...")
        data = fetch_asset(sym)
        if data:
            assets[sym] = data

    fred_data = {}
    if fred_api_key:
        for sid in FRED_SERIES:
            print(f"[MacroTracker] FRED {sid}...")
            fred_data[sid] = fetch_fred(sid, fred_api_key)
    else:
        print("[MacroTracker] No FRED_API_KEY — skipping FRED data")

    report = build_report(assets, fred_data)
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{TODAY}.md"
    with open(path, "w") as f:
        f.write(report)
    print(f"[MacroTracker] Report saved → {path}")


if __name__ == "__main__":
    main()
