import yfinance as yf
import json
import datetime
import os

TODAY = str(datetime.date.today())

REGIONAL_YIELDS = {
    "^TNX": ("US 10Y", "US"),
    "^IRX": ("US 3M", "US"),
    "^FVX": ("US 5Y", "US"),
    "^TYX": ("US 30Y", "US"),
}


def tz(h):
    if hasattr(h.index, "tz") and h.index.tz:
        h.index = h.index.tz_convert(None)
    return h


def main():
    os.makedirs("data", exist_ok=True)
    rates = {}
    for sym, (name, region) in REGIONAL_YIELDS.items():
        try:
            h = tz(yf.Ticker(sym).history(period="5d"))
            if h.empty:
                continue
            c = float(h["Close"].iloc[-1])
            p = float(h["Close"].iloc[-2]) if len(h) >= 2 else c
            rates[sym] = {
                "name": name,
                "region": region,
                "yield": round(c, 3),
                "chg_1d_bps": round((c - p) * 100, 1),
            }
        except Exception as e:
            print(f"[rates] {sym}: {e}")

    with open("data/regional_rates.json", "w") as f:
        json.dump({"date": TODAY, "rates": rates}, f, indent=2)
    print(f"[rates] Done — {len(rates)} regions")


if __name__ == "__main__":
    main()
