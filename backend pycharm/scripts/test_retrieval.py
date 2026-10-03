import os
import chromadb
from chromadb.utils import embedding_functions

# Resolves relative path to the chroma_db folder accurately
CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name="curriculum_knowledge_base", embedding_function=embedding_fn)

results = collection.query(
    query_texts=["direct democracy features"],
    n_results=3,
    where={
        "$and": [
            {"grade": "Grade 8"},
            {"competency_level": "8.1.1"}
        ]
    }
)

print("\n--- Retrieved Documents ---")
for idx, doc in enumerate(results["documents"][0]):
    print(f"\n[Chunk {idx + 1}]:\n{doc}")