import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
JD_PATH = ROOT / "extracted_data_final" / "job_descriptions_cleaned.json"
CHROMA_PATH = ROOT / "chroma_db"

client = chromadb.PersistentClient(path=str(CHROMA_PATH))
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5")

# THIS COLLECTION IS ONLY FOR JOB DESCRIPTIONS
collection = client.get_or_create_collection(
    name="job_descriptions",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

# Clear old JD data
existing = collection.get(include=[])["ids"]
if existing:
    logger.info(f"Clearing {len(existing)} old job description chunks...")
    collection.delete(ids=existing)

with open(JD_PATH, "r", encoding="utf-8") as f:
    jds = json.load(f)

docs, metas, ids = [], [], []
for idx, jd in enumerate(jds):
    title = jd.get("position_title", f"JD_{idx}")
    chunks = jd.get("structured_chunks", [])
    for c_idx, chunk in enumerate(chunks):
        if not chunk.strip(): 
            continue
        docs.append(str(chunk))
        metas.append({"position_title": title, "chunk_idx": c_idx})
        ids.append(f"jd_{idx}_{c_idx}_{title.replace(' ', '_')[:30]}")

collection.add(documents=docs, metadatas=metas, ids=ids)
logger.info(f"JOB DESCRIPTIONS EMBEDDED → job_descriptions: {len(docs)} chunks")
