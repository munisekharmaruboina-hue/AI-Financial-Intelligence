from services.llm_service import call_llm
from prompts.advisor_prompt import ADVISOR_PROMPT
from agents.analytics_agent import compute_technical_signal
from graph.state import AgentState


async def run_advisor_agent(state: AgentState) -> dict:
    technical = state.get("technical", {})
    signal = compute_technical_signal(technical)

    prompt = ADVISOR_PROMPT.format(
        ticker=state["ticker"],
        signal=signal,
        technical=technical,
        research=state.get("research", {}).get("summary", ""),
    )

    recommendation = await call_llm(prompt)

    return {
        "advisor": {
            "recommendation": recommendation
        }
    }