from __future__ import annotations # this is used to avoid type errors and make the code more readable

import re
from typing import Dict, List

# Weights aligned with previous ATS narrative
WEIGHTS = {
    "skills": 0.40,
    "experience": 0.25,
    "education": 0.15,
    "similarity": 0.20,
}

EDUCATION_TIERS = [
    ("doctoral", 100, ["phd", "doctorate", "doctoral", "dphil"]),
    ("masters", 90, ["masters", "master", "msc", "m.sc", "m.s", "ma", "m.a", "mba"]),
    ("bachelors", 80, ["bachelor", "ba", "b.a", "bs", "b.s", "bsc", "b.sc"]),
    ("associate", 65, ["associate", "aas", "a.a", "a.s"]),
    ("diploma", 55, ["diploma", "certificate", "certification", "vocational"]),
    ("highschool", 40, ["high school", "secondary", "hs", "h.s", "ged"]),
]

LEVEL_KEYWORDS = {
    "Executive": ["executive", "vp", "vice president", "chief", "c-suite", "cto", "cfo", "cio"],
    "Senior": ["senior", "sr", "principal", "lead", "director"],
    "Mid-Level": ["mid-level", "midlevel", "mid", "specialist"],
    "Junior": ["junior", "jr", "associate", "assistant", "entry"],
    "Intern": ["intern", "trainee", "student"],
}


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower()
    lowered = lowered.replace("’", "'")
    lowered = re.sub(r"[^a-z0-9\s\+]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _score_education(raw: str | None) -> tuple[float, str]:
    normalized = _normalize(raw)
    for label, score, keywords in EDUCATION_TIERS:
        if any(keyword in normalized for keyword in keywords):
            return score, label.title()
    if raw:
        return 50.0, raw
    return 35.0, "Unspecified"


def _score_experience(years: float | None) -> float:
    if years is None:
        return 45.0
    capped = max(0.0, min(years, 20.0))
    return (capped / 20.0) * 100.0


def _score_skills(skills: List[str] | None) -> float:
    if not skills:
        return 35.0
    unique = {skill.lower().strip() for skill in skills if skill}
    capped = min(len(unique), 15)
    return (capped / 15.0) * 100.0


def _infer_level(candidate: Dict) -> str:
    base_text = " ".join(
        filter(
            None,
            [
                candidate.get("seniority"),
                candidate.get("title"),
            ],
        )
    )
    normalized = _normalize(base_text)
    for level_label, keywords in LEVEL_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return level_label
    return "Unknown"


def _build_explanation(level: str, years: float | None, similarity: float) -> str:
    years_text = f"{years:.1f} years" if years is not None else "unspecified tenure"
    sim_text = f"{similarity:.0f}% similarity"
    return f"{level} profile with {years_text} and {sim_text} against the query."


def _collect_strengths(skills_score: float, experience_score: float, similarity_score: float) -> List[str]:
    strengths: List[str] = []
    if skills_score >= 70:
        strengths.append("deep skill coverage")
    if experience_score >= 70:
        strengths.append("proven tenure")
    if similarity_score >= 70:
        strengths.append("high semantic match")
    return strengths


def _collect_gaps(skills_score: float, experience_score: float, similarity_score: float) -> List[str]:
    gaps: List[str] = []
    if skills_score < 55:
        gaps.append("limited documented skills")
    if experience_score < 55:
        gaps.append("light experience history")
    if similarity_score < 55:
        gaps.append("weak match to the job text")
    return gaps


def score_candidates(candidates: List[Dict], job_query: str | None = None) -> List[Dict]:
    """
    Lightweight ATS scoring used solely inside comparison_llm.
    Adds component scores and narrative hints required by the LLM prompt.
    """
    for candidate in candidates:
        years = candidate.get("years_numeric")
        skills = candidate.get("skills")
        similarity = float(candidate.get("similarity", 0.0))

        skills_score = _score_skills(skills)
        experience_score = _score_experience(years)
        education_score, education_label = _score_education(candidate.get("education"))
        similarity_score = max(0.0, min(similarity, 100.0))

        ats_score = (
            skills_score * WEIGHTS["skills"]
            + experience_score * WEIGHTS["experience"]
            + education_score * WEIGHTS["education"]
            + similarity_score * WEIGHTS["similarity"]
        )

        level_label = _infer_level(candidate)
        strengths = _collect_strengths(skills_score, experience_score, similarity_score)
        gaps = _collect_gaps(skills_score, experience_score, similarity_score)
        status = "ACCEPTED" if ats_score >= 70 else "REJECTED"

        candidate.update(
            {
                "skills_score": round(skills_score, 1),
                "experience_score": round(experience_score, 1),
                "education_score": round(education_score, 1),
                "similarity_score": round(similarity_score, 1),
                "ats_score": round(ats_score, 1),
                "education": candidate.get("education") or education_label,
                "inferred_seniority": level_label,
                "status": status,
                "rank_explanation": _build_explanation(level_label, years, similarity_score),
                "key_differentiators": strengths,
                "relative_weaknesses": gaps,
                "why_choose_this_one": "Balanced profile with " + ", ".join(strengths) if strengths else "",
                "why_not_choose_others": "Needs development in " + ", ".join(gaps) if gaps else "",
            }
        )
    return candidates

