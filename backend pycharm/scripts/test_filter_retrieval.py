import os
import chromadb
from chromadb.utils import embedding_functions

# Connect to persisted database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
client = chromadb.PersistentClient(path=DB_PATH)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_collection("curriculum_knowledge_base", embedding_function=embedding_fn)

# Input parameters
grade_input = "Grade 8"
subject_input = "Civic Education"
competency_input = "8.1.1"
user_query = "What are the core characteristics of democratic governance?"

# Query with where filter
results = collection.query(
    query_texts=[user_query],
    n_results=3,
    where={
        "$and": [
            {"grade": grade_input},
            {"subject": subject_input},
            {"competency_level": competency_input}
        ]
    }
)

docs = results["documents"][0]
metas = results["metadatas"][0]

print(f"Retrieved {len(docs)} matching chunks for Competency {competency_input}:\n")
for i, (doc, meta) in enumerate(zip(docs, metas)):
    print(f"--- Result {i + 1} [{meta.get('document_type', 'Doc')}] (Page {meta.get('page')}) ---")
    print(f"{doc[:250]}...\n")