from typing import TypedDict, Optional, Any


class AgentState(TypedDict):
    ticker: str
    market: dict[str, Any]       # from data_agent (price, volume, fundamentals)
    technical: dict[str, Any]    # from analytics_agent (indicators, signals)
    research: dict[str, Any]     # from research_agent (RAG-grounded news/filings summary)
    advisor: dict[str, Any]      # from advisor_agent (recommendation + reasoning)
    report: dict[str, Any]       # from report_agent (final formatted output)
    error: Optional[str]