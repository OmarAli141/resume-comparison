"""
LangGraph workflow — the complete recruiting agent.
This is the final piece. Everything now works.
"""
from langgraph.graph import StateGraph, END
from typing import Literal

from .state import AgentState
from .nodes import (
    understand_query,
    clarify_if_needed,
    handle_clarification_response,
)

def should_continue(state: AgentState) -> Literal["clarify", "end"]:
    """
    Decide next step based on query_complete.
    If complete, end the graph (main.py handles search manually).
    """
    if state.get("query_complete"):
        return "end"
    return "clarify"

# Build the graph
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("understand", understand_query)
workflow.add_node("clarify", clarify_if_needed)
workflow.add_node("handle_response", handle_clarification_response)

# Set entry point
workflow.set_entry_point("understand")

# Conditional routing
workflow.add_conditional_edges(
    "understand",
    should_continue,
    {
        "clarify": "clarify",
        "end": END
    }
)

# After clarify, we pause for user input in main.py
# Then main.py will update state and continue the graph to handle_response
workflow.add_edge("clarify", "handle_response")

# After handling response → go back to understand (to re-check missing fields)
workflow.add_edge("handle_response", "understand")

# Compile — this is your agent
app = workflow.compile()

__all__ = ["app"]