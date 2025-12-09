from pathlib import Path
from extract_text import extract_text_from_pdf
from resume_parser import parse_resume
import json
from datetime import datetime

# CHANGE THESE TO TEST ANY RESUME YOU WANT
TEST_FILES = [
    "data/data/INFORMATION-TECHNOLOGY/10840430.pdf",
    # "data/data/INFORMATION-TECHNOLOGY/another_resume.pdf",  # add more if you want
]

OUTPUT_JSON = Path("extracted_data_final/debug_output.json")

def main():
    print("DEBUG TEST MODE — ONLY SELECTED RESUMES\n")
    
    results = []

    for file_path_str in TEST_FILES:
        path = Path(file_path_str)
        if not path.exists():
            print(f"NOT FOUND: {file_path_str}")
            continue

        print(f"{'='*80}")
        print(f"PROCESSING: {path.name}")
        print(f"{'='*80}")

        text = extract_text_from_pdf(path)
        print(f"Extracted text: {len(text.split())} words, {len(text)} chars\n")

        parsed = parse_resume(text, resume_id=path.stem, category=path.parent.name)

        # Add timestamp
        parsed["_debug_file"] = str(path)
        parsed["_parsed_at"] = datetime.now().isoformat()

        results.append(parsed)

        # Pretty print in console
        print(f"ID           : {parsed['id']}")
        print(f"Category     : {parsed['category']}")
        print(f"Current Role : {parsed['job_title']}")
        print(f"Seniority    : {parsed['seniority'].upper()} → {parsed['years_experience']} years total")
        jobs = parsed.get("work_history", [])
        print(f"Jobs Found   : {len(jobs)}\n")

        for i, job in enumerate(jobs, 1):
            print(f"  [{i}] {job['title']}")
            print(f"      Company   : {job['company']}")
            print(f"      Period    : {job['start_date']} → {job['end_date']}")
            print(f"      Duration  : {job['duration_years']} years")
            print(f"      Desc words: {len(job['description'].split())}\n")

        print("-" * 80 + "\n")

    # SAVE TO JSON (pretty & readable)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"DONE!")
    print(f"Full parsed result saved to:")
    print(f"   {OUTPUT_JSON.resolve()}")
    print(f"\nOpen this file to see perfect structured JSON with ALL jobs")

if __name__ == "__main__":
    main()
