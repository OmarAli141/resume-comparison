import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
RESUMES_PATH = ROOT / "extracted_data_final" / "master_resumes_cleaned_final.json"
CHROMA_PATH = ROOT / "chroma_db"

client = chromadb.PersistentClient(path=str(CHROMA_PATH))
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5")

collection = client.get_or_create_collection(
    name="resumes_master",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

# CLEAR OLD DATA
existing = collection.get(include=[])["ids"]
if existing:
    logger.info(f"Clearing {len(existing)} old resume chunks...")
    collection.delete(ids=existing)

# LOAD RESUMES
with open(RESUMES_PATH, "r", encoding="utf-8") as f:
    master_db = json.load(f)

docs, metas, ids = [], [], []
resume_count = 0

for department, resumes in master_db.items():
    for resume in resumes:
        resume_id = str(resume["id"])
        job_title = resume["job_title"]
        seniority = resume["seniority"]
        years_exp = resume.get("years_experience", 0)
        summary = resume.get("summary", "")[:1000]
        skills = resume.get("skills", [])
        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)

        # CHUNK 1: Professional Identity
        docs.append(f"Candidate ID: {resume_id} | Role: {job_title} | Seniority: {seniority} | {years_exp}+ years experience | Department: {department}")
        metas.append({"type": "identity", "resume_id": resume_id, "job_title": job_title, "seniority": seniority})
        ids.append(f"{resume_id}_identity")

        # CHUNK 2: Summary
        if summary.strip():
            docs.append(f"Professional Summary: {summary}")
            metas.append({"type": "summary", "resume_id": resume_id})
            ids.append(f"{resume_id}_summary")

        # CHUNK 3: Skills
        if skills_str.strip():
            docs.append(f"Technical & Professional Skills: {skills_str}")
            metas.append({"type": "skills", "resume_id": resume_id})
            ids.append(f"{resume_id}_skills")

        # CHUNK 4: Each Job Experience (Rich Description)
        for idx, job in enumerate(resume.get("work_history", [])):
            desc = job.get("description", "").strip()
            if not desc:
                continue

            # Clean and enhance job chunk
            title = job.get("title", "Unknown Role")
            company = job.get("company", "Confidential")
            start = job.get("start_date", "")[:4]
            end = job.get("end_date", "")[:4]
            duration = job.get("duration_years", 0)

            enhanced = (
                f"Experience #{idx+1}: {title} at {company} "
                f"({start}–{end if end != 'None' else 'Present'}, {duration} years)\n"
                f"Responsibilities & Achievements: {desc}"
            )

            docs.append(enhanced)
            metas.append({
                "type": "experience",
                "resume_id": resume_id,
                "job_index": idx,
                "job_title": title,
                "duration_years": duration
            })
            ids.append(f"{resume_id}_exp_{idx}")

        resume_count += 1

# ADD TO CHROMA IN SAFE BATCHES
MAX_BATCH = 5000
logger.info(f"Embedding {len(docs)} chunks across {resume_count} resumes (batch size ≤ {MAX_BATCH})")
for start in range(0, len(docs), MAX_BATCH):
    end = start + MAX_BATCH
    collection.add(
        documents=docs[start:end],
        metadatas=metas[start:end],
        ids=ids[start:end]
    )

logger.info(f"SUCCESS! Embedded {len(docs)} rich chunks from {resume_count} resumes")
logger.info(f"Collection 'resumes_master' is now ready for ultra-accurate candidate matching")
