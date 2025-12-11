import json
from pathlib import Path
import re

ROOT = Path(__file__).parent.parent
INPUT = ROOT / "extracted_data" / "master_resumes_cleaned.json"   
OUTPUT = ROOT / "extracted_data_final" / "master_resumes_cleaned_final.json"

# Loads the cleaned resumes file into memory.
with open(INPUT, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

def calculate_seniority(years: float) -> str:
    if years < 0.5: return "Intern/Student"
    elif years < 4: return "Junior"
    elif years < 8: return "Mid-level"
    elif years < 15: return "Senior"
    elif years < 25: return "Lead / Principal"
    else: return "Manager / Executive"

def extract_education(edu_data) -> str:
    if not edu_data:
        return "—"
    
    # Handle both string and list formats
    if isinstance(edu_data, str):
        edu_text = edu_data.lower()
    elif isinstance(edu_data, list):
        edu_text = " ".join(str(e).lower() for e in edu_data if e)
    else:
        edu_text = str(edu_data).lower()
    
    if not edu_text or not edu_text.strip():
        return "—"
    
    # Priority order (highest first): PhD > Master's > Bachelor's
    # PhD/Doctorate
    if any(keyword in edu_text for keyword in ["phd", "ph.d", "ph. d", "doctor", "doctorate", "d.phil", "doctoral"]):
        return "PhD"
    
    # Master's
    if any(keyword in edu_text for keyword in ["master", "ms", "m.s", "m. s", "msc", "m.sc", "mba", "m.b.a", "ma", "m.a"]):
        return "Master's"
    
    # Bachelor's
    if any(keyword in edu_text for keyword in ["bachelor", "bs", "b.s", "b. s", "bsc", "b.sc", "ba", "b.a", "btech", "b.tech"]):
        return "Bachelor's"
    
    return "—"

def clean_title(title: str) -> str:
    if not title: return "Professional Role"
    bad = {"jan", "feb", "mar", "present", "city", "state", "n/a", "unknown", "tbd"}
    title = str(title).strip()
    if any(x in title.lower() for x in bad) or len(title) < 3:
        return "Professional Role"
    return title.strip()

def clean_skills(skills) -> list:
    if not skills: return []
    cleaned = []
    seen = set()
    for s in skills:
        s = str(s).strip()
        if len(s) < 2 or len(s) > 45: continue
        if any(b in s.lower() for b in {"magic", "pick", "reference", "additional"}): continue
        s = re.sub(r"[•–—]", "", s).strip(" :.")
        if s.lower() not in seen:
            seen.add(s.lower())
            cleaned.append(s.title())
        if len(cleaned) >= 15:
            break
    return cleaned

cleaned_master = {}

for dept, resumes in raw_data.items():
    cleaned_master[dept] = []
    for r in resumes:
        years = float(r.get("total_years_experience") or r.get("years_experience") or 0)
        
        # Category is the department key, formatted nicely
        category = str(dept).replace("_", " ").replace("-", " ").title()

        clean_resume = {
            "id": r["id"],
            "category": category,                              # Category right after id
            "job_title": clean_title(r.get("job_title")),
            "total_years_experience": round(years, 1),
            "seniority": calculate_seniority(years),           # CORRECT FROM DAY 1
            "education_level": extract_education(r.get("education", "")),  # CLEAN EDUCATION (string or list)
            "skills": clean_skills(r.get("skills", [])),       # CLEAN SKILLS
            "work_history": r.get("work_history", [])[:5]      # First 5 work history entries
        }
        cleaned_master[dept].append(clean_resume)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(cleaned_master, f, indent=2, ensure_ascii=False)

print(f"FINAL CLEAN DATA SAVED → {OUTPUT}")
print(f"Total resumes: {sum(len(v) for v in cleaned_master.values())}")
print("Now your retrieval phase NEVER needs to clean anything again!")
