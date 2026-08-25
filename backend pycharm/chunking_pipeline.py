import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize text splitter for sub-chunking long competency sections
sub_splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""]
)


def extract_raw_text(file_path: str) -> str:
    """Extracts raw text from PDF, DOCX, or TXT."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif ext in [".txt", ".json"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


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

    current_comp = "Foundational"
    for part in sections:
        part_clean = part.strip()
        if not part_clean:
            continue

        # Check if the part is the matched heading
        if re.match(pattern, part_clean, re.IGNORECASE):
            # Extract the numerical code, e.g., '1.1'
            comp_match = re.search(r'\d+\.\d+', part_clean)
            current_comp = comp_match.group(0) if comp_match else part_clean
        else:
            competency_blocks.append({
                "competency_level": current_comp,
                "text": part_clean
            })

    return competency_blocks


def process_and_chunk_document(
        file_path: str,
        grade_level: str,
        subject: str = "Civic Education",
        document_type: str = "teacher_guide"
) -> List[Dict[str, Any]]:
    """
    Extracts, splits by competency, creates sub-chunks, and tags metadata.
    """
    raw_text = extract_raw_text(file_path)
    if not raw_text.strip():
        return []

    competency_sections = split_by_competencies(raw_text)
    processed_chunks = []
    file_name = os.path.basename(file_path)

    for section in competency_sections:
        comp_level = section["competency_level"]
        sub_chunks = sub_splitter.split_text(section["text"])

        for idx, chunk_text in enumerate(sub_chunks):
            metadata = {
                "grade_level": grade_level,  # e.g., "Grade 8"
                "subject": subject,  # e.g., "Civic Education"
                "document_type": document_type,  # "teacher_guide", "textbook", "exemplar"
                "competency_level": comp_level,  # e.g., "1.1", "3.2", or "General"
                "source_file": file_name,
                "sub_chunk_index": idx + 1
            }

            processed_chunks.append({
                "text": chunk_text,
                "metadata": metadata,
                "id": f"{grade_level}_{os.path.splitext(file_name)[0]}_comp_{comp_level}_chunk_{idx + 1}"
            })

    return processed_chunks