import os
import sys
sys.path.insert(0, os.path.abspath("."))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("curriculum_syllabus")

# Retrieve all teacher guide documents
res = coll.get(where={"doc_type": "teacher_guide"})

patched = 0
for doc_id, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
    # Look for the chunk that introduces Competency Level 8.1.2
    if "8.1.2" in doc and "Names the public services provided for the area" in doc:
        meta["competency_level"] = "8.1.2"
        coll.update(
            ids=[doc_id],
            documents=[doc],
            metadatas=[meta]
        )
        print(f"Updated chunk [{doc_id}] -> set competency_level = '8.1.2'")
        patched += 1

print(f"\nSuccessfully patched {patched} chunks for 8.1.2 in ChromaDB.")