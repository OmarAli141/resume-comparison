"""
Post-search contact / LinkedIn interaction helpers.

These functions are used after candidates have been scored and displayed.
"""

from typing import List, Dict, Any, Tuple


def get_candidate_contact_info(candidate: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """
    Extract (email, linkedin_url) for a candidate.

    Falls back to fake Gmail / LinkedIn values based on candidate ID if
    explicit fields are missing.
    """
    resume = candidate.get("resume", {}) or {}
    cid = str(candidate.get("id", "")).strip()

    email = resume.get("email")
    linkedin = resume.get("linkedin_url")

    if not email and cid:
        email = f"candidate_{cid}@gmail.com"
    if not linkedin and cid:
        linkedin = f"https://www.linkedin.com/in/candidate-{cid}"

    return email, linkedin


def contact_followup_flow(candidates: List[Dict[str, Any]]) -> None:
    """
    Interactive flow AFTER results & LLM analysis:

    - Ask user if they want to:
        * open/check LinkedIn profile
        * contact via email
        * or skip
    - Works on the ranked `similarity_ranked` list from main.py.
    """
    if not candidates:
        return

    while True:
        action = (
            "\nDo you want to LinkedIn a candidate, Email a candidate, "
            "or None? (Linkedin/Email/None): "
        )
        choice = input(action).strip().lower()

        if choice in {"n", ""}:
            # User is done with this flow
            return
        if choice not in {"l", "e"}:
            print("Please enter 'l', 'e', or 'n'.")
            continue

        # Ask which candidate (by index as shown in tables)
        try:
            idx_raw = input(f"Enter candidate number (1-{len(candidates)}): ").strip()
            idx = int(idx_raw) - 1
        except ValueError:
            print("Please enter a valid number.")
            continue

        if not (0 <= idx < len(candidates)):
            print("Number out of range.")
            continue

        candidate = candidates[idx]
        email, linkedin = get_candidate_contact_info(candidate)
        title = candidate.get("title") or "Unknown Title"

        if choice == "e":
            if not email:
                print("No email available for this candidate.")
                continue
            print(
                f"\nPretending to send an email to {email} "
                f"about role '{title}'."
            )
        else:  # choice == "l"
            if not linkedin:
                print("No LinkedIn URL available for this candidate.")
                continue
            print(f"\nOpening LinkedIn profile:\n  {linkedin}")


