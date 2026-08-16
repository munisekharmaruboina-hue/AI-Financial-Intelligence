from langgraph.graph import StateGraph, END
from graph.state import AgentState

from agents.data_agent import run_data_agent
from agents.analytics_agent import run_analytics_agent
from agents.research_agent import run_research_agent
from agents.advisor_agent import run_advisor_agent
from agents.report_agent import run_report_agent


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("data_agent", run_data_agent)
    workflow.add_node("analytics_agent", run_analytics_agent)
    workflow.add_node("research_agent", run_research_agent)
    workflow.add_node("advisor_agent", run_advisor_agent)
    workflow.add_node("report_agent", run_report_agent)

    workflow.set_entry_point("data_agent")

    # data -> analytics + research can run independently, then fan-in at advisor
    workflow.add_edge("data_agent", "analytics_agent")
    workflow.add_edge("data_agent", "research_agent")
    workflow.add_edge("analytics_agent", "advisor_agent")
    workflow.add_edge("research_agent", "advisor_agent")
    workflow.add_edge("advisor_agent", "report_agent")
    workflow.add_edge("report_agent", END)

    return workflow.compile()


graph = build_graph()