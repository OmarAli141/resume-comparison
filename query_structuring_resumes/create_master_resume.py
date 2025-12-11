import json
import re
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("extracted_data/master_resumes.json") 
OUTPUT_FILE = Path("extracted_data/master_resumes_cleaned.json")

CUTOFF_DATE = "2018-12-31"

def clean_job_title(title: str) -> str:
    """
    Cleans the resume's main job title.
    - Replaces meaningless titles like 'Company Name', 'Unknown Role', 'N/A' with 'Unknown Role'.
    - Removes trailing decorations like '| …'.
    - Collapses multiple spaces.
    - Truncates very long titles to 80 characters.
    """
    if not title or title.strip() in ["Company Name", "Unknown Role", "N/A"]:
        return "Unknown Role"
    # Remove garbage
    title = re.sub(r"^(Company Name|Unknown Company).*", "Unknown Role", title, flags=re.I)
    title = re.sub(r"\s*\|\s*.+$", "", title)
    title = re.sub(r"\s{2,}", " ", title.strip())
    return title if len(title) < 80 else title[:77] + "..."

def fix_current_dates(date_str: str) -> str:
    """
    Replaces current or missing job dates with a fixed cutoff date.
    Ensures consistency when calculating total experience.
    """
    if not date_str:
        return CUTOFF_DATE
    date_str = str(date_str).strip()
    if date_str.lower() in ["present", "current", "now", "today"]:
        return CUTOFF_DATE
    return date_str

def extract_real_title_from_history(work_history):
    """
    If the main job title is unknown, searches the work_history for a real job title.
    Ignores short or invalid entries that look like dates or placeholders.
    """
    for job in work_history:
        t = job.get("title", "")
        if t and len(t) > 5 and t != "Company Name" and "20" not in t[:10]:
            return t
    return None

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

master_db = {}

for resume in data:
    category = resume.get("category", "UNKNOWN").upper()
    if category == "INFORMATION-TECHNOLOGY":
        category = "INFORMATION-TECHNOLOGY"
    master_db.setdefault(category, [])

    # Fix job title
    raw_title = resume.get("job_title", "")
    clean_title = clean_job_title(raw_title)
    
    # Fallback from first real job
    if clean_title == "Unknown Role":
        fallback = extract_real_title_from_history(resume.get("work_history", []))
        if fallback:
            clean_title = fallback

    # Fix dates
    for job in resume.get("work_history", []):
        job["start_date"] = fix_current_dates(job.get("start_date"))
        job["end_date"] = fix_current_dates(job.get("end_date"))
        job["company"] = "Confidential" if "Company Name" in str(job.get("company","")) else job.get("company", "Confidential")

    # Recalculate total years properly
    total_years = 0.0
    for job in resume.get("work_history", []):
        try:
            s = datetime.strptime(job["start_date"], "%Y-%m-%d")
            e = datetime.strptime(job["end_date"], "%Y-%m-%d")
            years = (e - s).days / 365.25
            if years > 0:
                total_years += years
        except:
            continue
    total_years = round(total_years, 1)

    seniority = "senior" if total_years >= 8 else "mid" if total_years >= 4 else "junior" if total_years > 0 else "unknown"

    clean_resume = {
        "id": resume["id"],
        "job_title": clean_title,
        "seniority": seniority,
        "years_experience": total_years,
        "summary": resume.get("summary", "")[:1000].strip(),
        "education": resume.get("education", "Not specified").strip(),
        "skills": resume.get("skills", []) if isinstance(resume.get("skills"), list) else [],
        "work_history": resume.get("work_history", [])
    }

    master_db[category].append(clean_resume)

# Sort departments by size
final_db = dict(sorted(master_db.items(), key=lambda x: len(x[1]), reverse=True))

# SAVE FINAL MASTER FILE
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_db, f, indent=2, ensure_ascii=False)

print("MASTER RESUMES DATABASE CREATED!")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Total departments: {len(final_db)}")
print(f"Total resumes: {sum(len(v) for v in final_db.values())}")
for dept, count in list(final_db.items())[:10]:
    print(f"   {len(count):3d} × {dept}")
