import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document


class CurriculumDocumentParser:
    """
    Extracts and parses text from Teacher Instructional Guides (TIG)
    and Textbooks in PDF or DOCX format.
    """

    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """Extracts text page by page from a PDF file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        reader = PdfReader(file_path)
        extracted_pages = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                extracted_pages.append({
                    "source": os.path.basename(file_path),
                    "page_number": page_num,
                    "content": text
                })
        return extracted_pages

    @staticmethod
    def parse_docx(file_path: str) -> List[Dict[str, Any]]:
        """Extracts paragraphs and structured tables from a Word (.docx) file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = Document(file_path)
        full_text = []

        # Extract text from paragraphs
        for para in doc.paragraphs:
            clean_p = para.text.strip()
            if clean_p:
                full_text.append(clean_p)

        # Extract text from tables (often used in TIG competency matrices)
        for table in doc.tables:
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_data:
                    full_text.append(" | ".join(row_data))

        content = "\n".join(full_text)
        return [{
            "source": os.path.basename(file_path),
            "page_number": 1,
            "content": content
        }]

    @classmethod
    def load_document(cls, file_path: str) -> List[Dict[str, Any]]:
        """Automatically routes file based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls.parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")


# =====================================================================
# TIG COMPETENCY CHUNKER
# =====================================================================
class TIGCompetencyExtractor:
    """
    Identifies and chunks curriculum by official Competency Levels (e.g., 1.1, 1.2, 8.1.1).
    """

    @staticmethod
    def split_by_competency_levels(
            raw_pages: List[Dict[str, Any]],
            grade_level: str = "Grade 8",
            subject: str = "Civic Education",
            doc_type: str = "teacher_guide"
    ) -> List[Dict[str, Any]]:
        """
        Splits raw text streams into discrete competency level chunks.
        """
        combined_text = "\n\n".join([p["content"] for p in raw_pages])
        source_name = raw_pages[0]["source"] if raw_pages else "Unknown"

        # Regex to detect competency headers like "Competency 1.1", "Competency Level : 1.1", "1.1 - Topic"
        pattern = r"(Competency\s*(?:Level)?\s*[:\-]?\s*(\d+\.\d+(?:\.\d+)?))"

        splits = re.split(pattern, combined_text, flags=re.IGNORECASE)
        chunks = []

        # If regex finds matches, slice into competency chunks
        if len(splits) > 1:
            # splits structure: [preamble, match_header, level_num, content, match_header, level_num, content...]
            i = 1
            while i < len(splits):
                header = splits[i]
                comp_level = splits[i + 1]
                content = splits[i + 2].strip()

                chunk_text = f"{header}\n{content}"

                chunks.append({
                    "id": f"{source_name}_comp_{comp_level}",
                    "content": chunk_text,
                    "metadata": {
                        "source": source_name,
                        "grade_level": grade_level,
                        "subject": subject,
                        "competency_level": comp_level,
                        "doc_type": doc_type
                    }
                })
                i += 3
        else:
            # Fallback for standard paragraph/textbook chunking if no explicit competency pattern
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
            split_texts = text_splitter.split_text(combined_text)

            for idx, text in enumerate(split_texts):
                chunks.append({
                    "id": f"{source_name}_chunk_{idx}",
                    "content": text,
                    "metadata": {
                        "source": source_name,
                        "grade_level": grade_level,
                        "subject": subject,
                        "competency_level": "General",
                        "doc_type": doc_type
                    }
                })

        return chunks