import os
from pathlib import Path
from ingestion import ingest_document
from extractor import extract_structured_lesson_plan
from vector_store import ChromaVectorStore

RAW_DATA_DIR = Path("./data/raw")


def build_custom_knowledge_base():
    """
    Reads all custom PDF/DOCX/TXT files in ./data/raw/
    and indexes them into ChromaDB as vector embeddings.
    """
    # 1. Initialize ChromaDB Vector Store
    db = ChromaVectorStore(embedding_provider="openai")

    # 2. Get all local files
    valid_extensions = [".pdf", ".docx", ".txt"]
    files = [f for f in RAW_DATA_DIR.iterdir() if f.suffix.lower() in valid_extensions]

    if not files:
        print(f"⚠️ No documents found in '{RAW_DATA_DIR}'. Add your Civic Education PDFs/DOCX files first!")
        return

    print(f"🚀 Found {len(files)} custom documents to index into Knowledge Base...\n")

    for idx, file_path in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Ingesting & Extracting: {file_path.name}")
        try:
            # Ingest raw document
            raw_text = ingest_document(str(file_path))

            # Extract structured schema via GPT-4
            plan_schema = extract_structured_lesson_plan(raw_text)

            # Index chunks directly into ChromaDB Vector Base
            db.chunk_and_index_lesson_plan(plan_schema, plan_id=f"kb_doc_{idx}")
            print(f"   └─ ✅ Successfully indexed into ChromaDB: '{plan_schema.title}'\n")

        except Exception as e:
            print(f"   └─ ❌ Error processing {file_path.name}: {e}\n")

    print("🎉 Knowledge Base update complete! ChromaDB is now loaded with your custom data.")


if __name__ == "__main__":
    build_custom_knowledge_base()