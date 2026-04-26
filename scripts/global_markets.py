import yfinance as yf
import json
import datetime
import os

TODAY = str(datetime.date.today())
INDICES = {
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ",
    "^FTSE": "FTSE 100", "^N225": "Nikkei 225",
    "^GDAXI": "DAX", "^HSI": "Hang Seng", "^AXJO": "ASX 200",
}

def tz(h):
    if hasattr(h.index, "tz") and h.index.tz:
        h.index = h.index.tz_convert(None)
    return h

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    gmd = {}
    for sym, name in INDICES.items():
        try:
            h = tz(yf.Ticker(sym).history(period="5d"))
            if h.empty or len(h) < 2:
                continue
            c = float(h["Close"].iloc[-1])
            p = float(h["Close"].iloc[-2])
            m = float(h["Close"].iloc[0])
            gmd[sym] = {"name": name, "price": round(c, 2),
                        "chg_1d": round((c - p) / p * 100, 2),
                        "chg_5d": round((c - m) / m * 100, 2)}
        except Exception as e:
            print(f"[global] {sym}: {e}")

    with open("data/global_markets.json", "w") as f:
        json.dump({"date": TODAY, "indices": gmd}, f, indent=2)

    lines = [f"# Global Markets — {TODAY}", "",
             "| Index | Price | 1D | 5D |", "|-------|-------|----|----|"]
    for sym, d in gmd.items():
        lines.append(f"| {d['name']} | {d['price']:,.2f} | {d['chg_1d']:+.2f}% | {d['chg_5d']:+.2f}% |")

    with open(f"reports/global_{TODAY}.md", "w") as f:
        f.write("\n".join(lines))
    print(f"[global] Done — {len(gmd)} indices")

if __name__ == "__main__":
    main()
