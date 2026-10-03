import os
import sys

# Ensure root directory is on the path
sys.path.insert(0, os.path.abspath("."))

from app.services.multi_grade_retriever import MultiGradeBoundaryRetriever

retriever = MultiGradeBoundaryRetriever()

# Testing 8.1.2 retrieval specifically
data = retriever.retrieve_tig_and_textbook_for_level(
    competency_level="8.1.2",
    query="Institutions that provide public services",
    grade_level="Grade 8",
    subject="Civic Education"
)

guidelines = data.get("tig_guidelines", [])
print(f"Total TIG items retrieved for 8.1.2: {len(guidelines)}\n")

for i, item in enumerate(guidelines):
    print(f"==================== ITEM {i+1} ====================")
    print(item.get("content", "")[:500])
    print("\n")