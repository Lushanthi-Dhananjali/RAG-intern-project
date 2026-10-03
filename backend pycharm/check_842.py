import os
import sys
sys.path.insert(0, os.path.abspath("."))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("curriculum_syllabus")

# Check metadata matches for 8.4.2
res = coll.get(where={"competency_level": "8.4.2"})
print(f"Chunks with metadata '8.4.2': {len(res['ids'])}")

for i, doc in enumerate(res["documents"]):
    print(f"\n==================== CHUNK {i+1} ====================")
    print(doc[:400])