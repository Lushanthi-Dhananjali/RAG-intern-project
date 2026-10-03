import os
import sys
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer

# =====================================================================
# PATH RESOLUTION & CLIENT INITIALIZATION
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "curriculum_syllabus"

# 1. Initialize Persistent ChromaDB Client
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# 2. Create or Load Collection with Cosine Space
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

# 3. Dense Embedder Model
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# =====================================================================
# STORAGE FUNCTION WITH METADATA BATCHING
# =====================================================================
def store_chunks_in_chromadb(chunks: List[Dict[str, Any]], batch_size: int = 64):
    """
    Takes a list of parsed curriculum chunk dictionaries and saves
    them into ChromaDB with structured metadata.
    """
    if not chunks:
        print("⚠️ No chunks provided to store.")
        return

    ids = []
    documents = []
    metadatas = []

    for item in chunks:
        ids.append(item["id"])
        documents.append(item["content"])

        # Ensure metadata values are flat (strings, ints, floats, bools)
        clean_metadata = {
            "source": str(item["metadata"].get("source", "TIG_Guide")),
            "grade_level": str(item["metadata"].get("grade_level", "Grade 8")),
            "subject": str(item["metadata"].get("subject", "Civic Education")),
            "competence": str(item["metadata"].get("competence", "Competency 8.0")),
            "competency_level": str(item["metadata"].get("competency_level", "8.1.1")),
            "periods": str(item["metadata"].get("periods", "01 Period")),
            "doc_type": str(item["metadata"].get("doc_type", "teacher_guide")),
            "category": str(item["metadata"].get("category", "target_curriculum"))
        }
        metadatas.append(clean_metadata)

    total_chunks = len(documents)
    print(f"📦 Generating embeddings & storing {total_chunks} chunks in ChromaDB...")

    # Upsert in batches to prevent memory bottlenecks
    for i in range(0, total_chunks, batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_docs = documents[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]

        # Generate vectors
        batch_embeddings = embedder.encode(batch_docs, show_progress_bar=False).tolist()

        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_docs,
            metadatas=batch_metas
        )
        print(f"  ↳ Indexed records {i + 1} to {min(i + batch_size, total_chunks)} of {total_chunks}...")

    print(f"✅ Finished! Total items currently stored in '{COLLECTION_NAME}': {collection.count()}")


# =====================================================================
# VERIFICATION / EXAMPLE RUN
# =====================================================================
if __name__ == "__main__":
    # Sample structured chunks matching NIE Grade 8 TIG format
    sample_parsed_chunks = [
        {
            "id": "civics_g8_tig_comp_8_1_1",
            "content": (
                "Competence: Competency 8.0: Explores democratic governance.\n"
                "Competency Level: 8.1.1: Identifies characteristics of direct democracy.\n"
                "Learning Outcomes: Differentiate direct democracy and representative democracy.\n"
                "Syllabus Content: Origin of democracy in ancient Athens, citizen participation.\n"
                "Suggested Activities: Small group debate on town hall assemblies."
            ),
            "metadata": {
                "source": "Grade_8_Civics_TIG.pdf",
                "grade_level": "Grade 8",
                "subject": "Civic Education",
                "competence": "Competency 8.0",
                "competency_level": "8.1.1",
                "periods": "01 Period (40 mins)",
                "doc_type": "teacher_guide",
                "category": "target_curriculum"
            }
        },
        {
            "id": "civics_g8_tig_comp_8_1_2",
            "content": (
                "Competence: Competency 8.0: Explores democratic governance.\n"
                "Competency Level: 8.1.2: Examines principles of representative democracy.\n"
                "Learning Outcomes: Explain the role of elections and voting rights.\n"
                "Syllabus Content: Universal franchise, parliamentary system in Sri Lanka.\n"
                "Suggested Activities: Mock election classroom role play."
            ),
            "metadata": {
                "source": "Grade_8_Civics_TIG.pdf",
                "grade_level": "Grade 8",
                "subject": "Civic Education",
                "competence": "Competency 8.0",
                "competency_level": "8.1.2",
                "periods": "02 Periods",
                "doc_type": "teacher_guide",
                "category": "target_curriculum"
            }
        }
    ]

    store_chunks_in_chromadb(sample_parsed_chunks)