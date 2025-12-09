import os  # operating system module
import re  # regular expressions module
import sys  # system module

# Ensures the script can import your local module work_history_parser.py
sys.path.append(os.path.dirname(__file__)) 

from work_history_parser import split_into_jobs, calculate_total_experience

# Dictionary mapping section names to their corresponding keywords
SECTION_KEYWORDS = {
    "summary": [
        "professional summary",
        "executive summary",
        "summary",
        "profile",
        "objective",
        "about",
    ],
    "experience": [
        "work experience",
        "professional experience",
        "experience",
        "employment history",
        "career history",
        "work history",
    ],
    "education": [
        "education",
        "education and training",
        "academic background",
        "educational background",
        "academic qualifications",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "competencies",
        "areas of expertise",
    ],
}

DEGREE_PATTERN = re.compile(
    r"(?i)\b("
    r"associate|bachelor|master|doctor|ph\.?d|mba|b\.?s|m\.?s|bba|"
    r"ba|ma|beng|meng|bsci|msci|jd|md|diploma"
    r")\b[^\n\.]*"
)


def _normalize_text(text: str) -> str:
    """
    Normalizes the text by replacing carriage returns with newlines and removing extra whitespace.
    Args:
        text: The text to normalize
    Returns:
        The normalized text
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _find_heading(text: str, keyword: str, start: int = 0):
    """
    Finds the first occurrence of a keyword in the text.
    Args:
        text: The text to search
        keyword: The keyword to search for
        start: The starting position in the text
    Returns:
        The match object if the keyword is found, otherwise None
    """
    pattern = re.compile(rf"(?im)^\s*{re.escape(keyword)}\b", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(text, pos=start)
    return match


def extract_section(text: str, section: str) -> str:
    """
    Extracts a specific section from the text.
    Args:
        text: The text to search
        section: The section to extract
    Returns:
        The extracted section
    """
    normalized = _normalize_text(text)
    keywords = SECTION_KEYWORDS.get(section, [])

    start_match = None
    for keyword in keywords:
        match = _find_heading(normalized, keyword)
        if match and (not start_match or match.start() < start_match.start()):
            start_match = match

    if not start_match:
        return ""

    heading_end = normalized.find("\n", start_match.end())
    if heading_end == -1:
        heading_end = start_match.end()
    start_idx = heading_end + 1
    end_idx = len(normalized)

    for other_section, other_keywords in SECTION_KEYWORDS.items():
        if other_section == section:
            continue
        for keyword in other_keywords:
            match = _find_heading(normalized, keyword, start_idx)
            if match and match.start() < end_idx:
                end_idx = match.start()

    return normalized[start_idx:end_idx].strip()


def extract_degrees(text: str) -> str:
    """
    Extracts degrees from the text.
    Args:
        text: The text to search
    Returns:
        The extracted degrees
    """
    if not text:
        return ""
    lines = []
    for match in DEGREE_PATTERN.finditer(text):
        snippet = match.group(0).strip(" :-•\n")
        if snippet:
            lines.append(snippet)
    if not lines:
        chunks = re.split(r"[\n;•]+", text)
        for chunk in chunks:
            if re.search(DEGREE_PATTERN, chunk):
                lines.append(chunk.strip())
    unique = []
    for line in lines:
        if line and line not in unique:
            unique.append(line)
    return " | ".join(unique[:5])


def extract_skills(text: str) -> list:
    """
    Extracts skills from the text.
    Args:
        text: The text to search
    Returns:
        The extracted skills
    """
    if not text:
        return []
    parts = re.split(r"[,;\n•]+", text)
    skills = []
    for part in parts:
        value = part.strip(" -")
        if len(value) > 2:
            skills.append(value)
    return skills[:40]


def parse_resume(text: str, resume_id: str, category: str):
    """
    Parses a resume and extracts the relevant information.
    Args:
        text: The text to search
        resume_id: The ID of the resume
        category: The category of the resume
    Returns:
        A dictionary containing the parsed resume information
    """
    summary_text = extract_section(text, "summary")
    if not summary_text or len(summary_text) < 50:
        summary_text = text[:1000]

    education_text = extract_section(text, "education")
    skills_text = extract_section(text, "skills")
    experience_text = extract_section(text, "experience") or text

    jobs = split_into_jobs(experience_text)
    if not jobs:
        jobs = split_into_jobs(text)

    total_years = calculate_total_experience(jobs)

    if total_years >= 8:
        seniority = "senior"
    elif total_years >= 4:
        seniority = "mid"
    elif total_years > 0:
        seniority = "junior"
    else:
        seniority = "unknown"

    current_title = jobs[0]["title"] if jobs else "Unknown Role"

    return {
        "id": resume_id,
        "category": category.upper(),
        "job_title": current_title,
        "seniority": seniority,
        "years_experience": round(total_years, 1),
        "summary": re.sub(r"\s+", " ", summary_text).strip(),
        "education": extract_degrees(education_text or text),
        "skills": extract_skills(skills_text),
        "work_history": jobs,
    }