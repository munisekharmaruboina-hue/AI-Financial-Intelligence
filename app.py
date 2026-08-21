from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graph.workflow import graph
from services.market_service import resolve_ticker, get_market_data

app = FastAPI(
    title="AI Financial Intelligence API",
    version="2.0"
)


class StockRequest(BaseModel):
    ticker: str
    exchange: str = "NSE"


@app.get("/")
def home():
    return {
        "message": "AI Financial Intelligence API Running",
        "version": "2.0"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(request: StockRequest):
    try:
        resolved_ticker = await resolve_ticker(request.ticker, request.exchange)

        try:
            test_data = await get_market_data(resolved_ticker)
            if not test_data.get("history"):
                raise HTTPException(
                    status_code=404,
                    detail=f"'{request.ticker}' does not appear to be a valid, publicly traded ticker. Try a more specific company name or exact ticker symbol."
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=404,
                detail=f"'{request.ticker}' does not appear to be a valid, publicly traded ticker. Try a more specific company name or exact ticker symbol."
            )

        initial_state = {
            "ticker": resolved_ticker,
            "market": {},
            "technical": {},
            "research": {},
            "advisor": {},
            "report": {},
            "error": None,
        }

        result = await graph.ainvoke(initial_state)

        if result.get("error"):
            raise HTTPException(status_code=502, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))