import os
import sys
sys.path.insert(0, os.path.abspath("."))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("curriculum_syllabus")

# Retrieve all teacher guide documents
res = coll.get(where={"doc_type": "teacher_guide"})

print(f"Total TIG documents inspected: {len(res['ids'])}\n")

matches = []
for doc_id, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
    if "8.4.2" in doc:
        matches.append((doc_id, meta.get("competency_level"), doc[:300]))

print(f"Found {len(matches)} chunks containing '8.4.2' in body text:\n")
for doc_id, tag, preview in matches:
    print(f"ID: {doc_id} | Tagged As: [{tag}]")
    print(f"Preview: {repr(preview)}\n" + "-"*50)