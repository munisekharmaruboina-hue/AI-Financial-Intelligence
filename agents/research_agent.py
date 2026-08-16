from rag.vector_store import build_ephemeral_store
from rag.retriever import retrieve_context
from rag.splitter import split_articles
from services.news_service import fetch_latest_news
from services.llm_service import call_llm
from prompts.research_prompt import RESEARCH_PROMPT
from graph.state import AgentState


async def run_research_agent(state: AgentState) -> dict:
    ticker = state["ticker"]

    try:
        articles = await fetch_latest_news(ticker)
        print(f"[DEBUG] Fetched {len(articles)} articles")
    except Exception as e:
        print(f"[DEBUG] News fetch failed: {e}")
        articles = []

    if not articles:
        return {"research": {"summary": "No recent news found.", "sources_used": 0}}

    context_chunks = []
    try:
        chunks = split_articles(articles)
        print(f"[DEBUG] Split into {len(chunks)} chunks")
        store = build_ephemeral_store(chunks)
        print(f"[DEBUG] Vector store built: {store is not None}")
        context_chunks = await retrieve_context(store, query=f"{ticker} outlook risks earnings", k=5)
        print(f"[DEBUG] RAG retrieved {len(context_chunks)} chunks")
    except Exception as e:
        print(f"[DEBUG] RAG pipeline failed: {e}")
        context_chunks = []

    combined_context = "\n\n".join(context_chunks) if context_chunks else "\n\n".join(
        a["summary"] for a in articles[:5] if a.get("summary")
    )

    prompt = RESEARCH_PROMPT.format(ticker=ticker, context=combined_context)
    print(f"[DEBUG] Prompt sent to LLM (first 200 chars): {prompt[:200]}")

    summary = await call_llm(prompt)

    return {
        "research": {
            "summary": summary,
            "sources_used": len(context_chunks) or len(articles),
        }
    }
    if not articles:
        return {"research": {"summary": "No recent news found.", "sources_used": 0}}