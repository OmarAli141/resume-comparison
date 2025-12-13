"""
Clean job descriptions and create structured chunks.
Creates a new JSON file with:
- position_title
- structured_chunks (array of labeled strings like "Job Title: ...", "Required Skills: ...")
"""

import json
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from match_resumes_to_jd import prepare_jd_query_chunks

ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "extracted_data" / "job_descriptions_filtered.json"
OUTPUT_FILE = ROOT / "extracted_data_final" / "job_descriptions_cleaned.json"

def process_job_descriptions():
    """Process all job descriptions and create structured chunks."""
    print(f"Loading from: {INPUT_FILE}")
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        jds = json.load(f)
    
    print(f"Processing {len(jds)} job descriptions...")
    
    structured_jds = []
    
    for idx, jd in enumerate(jds, 1):
        if idx % 100 == 0:
            print(f"  Processed {idx}/{len(jds)}...")
        
        # Extract position title
        position_title = jd.get("position_title", "Unknown Position").strip()
        
        # Generate structured chunks using the existing function
        structured_chunks = prepare_jd_query_chunks(jd)
        
        # Create structured entry
        structured_entry = {
            "position_title": position_title,
            "structured_chunks": structured_chunks
        }
        
        structured_jds.append(structured_entry)
    
    # Save to new file
    print(f"\nSaving to: {OUTPUT_FILE}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structured_jds, f, ensure_ascii=False, indent=2)
    
    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"Done! Saved {len(structured_jds)} job descriptions → {OUTPUT_FILE} ({size_kb:.1f} KB)")
    
    # Show sample
    if structured_jds:
        print(f"\nSample structured job description:")
        sample = structured_jds[0]
        print(f"  Position Title: {sample['position_title']}")
        print(f"  Number of chunks: {len(sample['structured_chunks'])}")
        print(f"\n  Structured chunks:")
        for i, chunk in enumerate(sample['structured_chunks'][:3], 1):
            print(f"    {i}. {chunk[:100]}...")


if __name__ == "__main__":
    process_job_descriptions()

