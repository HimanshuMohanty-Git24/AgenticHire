# src/graph.py
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from .agents import (
    sourcing_agent,
    screening_agent,
    diversity_agent,
    hiring_manager_agent
)

# Define the state for the graph (simplified)
class AgentState(TypedDict):
    candidates: List[dict]
    parsed_profiles: str
    all_relevance_scores: list
    diversity_analysis: dict
    final_selection: dict

# Create the graph instance
workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("sourcing", sourcing_agent)
workflow.add_node("screening", screening_agent)
workflow.add_node("diversity", diversity_agent)
workflow.add_node("hiring_manager", hiring_manager_agent)

# Define the edges in a simple, linear flow
workflow.set_entry_point("sourcing")
workflow.add_edge("sourcing", "screening")
workflow.add_edge("screening", "diversity")
workflow.add_edge("diversity", "hiring_manager")
workflow.add_edge("hiring_manager", END)

# Compile the graph into a runnable application
app_graph = workflow.compile()