import os
import re
import uuid
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Initialize persistent ChromaDB storage
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PERSIST_DIRECTORY = os.path.join(BASE_DIR, "chroma_db")
DATA_DIRECTORY = os.path.join(BASE_DIR, "curriculum_data")

chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="curriculum_knowledge_base",
    embedding_function=embedding_fn
)

# Regex matching standard NIE competency codes (e.g., "8.1.1", "7.2.1")
COMPETENCY_HEADING_PATTERN = re.compile(
    r'(?:Competency\s+Level\s*[:\-\.]?\s*|\b)([6-9]\.\d+\.\d+)\b',
    re.IGNORECASE
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""]
)


def ingest_pdf_file(file_path: str, grade: str, subject: str, doc_type: str):
    print(f"\nProcessing [{grade} - {doc_type}]: {os.path.basename(file_path)}")
    try:
        reader = PdfReader(file_path)
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return

    documents = []
    metadatas = []
    ids = []

    # Default fallback competency based on Grade (e.g., "Grade 8" -> "8.1.1")
    grade_num = grade.replace("Grade ", "").strip()
    active_competency = f"{grade_num}.1.1" if grade_num.isdigit() else "general"

    for page_idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue

        # Look for competency level heading inside this page
        page_match = COMPETENCY_HEADING_PATTERN.search(page_text)
        if page_match:
            active_competency = page_match.group(1).strip()

        chunks = splitter.split_text(page_text)

        for chunk in chunks:
            chunk_match = COMPETENCY_HEADING_PATTERN.search(chunk)
            chunk_competency = chunk_match.group(1).strip() if chunk_match else active_competency

            documents.append(chunk)
            metadatas.append({
                "grade": grade,
                "subject": subject,
                "competency_level": chunk_competency,
                "document_type": doc_type,
                "source_file": os.path.basename(file_path),
                "page": page_idx + 1
            })
            ids.append(str(uuid.uuid4()))

    if documents:
        # ChromaDB batch limit safe insertion
        batch_size = 500
        for i in range(0, len(documents), batch_size):
            collection.add(
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size]
            )
        print(f" Successfully stored {len(documents)} chunks.")
    else:
        print(f"⚠️ No text could be extracted from: {os.path.basename(file_path)}")


def scan_and_ingest_all():
    if not os.path.exists(DATA_DIRECTORY):
        print(f"Error: Folder '{DATA_DIRECTORY}' does not exist.")
        return

    print(f"Scanning directory: {DATA_DIRECTORY}")

    for root, _, files in os.walk(DATA_DIRECTORY):
        for file in files:
            if not file.lower().endswith(".pdf"):
                continue

            file_path = os.path.join(root, file)
            folder_name = os.path.basename(root).lower()
            file_name = file.lower()

            # 1. Determine Grade
            if "grade_7" in folder_name or "grade_7" in file_name:
                grade = "Grade 7"
            elif "grade_8" in folder_name or "grade_8" in file_name:
                grade = "Grade 8"
            elif "grade_9" in folder_name or "grade_9" in file_name:
                grade = "Grade 9"
            else:
                grade = "General"

            # 2. Determine Document Type
            if "teacher_guide" in file_name or "tig" in file_name:
                doc_type = "Teacher Guide"
            elif "textbook" in file_name:
                doc_type = "Textbook"
            elif "lesson_plan" in file_name or "exemplar" in folder_name:
                doc_type = "Exemplar Plan"
            else:
                doc_type = "Reference"

            # 3. Ingest
            ingest_pdf_file(
                file_path=file_path,
                grade=grade,
                subject="Civic Education",
                doc_type=doc_type
            )

    print(f"\n All curriculum data ingested into ChromaDB! Total chunks: {collection.count()}")


if __name__ == "__main__":
    scan_and_ingest_all()