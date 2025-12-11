import json
import re
from pathlib import Path

INPUT_JSON  = Path("extracted_data/master_resumes_cleaned.json") 
OUTPUT_JSON = Path("extracted_data/master_resumes_cleaned.json")

def clean_description(raw: str) -> str:
    """
    Turns the giant bullet-list string (with \n, Company Name, weird chars)
    into beautiful, readable, professional paragraphs.
    """
    if not raw or not isinstance(raw, str):
        return ""

    text = raw

    # 1. Remove company header completely
    text = re.sub(r"Company Name[^\n]*\n?", "", text, flags=re.I)
    text = re.sub(r"City\s*,\s*State[^\n]*", "", text, flags=re.I)

    # 2. Split into lines and clean each one
    clean_lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Remove bullet symbols
        line = re.sub(r"^[-•·▪▫‣⁃◦]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)   # numbered lists

        # Remove lingering weird characters
        line = line.replace("ï¼", "").replace("â€“", "-")

        # Skip very short leftover garbage
        if len(line) < 8:
            continue

        clean_lines.append(line.strip())

    # 3. Group into logical paragraphs (blank line = new paragraph)
    paragraphs = []
    current = []

    for line in clean_lines:
        # If line ends with . : ; or is very long → sentence end
        if line.endswith(('.', ':', ';')) or len(line) > 120:
            current.append(line)
            paragraphs.append(" ".join(current))
            current = []
        else:
            current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    # 4. Join with double newline → beautiful readable text
    final_text = "\n\n".join(paragraphs)

    # 5. Final polish
    final_text = re.sub(r"\s+", " ", final_text)           # collapse spaces
    final_text = re.sub(r"\n\s*\n\s*\n", "\n\n", final_text)  # max 2 newlines
    return final_text.strip()


print("CLEANING JOB DESCRIPTIONS – MAKING THEM BEAUTIFUL...")
print(f"Reading: {INPUT_JSON}")

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    db = json.load(f)

total_jobs = 0
for department, resumes in db.items():
    for resume in resumes:
        for job in resume.get("work_history", []):
            old_desc = job.get("description", "")
            if old_desc:
                total_jobs += 1
                job["description"] = clean_description(old_desc)

# Save the new masterpiece
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"DONE! {total_jobs} job descriptions cleaned & polished")
print(f"FINAL FILE → {OUTPUT_JSON}")
print("\nExample of the magic (first job description):")
example = None
for resumes in db.values():
    for r in resumes:
        if r.get("work_history"):
            example = r["work_history"][0]["description"]
            break
    if example:
        break

print("\n" + "="*80)
print(example[:1000])
if len(example) > 1000:
    print("...")
print("="*80)
