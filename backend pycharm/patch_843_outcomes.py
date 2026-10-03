import os
import sys
sys.path.insert(0, os.path.abspath("."))
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("curriculum_syllabus")

res = coll.get(where={"competency_level": "8.4.3"})

target_doc_id = None
target_doc = None
target_meta = None

# Locate the 8.4.3 outcomes chunk
for doc_id, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
    if "Learning Outcomes" in doc and "Manages the disasters" in doc:
        target_doc_id = doc_id
        target_doc = doc
        target_meta = meta
        break

if target_doc_id:
    # Full official 6-outcome specification from the master NIE syllabus grid
    official_843_text = """Competency Level : 8.4.3
Manages the disasters.
No. of Periods : 01
Learning Outcomes :
• Explains the importance of being alert about the situations where accidents and disasters might happen.
• Suggests suitable preventive measures for accidents and disasters.
• Explains the importance of safeguarding from accidents other than situational ones by identifying those situations.
• Explains with examples that bad habits cause for accidents and disasters.
• Identifies accidents caused by food and drugs highlights the importance of protection.
• Expresses the importance of getting rid of bad habits for the prevention of accidents and disasters.

Instructions for Lesson Planning:
(Plan the lesson in order to cover the content)"""

    coll.update(
        ids=[target_doc_id],
        documents=[official_843_text],
        metadatas=[target_meta]
    )
    print(f"Successfully updated chunk [{target_doc_id}] with all 6 official learning outcomes.")
else:
    print("Chunk for 8.4.3 not found.")