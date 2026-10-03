import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
import chromadb
from sentence_transformers import SentenceTransformer

# =====================================================================
# PATH RESOLUTION & SETUP (ROBUST FOR app/scripts/)
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Moves up two directory levels: app/scripts/ -> app/ -> backend root
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
DATA_DIR = os.path.join(PROJECT_ROOT, "curriculum_data")
COLLECTION_NAME = "curriculum_syllabus"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# =====================================================================
# METADATA & PARSING HELPERS
# =====================================================================
def infer_metadata_from_path(file_path: Path) -> Dict[str, str]:
    """
    Infers grade, subject, and document type from directory path and filename.
    """
    path_str = str(file_path).lower().replace("\\", "/")
    filename = file_path.name.lower()

    # 1. Infer Grade Level (Grade 6 to 9)
    grade_match = re.search(r"grade[_\s\-]?([6-9])", path_str)
    grade = f"Grade {grade_match.group(1)}" if grade_match else "General"

    # 2. Infer Subject
    if "civic" in path_str:
        subject = "Civic Education"
    elif "science" in path_str:
        subject = "Science"
    else:
        subject = "General"

    # 3. Infer Document Type
    if "exemplar" in path_str or "sample" in filename:
        doc_type = "exemplar_lesson_plan"
    elif "teacher_guide" in filename or "tig" in filename:
        doc_type = "teacher_guide"
    elif "textbook" in filename or "tb" in filename:
        doc_type = "textbook"
    else:
        doc_type = "supplementary"

    return {
        "grade_level": grade,
        "subject": subject,
        "doc_type": doc_type,
        "source": file_path.name
    }


def extract_competency_tags(text: str) -> List[str]:
    """
    Extracts 2-digit and 3-digit competency levels:
    - Civic Education: e.g. 6.1.1, 7.2.1, 8.4.3, 9.2.1
    - Science: e.g. 1.1, 1.6, 1.7, 2.1, 14.2
    """
    pattern = re.compile(
        r"(?:Competency\s*level[\s;:]*|\bLevel[\s;:]*|\bCompetency[\s;:]*)?(\b\d{1,2}\s*[\.:]\s*\d+(?:\s*[\.:]\s*\d+)?\b)",
        re.IGNORECASE
    )
    raw_matches = pattern.findall(text)
    clean_levels = set()

    for m in raw_matches:
        normalized = re.sub(r"[\s:]+", ".", m)
        normalized = re.sub(r"\.+", ".", normalized).strip(".")
        parts = [p for p in normalized.split(".") if p.isdigit()]

        # Allow 2-digit (e.g. 1.6, 8.4) or 3-digit (e.g. 8.4.3)
        if len(parts) in (2, 3):
            major_num = int(parts[0])
            # Valid Sri Lankan curriculum competency ranges (1 to 20)
            if 1 <= major_num <= 20:
                clean_levels.add(".".join(parts))

    def safe_sort_key(level_str: str) -> List[int]:
        return [int(p) for p in level_str.split(".") if p.isdigit()]

    return sorted(list(clean_levels), key=safe_sort_key)


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 250) -> List[str]:
    """
    Sliding window chunker respecting natural paragraph breaks.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]

        last_nl = chunk.rfind("\n\n")
        if last_nl > max_chars * 0.5 and end < len(text):
            chunk = text[start:start + last_nl]
            start += last_nl + 2
        else:
            start += (max_chars - overlap)

        if chunk.strip():
            chunks.append(chunk.strip())

    return chunks


def extract_text_from_pdf(pdf_path: Path) -> List[Tuple[int, str]]:
    """
    Extracts text page-by-page using pypdf.
    """
    pages_data = []
    reader = PdfReader(str(pdf_path))
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages_data.append((idx, text))
    return pages_data


# =====================================================================
# MAIN INGESTION PIPELINE
# =====================================================================
def process_and_ingest_all():
    print("=" * 80)
    print("STARTING MULTI-GRADE, MULTI-SUBJECT CURRICULUM INGESTION")
    print(f"Data Directory: {DATA_DIR}")
    print(f"ChromaDB Path:  {CHROMA_PATH}")
    print("=" * 80)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    pdf_files = list(Path(DATA_DIR).rglob("*.pdf"))
    if not pdf_files:
        print(f"Error: No PDF files found in {DATA_DIR}!")
        return

    total_chunks_added = 0

    for file_path in pdf_files:
        meta_base = infer_metadata_from_path(file_path)
        print(f"\nProcessing: [{meta_base['subject']} | {meta_base['grade_level']} | {meta_base['doc_type']}] -> {file_path.name}")

        try:
            pages = extract_text_from_pdf(file_path)
        except Exception as e:
            print(f"  [ERROR] Failed to read {file_path.name}: {e}")
            continue

        file_docs = []
        file_metas = []
        file_ids = []

        current_active_level = "General"

        for page_num, page_text in pages:
            detected_levels = extract_competency_tags(page_text)

            three_digit = [lvl for lvl in detected_levels if len(lvl.split(".")) == 3]
            if three_digit:
                current_active_level = three_digit[0]
            elif detected_levels:
                current_active_level = detected_levels[0]

            chunks = chunk_text(page_text)

            for chunk_idx, chk in enumerate(chunks):
                chk_levels = extract_competency_tags(chk)
                chunk_3digit = [lvl for lvl in chk_levels if len(lvl.split(".")) == 3]
                assigned_level = chunk_3digit[0] if chunk_3digit else (chk_levels[0] if chk_levels else current_active_level)

                clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", file_path.stem)
                doc_id = f"{clean_name}_p{page_num}_comp_{assigned_level}_c{chunk_idx}"

                meta = {
                    "grade_level": meta_base["grade_level"],
                    "subject": meta_base["subject"],
                    "doc_type": meta_base["doc_type"],
                    "source": meta_base["source"],
                    "page_number": int(page_num),
                    "competency_level": str(assigned_level),
                    "has_learning_outcomes": bool("learning outcomes" in chk.lower() or "outcomes" in chk.lower()),
                    "has_syllabus_matrix": bool(
                        ("subject content" in chk.lower() or "content" in chk.lower())
                        and ("learning outcomes" in chk.lower() or "outcomes" in chk.lower())
                    )
                }

                file_docs.append(chk)
                file_metas.append(meta)
                file_ids.append(doc_id)

        BATCH_SIZE = 64
        for i in range(0, len(file_docs), BATCH_SIZE):
            b_docs = file_docs[i:i + BATCH_SIZE]
            b_metas = file_metas[i:i + BATCH_SIZE]
            b_ids = file_ids[i:i + BATCH_SIZE]
            b_embeddings = embedder.encode(b_docs).tolist()

            collection.upsert(
                ids=b_ids,
                documents=b_docs,
                metadatas=b_metas,
                embeddings=b_embeddings
            )

        total_chunks_added += len(file_docs)
        print(f"  -> Ingested {len(file_docs)} chunks from {len(pages)} pages.")

    print("\n" + "=" * 80)
    print(f"INGESTION COMPLETE! Total collection count: {collection.count()} chunks.")
    print("=" * 80)


if __name__ == "__main__":
    process_and_ingest_all()