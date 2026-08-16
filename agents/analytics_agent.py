from graph.state import AgentState

def compute_technical_signal(technical: dict) -> str:
    if technical.get("error"):
        return "Insufficient data"
    sma_20 = technical.get("sma_20")
    sma_50 = technical.get("sma_50")
    if sma_20 is None or sma_50 is None:
        return "Insufficient data"
    return "Bullish signal" if sma_20 > sma_50 else "Bearish signal"
    
async def run_analytics_agent(state: AgentState) -> dict:
    market = state.get("market", {})
    prices = market.get("history", [])

    if not prices:
        return {"technical": {"error": "no price history available"}}

    closes = [p["close"] for p in prices]

    sma_20 = sum(closes[-20:]) / min(len(closes), 20)
    sma_50 = sum(closes[-50:]) / min(len(closes), 50)

    trend = "bullish" if sma_20 > sma_50 else "bearish"

    return {
        "technical": {
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "trend": trend,
            "latest_close": closes[-1],
        }
    }