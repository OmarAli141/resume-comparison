"""
LangGraph nodes — pure orchestration.
No prints, no side effects, only state updates.
"""
import re
from typing import Dict, Any, List

from .state import AgentState
from .tools import (
    get_missing_fields,
    parse_clarification_answer,
    parse_query_requirements,
    _extract_skills_from_query
)
from .prompts import QUESTION_PROMPTS, SENIORITY_MAP, EDUCATION_MAP

def understand_query(state: AgentState) -> Dict[str, Any]:
    """
    First node: Parse the initial user query into structured data.
    Preserves existing structured_query if it exists (from clarification answers).
    """
    user_query = state["user_query"].strip()
    
    # Get existing structured_query to preserve clarification answers
    existing_structured = state.get("structured_query", {})
    
    # If structured_query already exists and has been updated (not empty dict),
    # just recalculate missing fields without re-parsing
    if existing_structured and any(
        v not in (None, {}, []) and v != "__SKIP__" 
        for v in existing_structured.values()
    ):
        # Just recalculate missing fields from existing structured_query
        missing = get_missing_fields(existing_structured)
        return {
            "structured_query": existing_structured,
            "missing_fields": missing,
            "query_complete": len(missing) == 0
        }
    
    # Otherwise, parse from user_query (first time only)
    # 1. Use shared's powerful parser
    reqs = parse_query_requirements(user_query)

    # 2. Extract clean job title (shared doesn't do this well)
    lower_query = user_query.lower()
    title_part = user_query
    
    # Handle "looking for X", "hiring for X", "need X", etc.
    for pattern in ["looking for", "hiring for", "need", "needing", "searching for", "want"]:
        if pattern in lower_query:
            parts = user_query.split(pattern, 1)
            if len(parts) > 1:
                title_part = parts[1].strip()
                break
    
    # Handle other separators - but stop at "with" if it's followed by skills/requirements
    if title_part == user_query:  # If no "looking for" pattern found
        for sep in [" with ", " - ", " | ", " in ", " at "]:
            if sep in lower_query:
                title_part = user_query.split(sep)[0].strip()
                break
    
    # Also handle "with" separately to stop at skills/requirements
    if " with " in lower_query:
        parts = title_part.split(" with ", 1)
        if len(parts) > 1:
            # Check if what comes after "with" looks like skills/requirements
            after_with = parts[1].lower()
            # If it contains skill-like words or numbers, stop before "with"
            if any(word in after_with for word in ["skill", "experience", "year", "degree", "bachelor", "master"]):
                title_part = parts[0].strip()

    # Remove leading seniority from title
    words = title_part.split()
    while words and words[0].lower() in ["junior", "senior", "jr", "sr", "lead", "intern", "an", "a", "the"]:
        words.pop(0)
    clean_title = " ".join(words).strip().title()
    if not clean_title:
        clean_title = user_query.title()

    # 3. Map seniority & education to your display format
    seniority_map = SENIORITY_MAP
    edu_map = EDUCATION_MAP

    # 4. Extract skills using the dedicated function
    extracted_skills = _extract_skills_from_query(user_query)
    
    # Filter out false positives (education, seniority keywords, experience patterns)
    filtered_skills = []
    exclude_keywords = {
        "bachelor", "bachelors", "master", "masters", "phd", "doctorate", "doctoral",
        "associate", "associates","junior", "senior", "mid", "executive", "intern", "lead", "principal", "assistant",
        "years", "year", "experience", "level", "degree", "diploma", "yrs"
    }
    for skill in extracted_skills:
        skill_lower = skill.lower()
        # Skip if it's an education/seniority keyword
        if skill_lower in exclude_keywords:
            continue
        # Skip year patterns (e.g., "5+ years", "10 years")
        if re.match(r'^\d+\+?\s*(years?|yrs?)?$', skill_lower):
            continue
        # Skip if it contains year patterns (e.g., "5+ Years Math Bachelor")
        if re.search(r'\d+\+?\s*(years?|yrs?)', skill_lower):
            continue
        # Skip if it contains education keywords
        if any(edu in skill_lower for edu in ["bachelor", "master", "phd", "degree"]):
            continue
        # Skip if it's too long (likely contains extra info)
        if len(skill) > 30:
            continue
        filtered_skills.append(skill)
    
    structured = {
        "job_title": clean_title,
        "experience_seniority": {
            "min_years": reqs.get("min_years"),
            "max_years": reqs.get("max_years"),
            "seniority": seniority_map.get(reqs.get("seniority_level"), None)
        },
        "skills": filtered_skills,  # Use extracted skills from query
        "education": edu_map.get(reqs.get("education_level"))
    }

    # 5. Determine what's missing
    missing = get_missing_fields(structured)

    return {
        "structured_query": structured,
        "missing_fields": missing,
        "query_complete": len(missing) == 0
    }


def clarify_if_needed(state: AgentState) -> Dict[str, Any]:
    """
    Ask ONE clarifying question if needed.
    """
    missing = state["missing_fields"]

    if not missing:
        return {
            "final_response": "Got it! All requirements clear. Searching now...",
            "query_complete": True
        }

    next_field = missing[0]
    question = QUESTION_PROMPTS[next_field]

    return {
        "final_response": question,
        "query_complete": False
    }


def handle_clarification_response(state: AgentState) -> Dict[str, Any]:
    """
    User answered a clarification question → parse and update structured_query
    """
    messages: List[Dict[str, Any]] = state.get("messages", [])
    last_message = messages[-1]["content"] if messages else ""
    missing_fields = state.get("missing_fields", [])
    current_field = missing_fields[0] if missing_fields else None

    if not current_field:
        return {"query_complete": True}

    parsed = parse_clarification_answer(last_message, current_field)

    # Update structured_query
    structured = state["structured_query"].copy()
    if parsed == "__SKIP__":
        structured[current_field] = "__SKIP__"
    elif parsed is not None:
        if current_field == "experience_seniority" and isinstance(parsed, dict):
            current = structured.get(current_field, {})
            current.update(parsed)
            structured[current_field] = current
        else:
            structured[current_field] = parsed

    # Recalculate missing
    missing = get_missing_fields(structured)

    return {
        "structured_query": structured,
        "missing_fields": missing,
        "query_complete": len(missing) == 0
    }