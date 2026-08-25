import chromadb

try:
    client = chromadb.PersistentClient(path="./chroma_db")
    existing_collections = [c.name for c in client.list_collections()]

    if "curriculum_syllabus" in existing_collections:
        client.delete_collection("curriculum_syllabus")
        print("🗑️ Successfully deleted collection 'curriculum_syllabus'.")
    else:
        print("ℹ️ Collection 'curriculum_syllabus' does not exist or was already deleted.")
except Exception as e:
    print(f"Error resetting collection: {e}")