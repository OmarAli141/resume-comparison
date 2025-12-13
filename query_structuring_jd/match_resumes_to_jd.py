from typing import List, Tuple
import re

_SECTION_ORDER = [
    ("position_title", "Job Title"),
    ("Required Skills", "Required Skills"),
    ("Preferred Qualifications", "Preferred Qualifications"),
    ("Core Responsibilities", "Core Responsibilities"),
    ("Experience Level", "Experience Level"),
    ("Education", "Education"),
    ("Location", "Location"),
]


def _clean_text(value) -> str:
    """Normalize text: remove bullets, fix spacing, skip N/A."""
    if not value or str(value).strip().lower() in {"n/a", "not available", "none"}:
        return ""

    if isinstance(value, list):
        value = "; ".join(str(v).strip() for v in value if v and str(v).strip())
    elif isinstance(value, dict):
        parts = [f"{k}: {_clean_text(v)}" for k, v in value.items() if _clean_text(v)]
        value = "; ".join(parts)

    text = str(value)
    text = re.sub(r"[•·▪►–]", "-", text)
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.strip() for line in text.split("\n") if line.strip()).strip()


def _iter_structured_sections(jd_entry: dict) -> List[Tuple[str, str]]:
    sections = []
    model = jd_entry.get("model_response", {})

    for raw_key, label in _SECTION_ORDER:
        source = jd_entry if raw_key == "position_title" else model
        text = _clean_text(source.get(raw_key, ""))
        if text:
            sections.append((label, text))

    # Add any extra keys from model_response (rare)
    used = {k for k, _ in _SECTION_ORDER if k != "position_title"}
    for key, val in model.items():
        if key not in used:
            cleaned = _clean_text(val)
            if cleaned:
                sections.append((key.title(), cleaned))

    return sections


def prepare_jd_query_chunks(jd_entry: dict) -> List[str]:
    """Return list of clean, labeled chunks ready for embedding."""
    sections = [f"{label}: {text}" for label, text in _iter_structured_sections(jd_entry)]

    final_chunks = []
    for section in sections:
        if len(section) <= 1000:
            final_chunks.append(section)
            continue

        # Split long sections safely
        sentences = re.split(r"(?<=[.;])\s+", section)
        buffer = ""
        for s in sentences:
            if len(buffer) + len(s) + 1 > 900:
                if buffer:
                    final_chunks.append(buffer.strip())
                buffer = s
            else:
                buffer = f"{buffer} {s}".strip() if buffer else s
        if buffer:
            final_chunks.append(buffer.strip())

    return [c for c in final_chunks if len(c) > 25]

