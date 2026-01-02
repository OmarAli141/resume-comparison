"""
It will contain the tools that the agent will use to answer the user's question.
NO LLM calls, NO state, NO prints. Just clean, testable logic.
"""
import re
from typing import List, Dict, Any

from shared.candidate_filters import (
    parse_query_requirements,
    candidate_matches_requirements,
    _normalize_education_level,
    _extract_skills_from_query,
    _normalize_level,
    describe_filters
)
from shared.core_search import RESUME_LOOKUP, extract_candidate_profile, search_by_job_description, search_by_text
from .prompts import SKIP_KEYWORDS, QUESTION_ORDER, SENIORITY_MAP

def is_skip(text: str) -> bool:
    """
    Check if the user want to skip the question

    Args:
        text (str): The user's response
    Returns:
        bool: True if the user want to skip the question, False otherwise
    """
    text = text.lower().strip()
    
    if not text:
        return True
    
    for keyword in SKIP_KEYWORDS:
        if keyword in text:
            return True
   
    return False

def parse_clarification_answer(answer: str, field: str) -> Any:
    """
    Parse user's answer during step-by-step clarification.
    
    Args:
        answer: Raw user reply
        field: Which field we're asking about

    Returns:
        Parsed value or "__SKIP__" or None
    """
    if is_skip(answer):
        return "__SKIP__"

    cleaned = answer.strip()

    if field == "job_title":
        return cleaned.title() if cleaned else None

    if field == "experience_seniority":
        # Let shared do the heavy work
        reqs = parse_query_requirements(cleaned)
        result = {}
        if reqs["min_years"] is not None:
            result["min_years"] = int(reqs["min_years"])
        if reqs["max_years"] is not None:
            result["max_years"] = int(reqs["max_years"])
        if reqs["seniority_level"]:
            # Map to your display format using SENIORITY_MAP
            # parse_query_requirements returns keys like "junior", "senior" which match SENIORITY_MAP keys
            level_key = reqs["seniority_level"].lower()
            mapped = SENIORITY_MAP.get(level_key)
            if mapped:
                result["seniority"] = mapped
            else:
                # Fallback: capitalize first letter
                result["seniority"] = reqs["seniority_level"].title()
        
        # Return result if it has any content, otherwise None
        if result:
            return result
        return None

    if field == "skills":
        # Simple comma or "and" split
        if not cleaned:
            return None
        skills = [s.strip().title() for s in re.split(r'[,\n]|\sand\s+', cleaned) if s.strip()]
        return skills if skills else None

    if field == "education":
        reqs = parse_query_requirements(cleaned)
        level = reqs.get("education_level")
        if not level:
            return None
        mapping = {
            "bachelors": "Bachelor's",
            "masters": "Master's",
            "doctoral": "PhD"
        }
        return mapping.get(level, level.title())

    return cleaned  # fallback


def get_missing_fields(structured: Dict[str, Any]) -> List[str]:
    """
    Return list of fields (from QUESTION_ORDER) that are still missing.
    
    Rules:
        - "__SKIP__" counts as complete
        - experience_seniority: complete if has min_years OR seniority
        - others: must have non-None/non-empty value
    """
    missing = []

    for field in QUESTION_ORDER:
        value = structured.get(field)

        if value == "__SKIP__":
            continue  # explicitly skipped → good

        if field == "job_title":
            if not value or not isinstance(value, str) or not value.strip():
                missing.append(field)

        elif field == "experience_seniority":
            exp = structured.get("experience_seniority")
            # If field doesn't exist or is not a dict, it's missing
            if exp is None or not isinstance(exp, dict):
                missing.append(field)
                continue
            # Check if we have either years or seniority
            min_years = exp.get("min_years")
            max_years = exp.get("max_years")
            seniority = exp.get("seniority")
            has_years = (min_years is not None) or (max_years is not None)
            has_seniority = seniority is not None and bool(seniority)
            if not (has_years or has_seniority):
                missing.append(field)

        elif field == "skills":
            if not value or not isinstance(value, list) or len(value) == 0:
                missing.append(field)

        elif field == "education":
            if not value:
                missing.append(field)

    return missing