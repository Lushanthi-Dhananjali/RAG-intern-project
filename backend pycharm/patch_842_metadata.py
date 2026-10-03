import os
import sys
sys.path.insert(0, os.path.abspath("."))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("curriculum_syllabus")

target_chunk_ids = [
    "grade_8_grade_8_civic_teacher_guide_sec23_comp_8.4_chk_185",
    "grade_8_civic_teacher_guide_sec23_comp_8.4.1_chk_185"
]

res = coll.get(ids=target_chunk_ids)

for doc_id, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
    meta["competency_level"] = "8.4.2"
    coll.update(
        ids=[doc_id],
        documents=[doc],
        metadatas=[meta]
    )
    print(f"Patched [{doc_id}] -> competency_level = '8.4.2'")

print("\nSuccessfully updated 8.4.2 syllabus table metadata.")