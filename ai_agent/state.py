from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    user_query: str
    structured_query: Dict[str, Any]
    missing_fields: List[str]
    query_complete: bool
    final_response: str
