import ta
import pandas as pd


class TechnicalService:

    def analyze(self, market):
        history = market.get("history", [])

        if not history or len(history) < 15:
            return {"error": "Not enough price history to compute indicators"}

        df = pd.DataFrame(history)
        df = df.rename(columns={"close": "Close"})
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna(subset=["Close"])

        result = {}

        # RSI needs at least 14 periods
        if len(df) >= 14:
            rsi_val = ta.momentum.RSIIndicator(df["Close"]).rsi().iloc[-1]
            result["rsi"] = round(rsi_val, 2) if pd.notna(rsi_val) else None
        else:
            result["rsi"] = None

        # EMA50 needs at least 50 periods
        if len(df) >= 50:
            ema50_val = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator().iloc[-1]
            result["ema50"] = round(ema50_val, 2) if pd.notna(ema50_val) else None
        else:
            result["ema50"] = None

        # EMA200 needs at least 200 periods — often unavailable with only 3mo of history
        if len(df) >= 200:
            ema200_val = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator().iloc[-1]
            result["ema200"] = round(ema200_val, 2) if pd.notna(ema200_val) else None
        else:
            result["ema200"] = None

        # MACD needs at least 26 periods (slow EMA span)
        if len(df) >= 26:
            macd_val = ta.trend.MACD(df["Close"]).macd().iloc[-1]
            result["macd"] = round(macd_val, 2) if pd.notna(macd_val) else None
        else:
            result["macd"] = None

        return result