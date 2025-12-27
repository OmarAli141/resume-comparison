import json
from pathlib import Path


def generate_fake_contacts():
    """
    Add fake LinkedIn profiles and Gmail accounts to each resume in
    master_resumes_cleaned_final.json.

    This updates the JSON file in-place. Existing `email` or `linkedin_url`
    fields are left untouched.
    """
    root = Path(__file__).resolve().parent.parent
    data_path = root / "extracted_data_final" / "master_resumes_cleaned_final.json"
    output_path = root / "extracted_data_final" / "master_resumes_cleaned_final_with_fake_contacts.json"

    if not data_path.exists():
        print(f"Data file not found at: {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    changed = False

    for _, resumes in db.items():
        for r in resumes:
            rid = str(r.get("id", "")).strip()
            if not rid:
                continue

            # Only add if not already present
            if "email" not in r or not r["email"]:
                r["email"] = f"candidate_{rid}@gmail.com"
                changed = True

            if "linkedin_url" not in r or not r["linkedin_url"]:
                r["linkedin_url"] = f"https://www.linkedin.com/in/candidate-{rid}"
                changed = True

    if not changed:
        print("No changes needed; all resumes already have contact fields.")
        return

    # Write to a NEW file so the original JSON stays untouched
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"Fake contact details written to: {output_path}")


if __name__ == "__main__":
    generate_fake_contacts()


