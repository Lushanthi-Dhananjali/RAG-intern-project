import os
import sys

# Ensure the project root directory is always in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the 3-Tier MultiGradeBoundaryRetriever
try:
    from app.services.multi_grade_retriever import MultiGradeBoundaryRetriever
except ModuleNotFoundError:
    try:
        from services.multi_grade_retriever import MultiGradeBoundaryRetriever
    except ModuleNotFoundError:
        from multi_grade_retriever import MultiGradeBoundaryRetriever

# -------------------------------------------------------------
# Configuration & Initialization
# -------------------------------------------------------------
# Point dynamically to the chroma_db folder relative to project root
CHROMA_STORAGE_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

retriever = MultiGradeBoundaryRetriever(chroma_path=CHROMA_STORAGE_PATH)

query_topic = "Protecting the environment: waste segregation, tree planting, and water preservation"
target_grade = "Grade 8"
subject = "Civic Education"

# -------------------------------------------------------------
# Run 3-Tier Boundary Retrieval
# -------------------------------------------------------------
results = retriever.retrieve_3tier_boundaries(
    query=query_topic,
    target_grade=target_grade,
    subject=subject
)

print("\n" + "=" * 80)
print(f"🔍 3-TIER RETRIEVAL TEST FOR: {results.get('query', query_topic)}")
print(f"📚 Subject: {subject} | Target: {target_grade}")
print("=" * 80)

# TIER 1: Target Grade Content
tier1_docs = results.get("tier_1_target_content", [])
print(f"\n🎯 [TIER 1 - Target Content ({target_grade})]: {len(tier1_docs)} distinct chunks found")
for idx, item in enumerate(tier1_docs, 1):
    preview = item.get("content", "")[:120].replace("\n", " ")
    print(f"  [{idx}] ID: {item.get('id', 'N/A')}")
    print(f"      Source: {item.get('source', 'Unknown')} | Type: {item.get('doc_type', 'N/A')} | Comp: {item.get('competency', 'General')}")
    print(f"      Text: \"{preview}...\"\n")

# TIER 2: Lower Grade Prerequisites
tier2_docs = results.get("tier_2_prerequisites", [])
print(f"🧱 [TIER 2 - Prerequisite Baseline (Grade 7)]: {len(tier2_docs)} distinct chunks found")
for idx, item in enumerate(tier2_docs, 1):
    preview = item.get("content", "")[:120].replace("\n", " ")
    print(f"  [{idx}] ID: {item.get('id', 'N/A')}")
    print(f"      Source: {item.get('source', 'Unknown')} | Comp: {item.get('competency', 'General')}")
    print(f"      Text: \"{preview}...\"\n")

# TIER 3: Upper Grade Boundary Limits
tier3_docs = results.get("tier_3_upper_boundaries", [])
print(f"🚫 [TIER 3 - Upper Boundary Limits (Grade 9)]: {len(tier3_docs)} distinct chunks found")
for idx, item in enumerate(tier3_docs, 1):
    preview = item.get("content", "")[:120].replace("\n", " ")
    print(f"  [{idx}] ID: {item.get('id', 'N/A')}")
    print(f"      Source: {item.get('source', 'Unknown')} | Comp: {item.get('competency', 'General')}")
    print(f"      Text: \"{preview}...\"\n")

# EXEMPLARS: Activity-Based Practical Lesson Formats
exemplar_docs = results.get("practical_exemplars", [])
print(f"🌱 [EXEMPLARS - Practical Activities]: {len(exemplar_docs)} chunks found")
for idx, item in enumerate(exemplar_docs, 1):
    preview = item.get("content", "")[:120].replace("\n", " ")
    print(f"  [{idx}] ID: {item.get('id', 'N/A')}")
    print(f"      Source: {item.get('source', 'Unknown')} | Type: {item.get('doc_type', 'exemplar_lesson_plan')}")
    print(f"      Text: \"{preview}...\"\n")