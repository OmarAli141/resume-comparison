# ULTRA-CLEAN VERSION — Data is already perfect from extraction

import json
from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).parent.parent
CHROMA_PATH = ROOT / "chroma_db"
MASTER_DB_PATH = ROOT / "extracted_data_final" / "master_resumes_cleaned_final.json"

# Load clean master data
with open(MASTER_DB_PATH, "r", encoding="utf-8") as f:
    MASTER_DB = json.load(f)

# Fast lookup: ID → (resume, department)
RESUME_LOOKUP = {
    str(r["id"]): (r, dept)
    for dept, resumes in MASTER_DB.items()
    for r in resumes
}

client = chromadb.PersistentClient(path=str(CHROMA_PATH))
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

resume_collection = client.get_collection(name="resumes_master")
jd_collection = client.get_collection(name="job_descriptions")


# NO CLEANING ANYMORE — DATA IS ALREADY PERFECT
def extract_candidate_profile(resume: dict, fallback_category: str | None = None) -> Dict:
    years = resume["total_years_experience"]
    years_str = f"{years:.1f}y" if years >= 1 else "<1y" if years > 0 else "—"

    return {
        "id": resume["id"],
        "seniority": resume["seniority"],
        "title": resume["job_title"],
        "years": years_str,
        "years_numeric": years,
        "category": resume["category"],
        "education": resume["education_level"],
        "education_normalized": resume.get("education_level", ""),
        "skills": resume["skills"],
        "skills_display": " • ".join(resume["skills"]) if resume["skills"] else "—",
        "resume": resume
    }


# SEARCH FUNCTIONS — WITH METADATA FILTERS (seniority level and skills)
def search_by_text(query: str, top_k: int = 10, seniority_filter: str | None = None, skills_filter: List[str] | None = None) -> List[Dict]:
    """
    Search by text with optional filters.
    Args:
        query: Search query
        top_k: Number of results (default 10)
        seniority_filter: Filter by seniority level (e.g., "Junior", "Senior", "Mid-level")
        skills_filter: List of required skills to filter by
    """
    query_lower = query.lower()
    where = None
    
    # Auto-detect seniority from query if not specified
    if seniority_filter:
        where = {"seniority": {"$eq": seniority_filter}}
    elif any(x in query_lower for x in ["junior", "jr", "entry", "fresh", "intern"]):
        where = {"seniority": {"$in": ["Junior", "Intern/Student"]}}
    elif any(x in query_lower for x in ["senior", "sr", "lead", "principal", "manager", "executive"]):
        where = {"seniority": {"$in": ["Senior", "Lead / Principal", "Manager / Executive"]}}
    
    # Add skills filter if provided
    if skills_filter:
        if where:
            where["skills"] = {"$in": skills_filter}
        else:
            where = {"skills": {"$in": skills_filter}}

    return resume_collection.query(
        query_texts=[query],
        n_results=top_k * 2,  # Get more to filter duplicates
        where=where,
        include=["distances", "metadatas"]
    )


def search_by_job_description(
    query: str,
    top_k: int = 10,
    seniority_filter: str | None = None,
    skills_filter: List[str] | None = None,
) -> List[Dict] | None:
    """
    Two-stage search that makes REAL use of job-description embeddings.

    1) Use the free-text `query` to search the job_descriptions collection
       and find the most similar real job description.
    2) Take that full JD text and use it to search the resume embeddings.

    This way, any natural-language query ("senior accountant with master's degree...")
    is first grounded to an actual JD, then matched to resumes.
    """
    # --- Stage 1: find the closest real JD by semantic similarity ---
    jd_results = jd_collection.query(
        query_texts=[query],
        n_results=1,
        include=["documents", "metadatas", "distances"],
    )

    if not jd_results.get("ids") or not jd_results["ids"][0]:
        return None

    # Concatenate all chunks of the best-matching JD
    jd_docs = jd_results.get("documents", [[]])[0]
    if not jd_docs:
        return None
    full_jd = " ".join(jd_docs)

    best_meta_list = jd_results.get("metadatas", [[]])[0] or []
    best_meta = best_meta_list[0] if best_meta_list else {}
    title_lower = str(best_meta.get("position_title") or query).lower()

    # --- Stage 2: search resumes using the rich JD text ---
    where = None

    # Auto-detect seniority from JD title (or fallback to original query) if not specified
    if seniority_filter:
        where = {"seniority": {"$eq": seniority_filter}}
    elif any(x in title_lower for x in ["junior", "jr", "entry"]):
        where = {"seniority": {"$in": ["Junior", "Intern/Student"]}}
    elif any(x in title_lower for x in ["senior", "sr", "lead", "manager", "principal"]):
        where = {"seniority": {"$in": ["Senior", "Lead / Principal", "Manager / Executive"]}}

    # Add skills filter if provided
    if skills_filter:
        if where:
            where["skills"] = {"$in": skills_filter}
        else:
            where = {"skills": {"$in": skills_filter}}

    return resume_collection.query(
        query_texts=[full_jd],
        n_results=top_k * 2,  # Get more to filter duplicates
        where=where,
        include=["distances", "metadatas"],
    )