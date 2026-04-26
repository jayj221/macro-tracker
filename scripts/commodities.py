import yfinance as yf
import json
import datetime
import os

TODAY = str(datetime.date.today())
COMMODITIES = {
    "GC=F": "Gold", "SI=F": "Silver", "CL=F": "Crude Oil",
    "NG=F": "Nat Gas", "ZC=F": "Corn", "ZW=F": "Wheat", "HG=F": "Copper",
}

def tz(h):
    if hasattr(h.index, "tz") and h.index.tz:
        h.index = h.index.tz_convert(None)
    return h

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    cd = {}
    for sym, name in COMMODITIES.items():
        try:
            h = tz(yf.Ticker(sym).history(period="3mo"))
            if h.empty or len(h) < 2:
                continue
            c = float(h["Close"].iloc[-1])
            p = float(h["Close"].iloc[-2])
            m = float(h["Close"].iloc[0])
            cd[sym] = {"name": name, "price": round(c, 2),
                       "chg_1d": round((c - p) / p * 100, 2),
                       "chg_3m": round((c - m) / m * 100, 2)}
        except Exception as e:
            print(f"[commodities] {sym}: {e}")

    with open("data/commodities.json", "w") as f:
        json.dump({"date": TODAY, "commodities": cd}, f, indent=2)

    lines = [f"# Commodities — {TODAY}", "",
             "| Commodity | Price | 1D | 3M |", "|-----------|-------|----|----|"]
    for sym, d in sorted(cd.items(), key=lambda x: x[1]["chg_1d"], reverse=True):
        lines.append(f"| {d['name']} | ${d['price']:,.2f} | {d['chg_1d']:+.2f}% | {d['chg_3m']:+.2f}% |")

    with open(f"reports/commodities_{TODAY}.md", "w") as f:
        f.write("\n".join(lines))
    print(f"[commodities] Done — {len(cd)} commodities")

if __name__ == "__main__":
    main()
