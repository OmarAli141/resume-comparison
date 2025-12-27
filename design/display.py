"""
Display functions for candidate results.
"""
def print_profile_table(candidates):
    print(f"\nTOP {len(candidates)} CANDIDATES — PROFILE SUMMARY")
    print("=" * 140)
    print(f"{'#':<3} {'ID':<12} {'EDUCATION':<18} {'YEARS':<8} {'TOP SKILLS'}")
    print("-" * 140)
    for idx, c in enumerate(candidates[:10], 1):
        skills = ", ".join(c.get("skills", [])[:7])
        if len(c.get("skills", [])) > 7:
            skills += " (+more)"
        edu = str(c.get("education", "—"))[:17]
        years = c.get("years", "—")
        print(f"{idx:<3} {c['id']:<12} {edu:<18} {years:<8} {skills}")
    print("=" * 140)


def print_similarity_table(candidates):
    print(f"\nSIMILARITY TO JOB DESCRIPTION")
    print("=" * 120)
    print(f"{'#':<3} {'ID':<12} {'SIM%':>8} {'CATEGORY':<28}")
    print("-" * 120)
    for idx, c in enumerate(candidates[:10], 1):
        sim = c.get("similarity", 0)
        category = c.get("category") or "—"
        category_display = (category[:27] + "…") if len(category) > 28 else category
        print(f"{idx:<3} {c['id']:<12} {sim:>7.1f}%  {category_display:<28}")
    print("=" * 120)


def print_llm_results(analysis: dict):
    if not analysis:
        print("\nLLM returned no data.")
        return

    sorted_items = sorted(analysis.items(), key=lambda x: x[1].get("ats_fit_score", 0), reverse=True)

    print("\nFINAL AI RECRUITER RECOMMENDATION")
    print("=" * 140)
    for rank, (cid, data) in enumerate(sorted_items, 1):
        score = data.get("ats_fit_score", 0)
        level = data.get("level_fit", "Unknown")
        print(f"\n#{rank} → ID: {cid} | AI ATS SCORE: {score}/100 | Level: {level}")
        print(f"   Summary       → {data.get('overall_summary', 'N/A')}")
        print(f"   Why hire      → {data.get('why_choose_this_candidate', 'N/A')}")
        if data.get("unique_strengths"):
            print(f"   Unique edges  →", " | ".join(data["unique_strengths"][:3]))
        if data.get("potential_risks"):
            print(f"   Risks         → {data.get('potential_risks')}")
        print(f"   Recommendation→ {data.get('final_recommendation', 'N/A')}")
        print("-" * 140)


def select_llm_backend():
    """Select LLM backend (Gemini or Ollama)."""
    from llm_comparison.llm_client import set_llm_backend
    
    print("\nAI recruiter engine options:")
    print("1. Gemini 2.5 Flash")
    print("2. qwen2.5:1.5b")
    while True:
        choice = input("Choose LLM backend (1 or 2): ").strip() or "2"
        if choice == "1":
            set_llm_backend("gemini")
            print("Gemini backend selected.")
            return
        if choice == "2":
            set_llm_backend("local")
            print("Ollama qwen backend selected.")
            return
        print("Please enter 1 for Gemini or 2 for qwen.")

