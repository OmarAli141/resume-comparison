MAX_LLM_CANDIDATES = 3
MAX_SKILLS = 7

def format_candidates_for_llm(candidates: list) -> str:
    lines = []
    for i, c in enumerate(candidates[:MAX_LLM_CANDIDATES], 1):
        skills = ", ".join(c.get("skills", [])[:MAX_SKILLS])
        if len(c.get("skills", [])) > MAX_SKILLS:
            skills += " (+more)"
        if not skills.strip():
            skills = "Not listed"

        level = c.get("inferred_seniority", "Unknown")
        ats = c.get("ats_score", 0)
        status = "ACCEPTED" if ats >= 70 else "REJECTED"

        lines.append(f"CANDIDATE #{i} — ID: {c['id']} | Current ATS: {ats:.1f} | Status: {status}")
        lines.append(f"   Level: {level} | Experience: {c.get('years', 'N/A')} | Education: {c.get('education', 'N/A')}")
        lines.append(f"   Job Title: {c.get('title', 'N/A')}")
        lines.append(f"   Top Skills: {skills}")
        lines.append(f"   Scores → Skills:{c.get('skills_score',0):.0f} | Exp:{c.get('experience_score',0):.0f} | Edu:{c.get('education_score',0):.0f} | Sim:{c.get('similarity_score',0):.0f}")
        lines.append("")

    return "\n".join(lines).strip()