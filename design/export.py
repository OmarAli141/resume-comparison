"""
Export functions for candidate results.
"""
import json
from datetime import datetime
from pathlib import Path


def export_results_to_json(candidates: list, query: str, analysis: dict) -> str:
    """Export search results and LLM analysis to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recruiter_report_{timestamp}.json"
    exports_dir = Path(__file__).resolve().parent.parent / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    filepath = exports_dir / filename

    top_entries = []
    for idx, c in enumerate(candidates[:10], 1):
        top_entries.append(
            {
                "rank": c.get("rank", idx),
                "id": c.get("id"),
                "title": c.get("title"),
                "education": c.get("education"),
                "years_experience": c.get("years"),
                "similarity_score": c.get("similarity"),
                "top_skills": c.get("skills", [])[:15],
            }
        )

    report = {
        "generated_at": datetime.now().isoformat(),
        "job_query": query,
        "candidates_found": len(candidates),
        "top_candidates": top_entries,
        "ai_recruiter_analysis": analysis
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return str(filepath)

