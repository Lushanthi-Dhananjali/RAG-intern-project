import os
import sys
import re
from typing import List, Dict, Any, Tuple
import chromadb
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
DATA_FOLDER = os.path.join(PROJECT_ROOT, "curriculum_data")
COLLECTION_NAME = "curriculum_syllabus"
BATCH_SIZE = 64

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

sub_splitter = RecursiveCharacterTextSplitter(
    chunk_size=750,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""]
)


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            return "\n\n".join([p.extract_text() or "" for p in reader.pages])
        except Exception as e:
            print(f"❌ PDF read error: {e}")
            return ""
    elif ext in [".docx", ".doc"]:
        try:
            doc = Document(file_path)
            full_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        full_text.append(" | ".join(list(dict.fromkeys(cells))))
            return "\n\n".join(full_text)
        except Exception as e:
            print(f"❌ DOCX read error: {e}")
            return ""
    elif ext in [".txt", ".json"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def run_full_ingestion():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        for sub in ["grade_7", "grade_8", "grade_9", "exemplars"]:
            os.makedirs(os.path.join(DATA_FOLDER, sub), exist_ok=True)
        print(f"📁 Created '{DATA_FOLDER}' folder structure. Add your files and re-run.")
        return

    all_files = []
    for root, _, filenames in os.walk(DATA_FOLDER):
        for f in filenames:
            if f.lower().endswith((".pdf", ".docx", ".doc", ".txt")):
                all_files.append(os.path.join(root, f))

    if not all_files:
        print(f"⚠️ No files found in '{DATA_FOLDER}'.")
        return

    print("🚀 Starting Automated Ingestion Pipeline...\n" + "=" * 70)

    all_ids, all_documents, all_metadatas = [], [], []

    for file_path in all_files:
        file_name = os.path.basename(file_path)
        path_lower = file_path.lower()

        # Metadata Categorization
        if "exemplar" in path_lower or "sample" in path_lower:
            grade_level = "Grade 8"
            doc_type = "exemplar_lesson_plan"
            category = "practical_exemplar"
        elif "grade_7" in path_lower or "grade 7" in path_lower:
            grade_level = "Grade 7"
            doc_type = "teacher_guide" if "guide" in path_lower or "tig" in path_lower else "textbook"
            category = "prerequisite_knowledge"
        elif "grade_9" in path_lower or "grade 9" in path_lower:
            grade_level = "Grade 9"
            doc_type = "teacher_guide" if "guide" in path_lower or "tig" in path_lower else "textbook"
            category = "upper_boundary"
        else:
            grade_level = "Grade 8"
            doc_type = "teacher_guide" if "guide" in path_lower or "tig" in path_lower else "textbook"
            category = "target_curriculum"

        print(f"📄 Processing: [{grade_level} | {doc_type}] -> {file_name}")

        raw_text = extract_text_from_file(file_path)
        if not raw_text.strip():
            continue

        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", os.path.splitext(file_name)[0])

        # If it's a sample lesson plan, store it as full exemplar chunks
        if doc_type == "exemplar_lesson_plan":
            chunks = sub_splitter.split_text(raw_text)
            for idx, chk in enumerate(chunks, 1):
                chunk_id = f"exemplar_{sanitized_name}_{idx}"
                all_ids.append(chunk_id)
                all_documents.append(chk)
                all_metadatas.append({
                    "source": file_name,
                    "grade_level": grade_level,
                    "subject": "Civic Education",
                    "doc_type": "exemplar_lesson_plan",
                    "category": "practical_exemplar",
                    "competency_level": "Exemplar"
                })
        else:
            # Standard competency level chunking
            comp_pattern = r"(?:Competenc(?:e|y)\s*Level\s*[:\-]?\s*|\bLevel\s*[:\-]?\s*)(\d+\.\d+(?:\.\d+)?)"
            sections = re.split(comp_pattern, raw_text, flags=re.IGNORECASE)

            if len(sections) > 1:
                i = 1
                while i < len(sections):
                    comp_lvl = sections[i].strip()
                    sec_body = sections[i + 1].strip()
                    sub_chunks = sub_splitter.split_text(sec_body)
                    for idx, chk in enumerate(sub_chunks, 1):
                        all_ids.append(f"{sanitized_name}_comp_{comp_lvl.replace('.', '_')}_{idx}")
                        all_documents.append(chk)
                        all_metadatas.append({
                            "source": file_name,
                            "grade_level": grade_level,
                            "subject": "Civic Education",
                            "doc_type": doc_type,
                            "category": category,
                            "competency_level": comp_lvl
                        })
                    i += 2
            else:
                chunks = sub_splitter.split_text(raw_text)
                for idx, chk in enumerate(chunks, 1):
                    all_ids.append(f"{sanitized_name}_gen_{idx}")
                    all_documents.append(chk)
                    all_metadatas.append({
                        "source": file_name,
                        "grade_level": grade_level,
                        "subject": "Civic Education",
                        "doc_type": doc_type,
                        "category": category,
                        "competency_level": "General"
                    })

    if all_documents:
        print(f"\n📦 Upserting {len(all_documents)} chunks into ChromaDB...")
        for i in range(0, len(all_documents), BATCH_SIZE):
            b_ids = all_ids[i:i + BATCH_SIZE]
            b_docs = all_documents[i:i + BATCH_SIZE]
            b_metas = all_metadatas[i:i + BATCH_SIZE]
            b_embs = embedder.encode(b_docs, show_progress_bar=False).tolist()

            collection.upsert(ids=b_ids, embeddings=b_embs, documents=b_docs, metadatas=b_metas)
        print(f"✅ Ingestion Complete! Total indexed vectors: {collection.count()}")


if __name__ == "__main__":
    run_full_ingestion()