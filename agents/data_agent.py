from services.market_service import get_market_data
from graph.state import AgentState


async def run_data_agent(state: AgentState) -> dict:
    ticker = state["ticker"]
    try:
        market_data = await get_market_data(ticker)
        return {"market": market_data}
    except Exception as e:
        return {"error": f"data_agent failed: {str(e)}"}