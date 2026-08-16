from services.llm_service import call_llm
from prompts.report_prompt import REPORT_PROMPT
from graph.state import AgentState


async def run_report_agent(state: AgentState) -> dict:
    if state.get("error"):
        return {"report": {"final": f"Analysis failed: {state['error']}"}}

    try:
        prompt = REPORT_PROMPT.format(
            ticker=state["ticker"],
            market=state.get("market", {}),
            technical=state.get("technical", {}),
            research=state.get("research", {}),
            advisor=state.get("advisor", {}),
        )
        final_report = await call_llm(prompt)
    except Exception as e:
        final_report = f"Report generation failed: {str(e)}"

    return {
        "report": {
            "final": final_report
        }
    }