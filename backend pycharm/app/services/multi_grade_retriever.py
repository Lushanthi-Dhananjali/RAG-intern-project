import os
from typing import Dict, List, Any
import chromadb


class MultiGradeBoundaryRetriever:
    """
    3-Tier Multi-Grade Boundary Retriever for ChromaDB.
    Isolates target grade competencies while retrieving prerequisite
    and upper boundary limits to strictly guide lesson plan generation.
    """

    def __init__(
            self,
            chroma_path: str = "./chroma_db",
            collection_name: str = "curriculum_syllabus"
    ):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _query_layer(
            self,
            query: str,
            n_results: int,
            where_clause: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Helper to run metadata-filtered vector queries and format output."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]

            extracted = []
            for doc, meta, doc_id in zip(docs, metas, ids):
                extracted.append({
                    "id": doc_id,
                    "content": doc,
                    "competency": meta.get("competency_level", "General"),
                    "source": meta.get("source_file", "unknown"),
                    "doc_type": meta.get("doc_type", "unknown"),
                    "grade_level": meta.get("grade_level", "unknown")
                })
            return extracted
        except Exception as e:
            print(f"⚠️ Retrieval layer warning ({where_clause}): {e}")
            return []

    def retrieve_3tier_boundaries(
            self,
            query: str,
            target_grade: str = "Grade 8",
            subject: str = "Civic Education"
    ) -> Dict[str, Any]:
        """
        Executes the 3-tier boundary search:
        - Tier 1: Target Grade (e.g., Grade 8 Core Competencies)
        - Tier 2: Lower Grade (e.g., Grade 7 Prerequisites)
        - Tier 3: Upper Grade (e.g., Grade 9 Upper Bounds)
        - Bonus Tier: Practical Exemplar Lesson Plans
        """
        # 1. Determine Grade Boundaries
        grade_num = int(target_grade.replace("Grade", "").strip()) if "Grade" in target_grade else 8
        lower_grade = f"Grade {grade_num - 1}"
        upper_grade = f"Grade {grade_num + 1}"

        # -------------------------------------------------------------
        # TIER 1: Target Grade Core Competencies & TIG Content (Primary)
        # -------------------------------------------------------------
        tier_1_target = self._query_layer(
            query=query,
            n_results=4,
            where_clause={
                "$and": [
                    {"grade_level": target_grade},
                    {"subject": subject}
                ]
            }
        )

        # -------------------------------------------------------------
        # TIER 2: Prerequisite Knowledge (Lower Grade Baseline)
        # -------------------------------------------------------------
        tier_2_prereq = self._query_layer(
            query=query,
            n_results=2,
            where_clause={
                "$and": [
                    {"grade_level": lower_grade},
                    {"subject": subject}
                ]
            }
        )

        # -------------------------------------------------------------
        # TIER 3: Upper Boundary Limits (Upper Grade Ceilings)
        # -------------------------------------------------------------
        tier_3_upper = self._query_layer(
            query=query,
            n_results=2,
            where_clause={
                "$and": [
                    {"grade_level": upper_grade},
                    {"subject": subject}
                ]
            }
        )

        # -------------------------------------------------------------
        # EXEMPLARS: Activity-Based Practical Lesson Formats
        # -------------------------------------------------------------
        exemplars = self._query_layer(
            query=query,
            n_results=1,
            where_clause={"category": "practical_exemplar"}
        )

        return {
            "query": query,
            "target_grade": target_grade,
            "tier_1_target_content": tier_1_target,
            "tier_2_prerequisites": tier_2_prereq,
            "tier_3_upper_boundaries": tier_3_upper,
            "practical_exemplars": exemplars
        }