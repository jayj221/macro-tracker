import yfinance as yf
import json
import datetime
import os

TODAY = str(datetime.date.today())
BONDS = {
    "TLT": "20Y Treasury", "IEF": "10Y Treasury", "SHY": "2Y Treasury",
    "LQD": "Corp Bonds", "HYG": "High Yield", "EMB": "Emerging Mkt", "TIP": "TIPS",
}

def tz(h):
    if hasattr(h.index, "tz") and h.index.tz:
        h.index = h.index.tz_convert(None)
    return h

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    bd = {}
    for sym, name in BONDS.items():
        try:
            h = tz(yf.Ticker(sym).history(period="1mo"))
            if h.empty or len(h) < 2:
                continue
            c = float(h["Close"].iloc[-1])
            p = float(h["Close"].iloc[-2])
            m = float(h["Close"].iloc[0])
            bd[sym] = {"name": name, "price": round(c, 2),
                       "chg_1d": round((c - p) / p * 100, 2),
                       "chg_1m": round((c - m) / m * 100, 2)}
        except Exception as e:
            print(f"[bonds] {sym}: {e}")

    with open("data/bond_markets.json", "w") as f:
        json.dump({"date": TODAY, "bonds": bd}, f, indent=2)

    lines = [f"# Bond Markets — {TODAY}", "",
             "| ETF | Name | Price | 1D | 1M |", "|----|------|-------|----|----|"]
    for sym, d in sorted(bd.items(), key=lambda x: x[1]["chg_1d"], reverse=True):
        lines.append(f"| {sym} | {d['name']} | ${d['price']} | {d['chg_1d']:+.2f}% | {d['chg_1m']:+.2f}% |")

    with open(f"reports/bonds_{TODAY}.md", "w") as f:
        f.write("\n".join(lines))
    print(f"[bonds] Done — {len(bd)} bond ETFs")

if __name__ == "__main__":
    main()
