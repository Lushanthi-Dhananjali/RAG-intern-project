import chromadb

# 1. Connect to your local ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="curriculum_syllabus",
    metadata={"hnsw:space": "cosine"}
)

# 2. Query only Grade 8 Civic Education Teacher Guides
query_text = "Protecting the environment and waste segregation"

results = collection.query(
    query_texts=[query_text],
    n_results=3,
    where={
        "$and": [
            {"grade_level": "Grade 8"},
            {"subject": "Civic Education"},
            {"document_type": "teacher_guide"}
        ]
    }
)

# 3. Print the retrieved chunks
print(f"\n🔍 Query: '{query_text}'")
print(f"Found {len(results.get('documents', [[]])[0])} matching chunks:\n" + "=" * 60)

for idx, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), start=1):
    print(f"\n[{idx}] File: {meta.get('source_file')} | Competency: {meta.get('competency_level')} | Category: {meta.get('category')}")
    print(f"Excerpt: {doc[:200]}...")