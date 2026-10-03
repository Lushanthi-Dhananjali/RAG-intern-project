from typing import Dict, List, Any
import chromadb


class CurriculumRetriever:
    def __init__(self, collection: chromadb.Collection):
        self.collection = collection

    def retrieve_exact_competency_guidance(
            self,
            grade: str,
            subject: str,
            competency_level: str,
            query: str = ""
    ) -> Dict[str, Any]:
        """
        Retrieves dedicated pedagogical sections and textbook grounding
        for a specific NIE competency level.
        """
        # Search query defaults to the competency tag if none provided
        search_prompt = query.strip() if query.strip() else f"Competency Level {competency_level}"

        # 1. Retrieve Pedagogical Guidance from Teacher Guide
        tig_filter = {
            "$and": [
                {"grade": grade},
                {"subject": subject},
                {"competency_level": competency_level},
                {"document_type": "Teacher Guide"}
            ]
        }

        tig_results = self.collection.query(
            query_texts=[f"learning outcomes instructional guidance activities {search_prompt}"],
            n_results=3,
            where=tig_filter
        )

        # 2. Retrieve Factual Content & Explanations from Textbook
        textbook_filter = {
            "$and": [
                {"grade": grade},
                {"subject": subject},
                {"competency_level": competency_level},
                {"document_type": "Textbook"}
            ]
        }

        textbook_results = self.collection.query(
            query_texts=[search_prompt],
            n_results=3,
            where=textbook_filter
        )

        tig_chunks = tig_results.get("documents", [[]])[0]
        textbook_chunks = textbook_results.get("documents", [[]])[0]

        # 3. Structure into separated semantic buckets
        return {
            "competency_level": competency_level,
            "grade": grade,
            "subject": subject,
            "teacher_guidance": tig_chunks,  # Learning outcomes & steps
            "subject_content": textbook_chunks,  # Factual material
            "raw_context_prompt": self._format_prompt_context(tig_chunks, textbook_chunks)
        }

    def _format_prompt_context(self, tig_chunks: List[str], textbook_chunks: List[str]) -> str:
        """Assembles prompt-ready context blocks with clear role labels."""
        context_parts = []

        if tig_chunks:
            context_parts.append(
                "--- OFFICIAL TEACHER INSTRUCTIONAL GUIDELINES & OUTCOMES ---\n" +
                "\n\n".join(tig_chunks)
            )

        if textbook_chunks:
            context_parts.append(
                "--- OFFICIAL TEXTBOOK SUBJECT MATTER ---\n" +
                "\n\n".join(textbook_chunks)
            )

        return "\n\n".join(context_parts)