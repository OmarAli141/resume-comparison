"""
Candidate search and filtering logic.
"""
import re
from typing import List, Dict, Any

from shared.core_search import (
    search_by_text,
    search_by_job_description,
    extract_candidate_profile,
    RESUME_LOOKUP,
)
from shared.candidate_filters import (
    parse_query_requirements,
    candidate_matches_requirements,
    describe_filters,
)


def build_search_query(structured: Dict[str, Any], original_query: str) -> str:
    """Build search query from structured requirements."""
    search_parts = []
    if structured.get("job_title") and structured.get("job_title") != "__SKIP__":
        search_parts.append(structured["job_title"])
    exp = structured.get("experience_seniority") or {}
    if not isinstance(exp, dict):
        exp = {}
    if exp.get("seniority"):
        search_parts.append(exp["seniority"])
    if exp.get("min_years"):
        search_parts.append(f"{exp['min_years']}+ years")
    skills_val = structured.get("skills")
    if skills_val and skills_val != "__SKIP__":
        search_parts.extend(skills_val[:3])
    if structured.get("education") and structured.get("education") != "__SKIP__":
        search_parts.append(structured["education"])
    
    return " ".join(search_parts) if search_parts else original_query


def search_candidates(search_query: str, top_k: int = 20) -> List[Dict[str, Any]]:
    """Search for candidates using the search query."""
    print("\nSearching database...", flush=True)
    results = search_by_job_description(search_query, top_k=top_k) or search_by_text(search_query, top_k=top_k)

    candidates = []
    seen = set()
    for i, resume_id in enumerate(results["ids"][0]):
        if len(candidates) >= top_k:
            break
        distance = results["distances"][0][i]
        similarity = round(100 * (1 - distance), 1)

        meta = results["metadatas"][0][i]
        rid = str(meta.get("resume_id") or resume_id.split("_")[0])
        if rid in seen:
            continue
        seen.add(rid)

        entry = RESUME_LOOKUP.get(rid)
        if not entry:
            continue
        resume, _ = entry
        profile = extract_candidate_profile(resume)
        if profile.get("years_numeric", 0) and profile["years_numeric"] > 50:
            continue  # skip implausible experience totals
        profile.update({"id": rid, "similarity": similarity})
        candidates.append(profile)
    
    return candidates


from typing import Tuple

def filter_by_job_title(candidates: List[Dict[str, Any]], job_title: str) -> Tuple[List[Dict[str, Any]], str]:
    """Filter candidates by job title/category. Returns (filtered_candidates, job_title_for_display)."""
    if not job_title or job_title == "__SKIP__":
        return candidates, None
    
    job_title_for_display = job_title
    job_title_lower = job_title.lower().strip()
    title_keywords = [w for w in job_title_lower.split() 
                    if w not in ["an", "a", "the", "for", "looking", "hiring", "need", "i", "am"] 
                    and len(w) > 2]
    
    if not title_keywords:
        return candidates, job_title_for_display
    
    # Get main keyword and create variations
    main_keyword = title_keywords[0]
    variations = [main_keyword]
    if main_keyword.endswith("ant"):
        variations.append(main_keyword[:-3] + "ing")  # accountant -> accounting
    elif main_keyword.endswith("ing"):
        variations.append(main_keyword[:-3] + "ant")  # accounting -> accountant
    if main_keyword.endswith("er"):
        variations.append(main_keyword + "s")  # manager -> managers
    variations.extend(title_keywords)
    
    filtered_by_title = []
    for c in candidates:
        candidate_title = (c.get("title") or "").lower()
        candidate_category = (c.get("category") or "").lower()
        
        # Check work history if available
        work_history_text = ""
        resume_data = c.get("resume", {})
        if resume_data:
            work_history = resume_data.get("work_history", [])
            if work_history:
                work_history_text = " ".join([
                    str(job.get("title", "")).lower() 
                    for job in work_history[:3]
                ])
        
        # Check if any variation appears in title, category, or work history
        matches = False
        for var in variations:
            if (var in candidate_title or 
                var in candidate_category or
                (work_history_text and var in work_history_text)):
                matches = True
                break
        
        if matches:
            filtered_by_title.append(c)
    
    if filtered_by_title:
        return filtered_by_title, job_title_for_display
    else:
        print(f"\nNo candidates found with job title matching '{job_title}'.")
        return [], job_title_for_display


def apply_requirements_filter(candidates: List[Dict[str, Any]], structured: Dict[str, Any], search_query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Apply requirements filtering and return filtered candidates and filter descriptions."""
    requirements = parse_query_requirements(search_query)
    
    # Use skills from structured_query if available
    skills_val = structured.get("skills")
    if skills_val and skills_val != "__SKIP__" and isinstance(skills_val, list) and len(skills_val) > 0:
        exclude_keywords = {
            "bachelor", "bachelors", "master", "masters", "phd", "doctorate", "doctoral",
            "associate", "associates", "junior", "senior", "mid", "executive", "intern", 
            "lead", "principal", "assistant", "years", "year", "experience", "level", 
            "degree", "diploma", "yrs"
        }
        filtered_skills = []
        for skill in skills_val:
            skill_lower = skill.lower()
            if skill_lower in exclude_keywords:
                continue
            if re.match(r'^\d+\+?\s*(years?|yrs?)?$', skill_lower):
                continue
            if re.search(r'\d+\+?\s*(years?|yrs?)', skill_lower):
                continue
            if any(edu in skill_lower for edu in ["bachelor", "master", "phd", "degree"]):
                continue
            if len(skill) > 30:
                continue
            filtered_skills.append(skill)
        if filtered_skills:
            requirements["skills"] = filtered_skills
    
    if not any(requirements.values()):
        return candidates, []
    
    filtered = [c for c in candidates if candidate_matches_requirements(c, requirements)]
    filters = describe_filters(requirements)
    
    return filtered, filters


def clean_job_title_for_display(job_title: str) -> str:
    """Clean job title for display (remove trailing skill/requirement info)."""
    if not job_title or job_title == "__SKIP__":
        return None
    
    clean_job_title = job_title
    if " with " in clean_job_title.lower():
        parts = clean_job_title.split(" with ", 1)
        if len(parts) > 1:
            after_with = parts[1].lower()
            if any(word in after_with for word in ["skill", "experience", "year", "degree", "bachelor", "master"]):
                clean_job_title = parts[0].strip()
    
    return clean_job_title

