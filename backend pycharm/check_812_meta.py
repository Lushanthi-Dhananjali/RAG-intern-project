import os
import sys
sys.path.insert(0, os.path.abspath("."))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("curriculum_syllabus")

# Check if ANY chunk has competency_level == 8.1.2
exact = coll.get(where={"competency_level": "8.1.2"})
print(f"Chunks with exact metadata '8.1.2': {len(exact['ids'])}")

# Search for the text "8.1.2" inside document bodies
all_docs = coll.get(where={"doc_type": "teacher_guide"})
matching_docs = []
for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
    if "8.1.2" in doc:
        matching_docs.append((meta.get("competency_level"), doc[:200]))

print(f"\nChunks containing '8.1.2' in body text: {len(matching_docs)}")
for comp, preview in matching_docs:
    print(f"Metadata Tag: [{comp}] -> Text: {repr(preview)}")