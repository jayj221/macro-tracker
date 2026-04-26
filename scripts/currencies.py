import yfinance as yf
import json
import datetime
import os

TODAY = str(datetime.date.today())
FX = {
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "JPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD", "CADUSD=X": "CAD/USD", "DX-Y.NYB": "DXY Index",
}

def tz(h):
    if hasattr(h.index, "tz") and h.index.tz:
        h.index = h.index.tz_convert(None)
    return h

def main():
    os.makedirs("data", exist_ok=True)
    fxd = {}
    for sym, name in FX.items():
        try:
            h = tz(yf.Ticker(sym).history(period="1mo"))
            if h.empty or len(h) < 2:
                continue
            c = float(h["Close"].iloc[-1])
            p = float(h["Close"].iloc[-2])
            m = float(h["Close"].iloc[0])
            fxd[sym] = {"name": name, "price": round(c, 4),
                        "chg_1d": round((c - p) / p * 100, 2),
                        "chg_1m": round((c - m) / m * 100, 2)}
        except Exception as e:
            print(f"[fx] {sym}: {e}")

    with open("data/currencies.json", "w") as f:
        json.dump({"date": TODAY, "fx": fxd}, f, indent=2)
    print(f"[currencies] Done — {len(fxd)} pairs")

if __name__ == "__main__":
    main()
