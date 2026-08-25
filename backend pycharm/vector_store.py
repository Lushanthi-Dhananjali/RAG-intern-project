import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from schema import LessonPlanSchema
from embeddings import EmbeddingPipeline


class ChromaVectorStore:
    """
    Persistent ChromaDB vector database manager for chunking, indexing,
    and retrieving lesson plans with explicit metadata filters.
    """

    def __init__(
            self,
            collection_name: str = "lesson_plans_db",
            persist_directory: str = "./chroma_db",
            embedding_provider: str = "openai"
    ):
        self.persist_directory = persist_directory

        # 1. Initialize Persistent ChromaDB Client
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # 2. Initialize Embedder
        self.embedder = EmbeddingPipeline(provider=embedding_provider)

        # 3. Get or Create Collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity metric
        )
        print(f"📦 ChromaDB Collection '{collection_name}' initialized at: {persist_directory}")

    def chunk_and_index_lesson_plan(self, plan: LessonPlanSchema, plan_id: Optional[str] = None) -> List[str]:
        """
        Splits a normalized LessonPlanSchema into logical sub-chunks
        (Objectives, Materials, Procedures) and indexes them into ChromaDB with metadata.
        """
        if not plan_id:
            plan_id = str(uuid.uuid4())

        # Base metadata dictionary shared across all segments of this plan
        base_metadata = {
            "plan_id": plan_id,
            "title": plan.title,
            "subject": plan.subject.lower().strip(),
            "grade_level": plan.grade_level.lower().strip(),
            "topic": plan.topic.lower().strip(),
            "standard_code": plan.educational_goal_or_standard.strip(),
            "duration_minutes": plan.estimated_duration_minutes
        }

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        doc_ids: List[str] = []

        # --- Segment 1: Objectives & Learning Outcomes ---
        outcomes_text = f"Title: {plan.title}\nEducational Goal: {plan.educational_goal_or_standard}\nLearning Outcomes:\n"
        outcomes_text += "\n".join([f"- {o.description}" for o in plan.learning_outcomes])

        documents.append(outcomes_text)
        meta_outcomes = base_metadata.copy()
        meta_outcomes["segment_type"] = "objectives"
        metadatas.append(meta_outcomes)
        doc_ids.append(f"{plan_id}_objectives")

        # --- Segment 2: Required Materials ---
        materials_text = f"Title: {plan.title}\nRequired Materials:\n"
        materials_text += "\n".join([f"- {m.item_name} (Qty: {m.quantity})" for m in plan.materials])

        documents.append(materials_text)
        meta_materials = base_metadata.copy()
        meta_materials["segment_type"] = "materials"
        metadatas.append(meta_materials)
        doc_ids.append(f"{plan_id}_materials")

        # --- Segment 3: Instructional Procedures ---
        for step in plan.procedures:
            step_text = (
                f"Title: {plan.title}\n"
                f"Phase: {step.phase_title} ({step.duration_minutes} min)\n"
                f"Teacher Action: {step.teacher_action}\n"
                f"Student Action: {step.student_action}"
            )
            documents.append(step_text)
            meta_step = base_metadata.copy()
            meta_step["segment_type"] = "procedure_step"
            meta_step["step_number"] = step.step_number
            metadatas.append(meta_step)
            doc_ids.append(f"{plan_id}_step_{step.step_number}")

        # --- Generate Embeddings ---
        embeddings = self.embedder.embed_documents(documents)

        # --- Add or Upsert into ChromaDB ---
        self.collection.upsert(
            ids=doc_ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(f"✅ Successfully indexed {len(documents)} segments for plan ID '{plan_id}'")
        return doc_ids

    def search_with_filters(
            self,
            query: str,
            subject: Optional[str] = None,
            grade_level: Optional[str] = None,
            segment_type: Optional[str] = None,
            n_results: int = 3
    ) -> Dict[str, Any]:
        """
        Performs vector similarity search with explicit metadata filtering.
        """
        # Build ChromaDB 'where' filter dictionary
        filter_conditions = []

        if subject:
            filter_conditions.append({"subject": {"$eq": subject.lower().strip()}})
        if grade_level:
            filter_conditions.append({"grade_level": {"$eq": grade_level.lower().strip()}})
        if segment_type:
            filter_conditions.append({"segment_type": {"$eq": segment_type.lower().strip()}})

        where_clause = None
        if len(filter_conditions) == 1:
            where_clause = filter_conditions[0]
        elif len(filter_conditions) > 1:
            where_clause = {"$and": filter_conditions}

        # Generate query vector
        query_vector = self.embedder.embed_query(query)

        # Execute filtered query
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where_clause
        )

        return results


# --- Demonstration Run ---
if __name__ == "__main__":
    from schema import LessonPlanSchema

    # 1. Initialize Vector Store
    db = ChromaVectorStore(embedding_provider="openai")

    # 2. Sample Plan
    sample_plan = LessonPlanSchema(
        title="Introduction to Photosynthesis",
        subject="Science",
        grade_level="Grade 8",
        topic="Plant Biology",
        educational_goal_or_standard="8.LS.1",
        estimated_duration_minutes=45,
        learning_outcomes=[
            {"id": 1, "description": "Identify sunlight, CO2, and water as chemical inputs.",
             "blooms_taxonomy_level": "Understand"}
        ],
        materials=[
            {"item_name": "Chloroplast diagram", "quantity": "1 per student", "is_digital": False}
        ],
        procedures=[
            {
                "step_number": 1,
                "phase_title": "Direct Instruction",
                "duration_minutes": 15,
                "teacher_action": "Explains chemical reaction formula on whiteboard.",
                "student_action": "Take notes in lab notebooks."
            }
        ],
        verification={
            "formative_assessment": "Exit ticket check.",
            "alignment_check": "Exit ticket evaluates chemical formula understanding."
        }
    )

    # 3. Index sample plan
    db.chunk_and_index_lesson_plan(sample_plan)

    # 4. Search with Explicit Metadata Filter
    print("\n🔍 Running Filtered Search for 'chloroplast diagram' (Filter: Grade 8 Science)...")
    search_results = db.search_with_filters(
        query="fundamental rights and duties of citizens",
        subject="civic education",  # <--- Set to Civic Education
        grade_level="grade 9",
        n_results=3
    )

    print("\n--- Search Results ---")
    for doc, meta in zip(search_results["documents"][0], search_results["metadatas"][0]):
        print(f"📍 Match Segment Type: {meta['segment_type']}")
        print(f"   Document Content: {doc[:100]}...\n")