import os
import re
from typing import List, Dict, Any
import chromadb
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# =====================================================================
# CONFIGURATION
# =====================================================================
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "curriculum_syllabus"
BASE_DATA_DIR = "./curriculum_data"
BATCH_SIZE = 100

# 1. Initialize Local Persistent ChromaDB Client
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

# 2. Text Splitter for sub-chunking
sub_splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""]
)


# =====================================================================
# TEXT EXTRACTION & NORMALIZATION
# =====================================================================

def clean_text(text: str) -> str:
    """Normalizes excessive whitespace and clean line breaks."""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from all readable pages of a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        extracted_pages = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)
        return "\n\n".join(extracted_pages)
    except Exception as e:
        print(f"❌ Error reading PDF {pdf_path}: {e}")
        return ""


def extract_text_from_docx(docx_path: str) -> str:
    """Extracts text from paragraphs and tables inside a Word (.docx) file."""
    try:
        doc = Document(docx_path)
        full_text = []

        # Extract standard paragraph text
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        # Extract structured content inside tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    unique_cells = list(dict.fromkeys(row_cells))
                    full_text.append(" | ".join(unique_cells))

        return "\n\n".join(full_text)
    except Exception as e:
        print(f"❌ Error reading DOCX {docx_path}: {e}")
        return ""


def extract_text_from_txt(txt_path: str) -> str:
    """Reads standard text / JSON raw files."""
    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading TXT {txt_path}: {e}")
        return ""


# =====================================================================
# COMPETENCY-AWARE CHUNKING PIPELINE
# =====================================================================

def split_by_competencies(raw_text: str) -> List[Dict[str, str]]:
    """
    Detects competency headings using regex pattern matching.
    Matches formats like: 'Competency 1.1', 'Competency Level 2.3', or '1.1 Competency'.
    """
    pattern = r'(Competency(?:\s+Level)?\s*[:\-]?\s*\d+\.\d+|\b\d+\.\d+\s+Competency)'
    sections = re.split(pattern, raw_text, flags=re.IGNORECASE)

    competency_blocks = []

    # Handle documents without explicit competency headings
    if len(sections) <= 1:
        return [{"competency_level": "General", "text": raw_text}]

    current_comp = "General"
    for part in sections:
        part_clean = part.strip()
        if not part_clean:
            continue

        # Check if the part is the matched competency heading
        if re.match(pattern, part_clean, re.IGNORECASE):
            comp_match = re.search(r'\d+\.\d+', part_clean)
            current_comp = comp_match.group(0) if comp_match else part_clean
        else:
            competency_blocks.append({
                "competency_level": current_comp,
                "text": part_clean
            })

    return competency_blocks


def process_document_to_chunks(
    file_path: str,
    grade_level: str,
    subject: str,
    doc_type: str,
    category: str,
    folder_name: str
) -> List[Dict[str, Any]]:
    """
    Reads a file, splits by competencies and sub-chunks, tagging with guaranteed unique IDs.
    """
    ext = os.path.splitext(file_path)[1].lower()
    raw_text = ""

    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        raw_text = extract_text_from_docx(file_path)
    elif ext in [".txt", ".json"]:
        raw_text = extract_text_from_txt(file_path)

    raw_text = clean_text(raw_text)
    if not raw_text:
        return []

    competency_sections = split_by_competencies(raw_text)
    file_name = os.path.basename(file_path)
    sanitized_file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(file_name)[0])

    document_chunks = []
    global_chunk_counter = 0

    for sec_idx, section in enumerate(competency_sections):
        comp_level = section["competency_level"]
        sub_chunks = sub_splitter.split_text(section["text"])

        for sub_idx, chunk_text in enumerate(sub_chunks):
            global_chunk_counter += 1
            # Unique ID prevents collisions on repeated competency headers
            chunk_id = f"{folder_name}_{sanitized_file_name}_sec{sec_idx}_comp_{comp_level}_chk_{global_chunk_counter}"

            metadata = {
                "grade_level": grade_level,
                "subject": subject,
                "doc_type": doc_type,
                "category": category,
                "competency_level": str(comp_level),
                "source_file": file_name,
                "chunk_index": global_chunk_counter
            }

            document_chunks.append({
                "text": chunk_text,
                "metadata": metadata,
                "id": chunk_id
            })

    return document_chunks


# =====================================================================
# MAIN INGESTION RUNNER
# =====================================================================

def run_full_ingestion(base_folder: str = BASE_DATA_DIR):
    """
    Traverses curriculum_data subdirectories, chunks texts,
    attaches multi-grade boundary metadata, and upserts into ChromaDB.
    """
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
        for sub in ["grade_7", "grade_8", "grade_9", "exemplars"]:
            os.makedirs(os.path.join(base_folder, sub), exist_ok=True)
        print(f"📁 Created '{base_folder}' folder structure. Place your PDF/Word documents inside and re-run.")
        return

    all_documents = []
    all_metadatas = []
    all_ids = []

    print("🚀 Starting Automated Ingestion Pipeline...\n" + "=" * 60)

    for folder_name in sorted(os.listdir(base_folder)):
        folder_path = os.path.join(base_folder, folder_name)
        if not os.path.isdir(folder_path):
            continue

        folder_lower = folder_name.lower()

        # 1. Multi-Grade Boundary Routing
        if "grade_7" in folder_lower or "grade 7" in folder_lower:
            grade_level = "Grade 7"
            category = "prerequisite_knowledge"
        elif "grade_8" in folder_lower or "grade 8" in folder_lower:
            grade_level = "Grade 8"
            category = "target_curriculum"
        elif "grade_9" in folder_lower or "grade 9" in folder_lower:
            grade_level = "Grade 9"
            category = "upper_boundary"
        elif "exemplar" in folder_lower or "sample" in folder_lower:
            grade_level = "Grade 8"
            category = "practical_exemplar"
        else:
            grade_level = "General"
            category = "reference"

        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isdir(file_path):
                continue

            file_lower = file_name.lower()

            # 2. Document Type Tagging
            if category == "practical_exemplar":
                doc_type = "exemplar_lesson_plan"
            elif any(k in file_lower for k in ["teacher", "tig", "guide"]):
                doc_type = "teacher_guide"
            else:
                doc_type = "textbook"

            print(f"📄 Processing: [{grade_level} | {category} | {doc_type}] -> {file_name}")

            chunks = process_document_to_chunks(
                file_path=file_path,
                grade_level=grade_level,
                subject="Civic Education",
                doc_type=doc_type,
                category=category,
                folder_name=folder_name
            )

            for item in chunks:
                all_documents.append(item["text"])
                all_metadatas.append(item["metadata"])
                all_ids.append(item["id"])

    # 3. Batch Upsert to ChromaDB
    total_docs = len(all_documents)
    if total_docs > 0:
        print("=" * 60)
        print(f"📦 Upserting {total_docs} chunks into ChromaDB in batches of {BATCH_SIZE}...")

        for i in range(0, total_docs, BATCH_SIZE):
            batch_docs = all_documents[i:i + BATCH_SIZE]
            batch_metas = all_metadatas[i:i + BATCH_SIZE]
            batch_ids = all_ids[i:i + BATCH_SIZE]

            collection.upsert(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"  ↳ Synced items {i + 1} to {min(i + BATCH_SIZE, total_docs)}...")

        print("\n" + "=" * 60)
        print("✅ Ingestion Complete!")
        print(f"📊 Total vectors currently indexed in '{COLLECTION_NAME}': {collection.count()}")
    else:
        print("\n⚠️ No valid documents (.pdf, .docx, .txt) were found in './curriculum_data/' subfolders.")


if __name__ == "__main__":
    run_full_ingestion()