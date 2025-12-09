import json
from pathlib import Path
from tqdm import tqdm
import os
import sys

# Make sure we can import our local modules
sys.path.append(os.path.dirname(__file__))

from extract_text import extract_text_from_pdf
from resume_parser import parse_resume


DATA_ROOT = Path("data/data")
OUTPUT_FILE = Path("extracted_data/master_resumes.json")


def main():
    print("STARTING FULL RESUME EXTRACTION")
    print(f"Looking in: {DATA_ROOT.resolve()}\n")

    # Validate input directory
    if not DATA_ROOT.exists():
        print(f"ERROR: {DATA_ROOT} not found!")
        return

    all_resumes = []

    # Get all subfolders (categories)
    category_dirs = [d for d in DATA_ROOT.iterdir() if d.is_dir()]

    for cat_dir in category_dirs:
        category = cat_dir.name.upper()  # Normalize category label
        pdfs = list(cat_dir.glob("*.pdf"))  # Get all PDF files in the category
        if not pdfs:
            continue

        print(f"Processing {len(pdfs)} resumes → {category}")

        for pdf_path in tqdm(pdfs, desc=category, leave=False):
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                continue

            resume_id = pdf_path.stem
            try:
                # Convert raw text into structured resume fields
                parsed = parse_resume(text, resume_id, category)
                all_resumes.append(parsed)
            except Exception as e:
                print(f"Failed {pdf_path.name}: {e}")

    # Save all parsed resumes as JSON
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_resumes, f, indent=2, ensure_ascii=False)

    # Statistics
    total = len(all_resumes)
    seniors = sum(1 for r in all_resumes if r["seniority"] == "senior")
    mids = sum(1 for r in all_resumes if r["seniority"] == "mid")
    juniors = sum(1 for r in all_resumes if r["seniority"] == "junior")

    print("\n" + "="*70)
    print("EXTRACTION COMPLETE — ALL PAST JOBS EXTRACTED")
    print(f"Total: {total} | Senior: {seniors} | Mid: {mids} | Junior: {juniors}")
    print(f"Saved → {OUTPUT_FILE.resolve()}")
    print("="*70)


if __name__ == "__main__":
    main()