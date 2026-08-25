import os
from pathlib import Path
from pypdf import PdfReader
import docx
import trafilatura


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from PDF files."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()


def extract_text_from_docx(docx_path: str) -> str:
    """Extracts text from Word documents."""
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def extract_text_from_url(url: str) -> str:
    """Fetches and extracts clean body text from a webpage URL."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Failed to fetch web content from URL: {url}")

    # Extract main content and ignore ads, navbars, and boilerplate HTML
    text = trafilatura.extract(downloaded)
    if not text:
        raise ValueError(f"Could not extract meaningful body text from: {url}")

    return text.strip()


def ingest_document(source: str) -> str:
    """
    Universal ingestion interface.
    Accepts local file paths (.pdf, .docx, .txt) OR web URLs (http/https).
    """
    # 1. Handle Web URLs
    if source.startswith("http://") or source.startswith("https://"):
        print(f"🌐 Ingesting web content from: {source}")
        return extract_text_from_url(source)

    # 2. Handle Local Files
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")

    ext = path.suffix.lower()
    print(f"📄 Ingesting local file [{ext}]: {source}")

    if ext == ".pdf":
        return extract_text_from_pdf(source)
    elif ext == ".docx":
        return extract_text_from_docx(source)
    elif ext == ".txt":
        with open(source, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")


# --- Test Web & Local Ingestion ---
if __name__ == "__main__":
    # Test Web Scraping:
    test_url = "https://en.wikipedia.org/wiki/Lesson_plan"
    try:
        scraped_text = ingest_document(test_url)
        print(f"✅ Web Scraping Success! Extracted {len(scraped_text)} characters.")
        print(f"Sample snippet: {scraped_text[:200]}...\n")
    except Exception as e:
        print(f"❌ Scraping error: {e}")