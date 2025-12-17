import re
from typing import Optional, Dict, List, Any

EDUCATION_KEYWORDS = {
    "doctoral": ["phd", "doctorate", "doctoral", "dphil", "ph.d"],
    "masters": ["master", "masters", "mba", "msc", "m.sc", "m.s", "ma", "m.a"],
    "bachelors": ["bachelor", "bachelors", "ba", "b.a", "bs", "b.s", "bsc", "b.sc", "undergraduate"],
    "associate": ["associate", "a.a.s", "aas"],
    "diploma": ["diploma", "certificate", "certification"],
    "highschool": ["high school", "secondary", "hs", "h.s", "ged"],
}

LEVEL_KEYWORDS = {
    "executive": ["executive", "vp", "vice president", "chief", "cfo", "ceo", "cto", "cio", "president", "director"],
    "senior": ["senior", "sr", "lead", "principal", "head", "staff", "distinguished"],
    "mid": ["mid", "mid-level", "midlevel", "intermediate", "experienced"],
    "junior": ["junior", "jr", "entry", "assistant", "level i", "level 1"],
    "intern": ["intern", "internship", "trainee", "co-op", "co op"],
}

LEVEL_DISPLAY = {
    "executive": "Manager / Executive",
    "senior": "Senior",
    "mid": "Mid-level",
    "junior": "Junior",
    "intern": "Intern/Student",
}


def _normalize_for_matching(text: Optional[str]) -> str:
    if not text:
        return ""
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _keyword_in_text(text_norm: str, keyword: str) -> bool:
    kw = _normalize_for_matching(keyword)
    if not kw:
        return False
    return re.search(r"\b" + re.escape(kw) + r"\b", text_norm) is not None


def _extract_skills_from_query(raw_query: str) -> List[str]:
    """Extract skills using heuristics for common patterns."""
    lower = raw_query.lower()
    skills: List[str] = []

    # "with Excel", "with Excel and SQL", etc.
    with_match = re.search(r"with\s+([^.]+?)(?:\s+skills?|\s+experience|\s+knowledge|\s+proficiency|$|\.|\))", lower)
    if with_match:
        part = with_match.group(1)
        candidates = re.split(r',|\sand\s+| or |\|', part)
        skills.extend([c.strip() for c in candidates if c.strip()])

    # "skills: Excel, SQL"
    skills_match = re.search(r"skills?\s*[:\-]?\s*([a-z0-9\s,&+/]+)", lower)
    if skills_match:
        part = skills_match.group(1)
        candidates = re.split(r',|\sand\s+| or |\&', part)
        skills.extend([c.strip() for c in candidates if c.strip()])

    # "proficient in Excel", "experience with Power BI", etc.
    for phrase in ["proficient in", "experience with", "knowledge of", "familiar with", "using"]:
        prof_match = re.search(rf"{phrase}\s+([^,.]+)", lower)
        if prof_match:
            part = prof_match.group(1)
            skills.extend([s.strip() for s in re.split(r',|\sand\s+', part) if s.strip()])

    # Clean, dedupe, and title-case
    cleaned = []
    seen = set()
    for s in skills:
        s = s.strip()
        if 1 < len(s) < 40 and s not in seen:
            seen.add(s)
            cleaned.append(s.title())
    return cleaned[:8]


def parse_query_requirements(query: str) -> Dict[str, Any]:
    if not query:
        return {
            "min_years": None,
            "max_years": None,
            "education_level": None,
            "seniority_level": None,
            "skills": []
        }

    raw_lower = query.lower()
    normalized = _normalize_for_matching(query)

    requirements: Dict[str, Any] = {
        "min_years": None,
        "max_years": None,
        "education_level": None,
        "seniority_level": None,
        "skills": []
    }

    # === Years ===
    range_match = re.search(r"(?:between\s+)?(\d+)\s*(?:and|to|-)\s*(\d+)\s*(?:years?|yrs?)", raw_lower)
    if range_match:
        a, b = int(range_match.group(1)), int(range_match.group(2))
        requirements["min_years"] = min(a, b)
        requirements["max_years"] = max(a, b)

    if requirements["min_years"] is None:
        min_match = re.search(r"(?:at least|minimum|min|over|more than)\s*(\d+)|(\d+)\s*\+", raw_lower)
        if min_match:
            val = min_match.group(1) or min_match.group(2)
            requirements["min_years"] = int(val)

    if requirements["max_years"] is None:
        # Handle "10-" pattern (max years)
        max_dash_match = re.search(r"(\d+)\s*-\s*(?!\d)", raw_lower)
        if max_dash_match:
            requirements["max_years"] = int(max_dash_match.group(1))
        else:
            max_match = re.search(r"(?:up to|less than|under|maximum|max)\s*(\d+)", raw_lower)
            if max_match:
                requirements["max_years"] = int(max_match.group(1))

    if requirements["min_years"] is None and requirements["max_years"] is None:
        simple_years = re.search(r"(\d{1,2})\s*(?:years?|yrs?)", raw_lower)
        if simple_years:
            requirements["min_years"] = int(simple_years.group(1))

    # === Education ===
    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(_keyword_in_text(normalized, kw) for kw in keywords):
            requirements["education_level"] = level
            break

    # === Seniority ===
    for level, keywords in LEVEL_KEYWORDS.items():
        if any(_keyword_in_text(normalized, kw) for kw in keywords):
            requirements["seniority_level"] = level
            break

    # === Skills ===
    extracted = _extract_skills_from_query(query)
    if extracted:
        requirements["skills"] = extracted

    return requirements


def _normalize_education_level(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    lower = text.lower()
    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return level
    return None


def _normalize_level(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    lower = text.lower()
    for level, keywords in LEVEL_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return level
    return None


def candidate_matches_requirements(candidate: dict, requirements: dict) -> bool:
    min_years = requirements.get("min_years")
    max_years = requirements.get("max_years")
    required_education = requirements.get("education_level")
    required_level = requirements.get("seniority_level")
    required_skills = requirements.get("skills", [])

    if min_years is not None and candidate.get("years_numeric", 0) < min_years:
        return False
    if max_years is not None and candidate.get("years_numeric", 0) > max_years:
        return False
    if required_education:
        cand_edu = _normalize_education_level(candidate.get("education") or candidate.get("education_level"))
        if cand_edu != required_education:
            return False
    if required_level:
        cand_level = _normalize_level(candidate.get("seniority") or candidate.get("title") or "")
        if cand_level != required_level:
            return False
    if required_skills:
        cand_skills_lower = [s.lower() for s in candidate.get("skills", [])]
        if not any(any(rs.lower() in cs for cs in cand_skills_lower) for rs in required_skills):
            return False

    return True


def describe_filters(requirements: dict) -> List[str]:
    desc = []
    if requirements.get("min_years") is not None:
        desc.append(f"Experience ≥ {int(requirements['min_years'])} years")
    if requirements.get("max_years") is not None:
        desc.append(f"Experience ≤ {int(requirements['max_years'])} years")
    if edu := requirements.get("education_level"):
        title = edu.title() + ("'s" if edu != "doctoral" else "")
        desc.append(f"Education: {title}")
    if level := requirements.get("seniority_level"):
        desc.append(f"Level: {LEVEL_DISPLAY.get(level, level.title())}")
    if skills := requirements.get("skills"):
        # Filter out bad patterns from skills
        exclude_keywords = {
            "bachelor", "bachelors", "master", "masters", "phd", "doctorate", "doctoral",
            "associate", "associates", "junior", "senior", "mid", "executive", "intern", 
            "lead", "principal", "assistant", "years", "year", "experience", "level", 
            "degree", "diploma", "yrs"
        }
        filtered_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            # Skip if it's an education/seniority keyword
            if skill_lower in exclude_keywords:
                continue
            # Skip year patterns
            if re.match(r'^\d+\+?\s*(years?|yrs?)?$', skill_lower):
                continue
            # Skip if it contains year patterns
            if re.search(r'\d+\+?\s*(years?|yrs?)', skill_lower):
                continue
            # Skip if it contains education keywords
            if any(edu in skill_lower for edu in ["bachelor", "master", "phd", "degree"]):
                continue
            # Skip if it's too long
            if len(skill) > 30:
                continue
            filtered_skills.append(skill)
        if filtered_skills:
            desc.append(f"Skills: {', '.join(filtered_skills[:5])}")
    return desc
