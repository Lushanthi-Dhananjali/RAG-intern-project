import os
import sys
import re
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "curriculum_syllabus"


# =====================================================================
# CONTENT ISOLATION & HYBRID VERBATIM TIG EXTRACTION HELPERS
# =====================================================================
def clean_bullet(text: str) -> str:
    """
    Cleans up whitespaces, strips symbols, removes parenthetical teacher notes,
    and trims to a proper sentence.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"^[\u2022\u2023\u25E6\u2043\u2219\*\-\–\—\d+\.]\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*\([^)]*plan the lesson[^)]*\)", "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned and not cleaned.endswith((".", ";")):
        cleaned += "."
    return cleaned


def isolate_target_competency_content(raw_text: str, target_level: str) -> str:
    """
    Safely isolates target competency content. If isolation fails or truncates,
    returns raw_text so data is never dropped.
    """
    if not raw_text or not target_level:
        return raw_text

    target_level = target_level.strip()
    pattern = rf"(?:Competency\s*Level|Level|Competency)[\s:]*{re.escape(target_level)}\b"
    match = re.search(pattern, raw_text, re.IGNORECASE)
    if not match:
        return raw_text

    start_idx = match.start()
    next_level_pattern = re.compile(
        r"(?:Competency\s*Level|Level)[\s:]*([0-9]{1,2}(?:\.[0-9]+){1,2})",
        re.IGNORECASE
    )

    end_idx = None
    for m in next_level_pattern.finditer(raw_text[start_idx + len(match.group(0)):]):
        if m.group(1).strip() != target_level:
            end_idx = start_idx + len(match.group(0)) + m.start()
            break

    if end_idx:
        isolated = raw_text[start_idx:end_idx].strip()
        return isolated if len(isolated) > 50 else raw_text

    return raw_text[start_idx:].strip()


def extract_verbatim_tig_outcomes(tig_text: str, target_level: str = "") -> List[str]:
    """
    Hybrid extractor: Extracts outcomes structurally using both bullet patterns
    and comprehensive multi-subject Bloom's action verbs.
    Robust against generic stop-word collisions in multi-page NIE tables.
    """
    if not tig_text or len(tig_text.strip()) < 15:
        return []

    # Comprehensive verb list covering both Civic Education & Science (Bloom's Taxonomy)
    EXPANDED_ACTION_VERBS = (
        # Civic & General
        "identifies", "explains", "investigates", "presents", "names", "describes",
        "lists", "suggests", "demonstrates", "analyses", "analyzes", "evaluates",
        "compares", "gives", "expresses", "appreciates", "classifies", "defines",
        "distinguishes", "shows", "builds", "prepares", "states", "emphasises",
        "emphasizes", "emphasize", "accepts", "values",
        # Science Specific
        "calculates", "designs", "measures", "tabulates", "hypothesizes", "draws",
        "labels", "observes", "records", "differentiates", "synthesizes", "determines",
        "conducts", "constructs", "illustrates", "infers", "predicts", "verifies"
    )

    lines = [l.strip() for l in re.split(r"[\n\r]+", tig_text) if l.strip()]
    outcomes: List[str] = []
    current_bullet = ""
    in_outcomes_zone = False

    # Strictly matched column boundaries to prevent premature exits
    STRICT_STOP_PATTERNS = [
        r"^subject\s+content\b",
        r"^learning[\s\-]+teaching[\s\-]+process\b",
        r"^teaching[\s\-]+learning[\s\-]+process\b",
        r"^proposed\s+instructions\b",
        r"^no\.?\s*of\s*periods\b",
        r"^criteria\s+for\s+evaluation\b",
        r"^assessment\s+and\s+evaluation\b",
        r"^instructions\s+for\s+lesson\s+planning\b",
        r"^activity\s*(?:[\d\.\:]|\bplan\b)",
        r"^competency\s+level\s*:\s*(?!8\.1\.3|8\.4\.3|8\.4\.1|8\.4\.2|8\.2\.1)"
    ]

    BULLET_MARKER = re.compile(r"^[\u2022\u2023\u25E6\u2043\u2219\*\-\–\—\d+\.]\s*")

    for line in lines:
        lower_line = line.lower()

        # 1. Start strictly when finding 'Learning Outcomes' table header
        if re.search(r"\b(?:learning\s+outcomes|outcomes)\b", lower_line) and not in_outcomes_zone:
            in_outcomes_zone = True
            continue

        # 2. Stop ONLY if an actual new column header or next section begins
        if in_outcomes_zone:
            if any(re.search(pat, lower_line) for pat in STRICT_STOP_PATTERNS):
                if current_bullet:
                    outcomes.append(clean_bullet(current_bullet))
                    current_bullet = ""
                in_outcomes_zone = False
                break

        # 3. Collect entries inside outcomes zone
        if in_outcomes_zone:
            clean_line = BULLET_MARKER.sub("", line).strip()
            lower_clean = clean_line.lower()

            # Skip common teacher pedagogical prompts
            if lower_clean.startswith(("give an opportunity", "instruct students", "guide students", "direct the students")):
                continue

            has_bullet = bool(BULLET_MARKER.match(line))
            starts_with_verb = any(re.match(rf"^{v}\b", lower_clean) for v in EXPANDED_ACTION_VERBS)

            if has_bullet or starts_with_verb:
                if current_bullet:
                    outcomes.append(clean_bullet(current_bullet))
                current_bullet = clean_line
            else:
                # Multi-line wrapped bullet continuation
                if current_bullet and not line.endswith(":"):
                    current_bullet += f" {clean_line}"

    if current_bullet:
        outcomes.append(clean_bullet(current_bullet))

    # 4. Filter headlines and empty strings
    valid = []
    for o in outcomes:
        c = clean_bullet(o)
        c_low = c.lower()

        is_competency_headline = (
            "contributes to minimize them" in c_low or
            "for the betterment of" in c_low or
            "makes use of" in c_low or
            "investigates the need and importance" in c_low or
            c_low.startswith("competency")
        )
        is_truncated = c_low.endswith(("of.", "in.", "for.", "to.", "and.", "with."))

        if len(c) >= 12 and not is_competency_headline and not is_truncated:
            valid.append(c)

    return valid

# Maintain alias for backward compatibility
extract_outcomes_structurally = extract_verbatim_tig_outcomes


# =====================================================================
# MULTI-GRADE BOUNDARY & COMPETENCY RETRIEVER
# =====================================================================
class MultiGradeBoundaryRetriever:
    """
    Retrieves curriculum chunks from ChromaDB across Grades 6-9 for both
    Civic Education and Science with dynamic fallback and structural table prioritization.
    """

    def __init__(self, chroma_path: Optional[str] = None):
        db_path = chroma_path or CHROMA_PATH
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def retrieve_exemplar_lesson_plan(self, subject: str = "Civic Education") -> str:
        results = self.collection.get(
            where={"doc_type": "exemplar_lesson_plan"},
            limit=5
        )
        if results.get("documents"):
            return "\n\n".join(results["documents"])
        return "Standard University of Peradeniya Lesson Plan Structure"

    def auto_extract_unit_competency_levels(
        self,
        unit_name_or_query: str,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education"
    ) -> List[str]:
        query_vector = self.embedder.encode(unit_name_or_query).tolist()

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=35,
            where={
                "$and": [
                    {"grade_level": grade_level.strip()},
                    {"subject": subject.strip()},
                    {"doc_type": "teacher_guide"}
                ]
            }
        )

        detected_levels = set()

        if results.get("metadatas") and results["metadatas"][0]:
            for meta in results["metadatas"][0]:
                comp_lvl = str(meta.get("competency_level", "")).strip()
                if re.match(r"^\d{1,2}\.[0-9]+(\.[0-9]+)?$", comp_lvl):
                    detected_levels.add(comp_lvl)

        sorted_levels = sorted(
            list(detected_levels),
            key=lambda x: [int(num) for num in x.split(".") if num.isdigit()]
        )

        return sorted_levels

    def retrieve_tig_and_textbook_for_level(
        self,
        competency_level: str,
        query: str,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education"
    ) -> Dict[str, Any]:
        target_level = competency_level.strip()
        clean_grade = grade_level.strip()
        clean_subject = subject.strip()

        # 1. Fetch exact competency level metadata matches
        direct_res = self.collection.get(
            where={
                "$and": [
                    {"grade_level": clean_grade},
                    {"subject": clean_subject},
                    {"competency_level": target_level},
                    {"doc_type": "teacher_guide"}
                ]
            },
            limit=10
        )
        matching_docs = direct_res.get("documents", []) or []
        matching_metas = direct_res.get("metadatas", []) or []

        # 2. Candidate teacher guide chunks query
        if not matching_docs:
            tig_res = self.collection.get(
                where={
                    "$and": [
                        {"grade_level": clean_grade},
                        {"subject": clean_subject},
                        {"doc_type": "teacher_guide"}
                    ]
                },
                limit=150
            )
            all_docs = tig_res.get("documents", []) or []
            all_metas = tig_res.get("metadatas", []) or []

            target_pattern = re.compile(rf"\b{re.escape(target_level)}\b")

            for d, m in zip(all_docs, all_metas):
                d_lower = d.lower()
                if any(bad in d_lower for bad in ["school term", "term 1", "term 2", "term 3", "competency levels"]):
                    continue
                if len(d.strip()) < 40:
                    continue

                meta_comp = str(m.get("competency_level", "")).strip()
                if meta_comp == target_level or target_pattern.search(d):
                    matching_docs.append(d)
                    matching_metas.append(m)

        # 3. Dynamic semantic table fallback if matrix table is missing
        has_real_table = any(
            ("learning outcomes" in d.lower() or "outcomes" in d.lower())
            for d in matching_docs
        )

        if not has_real_table:
            table_query = f"{clean_grade} {clean_subject} Competency Level {target_level} Learning Outcomes"
            query_vector = self.embedder.encode(table_query).tolist()

            sem_res = self.collection.query(
                query_embeddings=[query_vector],
                n_results=5,
                where={
                    "$and": [
                        {"grade_level": clean_grade},
                        {"subject": clean_subject},
                        {"doc_type": "teacher_guide"}
                    ]
                }
            )
            sem_docs = sem_res.get("documents", [[]])[0]
            sem_metas = sem_res.get("metadatas", [[]])[0]

            for d, m in zip(sem_docs, sem_metas):
                d_lower = d.lower()
                if "school term" in d_lower or len(d.strip()) < 40:
                    continue
                if d not in matching_docs:
                    matching_docs.append(d)
                    matching_metas.append(m)

        # 4. Strict Structural Prioritization: Put the chunk with exact competency target and matrix layout at Index 0
        exact_matrix_docs = []
        syllabus_matrix_docs = []
        other_docs = []

        for doc, meta in zip(matching_docs, matching_metas):
            d_lower = doc.lower()
            if any(term in d_lower for term in ["criteria for evaluation:", "annex 01", "task sheet:"]):
                continue

            meta_lvl = str(meta.get("competency_level", "")).strip()
            is_matrix_table = ("learning outcomes" in d_lower or "outcomes" in d_lower)

            tagged_content = (
                f"[OFFICIAL NIE TIG SYLLABUS MATRIX]\n{doc}"
                if is_matrix_table and "[OFFICIAL NIE TIG SYLLABUS MATRIX]" not in doc
                else doc
            )

            item = {
                "content": tagged_content,
                "metadata": meta,
                "source": meta.get("source", "PDF"),
                "doc_type": meta.get("doc_type", "teacher_guide")
            }

            # Exact competency level match එක පමණක් exact_matrix_docs වලට එකතු කිරීම
            if meta_lvl == target_level and is_matrix_table:
                exact_matrix_docs.append(item)
            elif is_matrix_table:
                syllabus_matrix_docs.append(item)
            else:
                other_docs.append(item)

        # Exact target level chunks ඇතුළත outcomes (bullets) වැඩි chunk එක පළමුව තැබීම
        exact_matrix_docs.sort(
            key=lambda x: len(re.findall(r"^[\u2022\u2023\u25E6\u2043\u2219\*\-\–\—\d+\.]\s*", x["content"], re.MULTILINE)),
            reverse=True
        )

        tig_items = exact_matrix_docs + syllabus_matrix_docs + other_docs[:5]

        # 5. Retrieve Textbook paragraphs
        query_vector_tb = self.embedder.encode(
            f"{clean_subject} {clean_grade} {target_level} {query}"
        ).tolist()

        textbook_res = self.collection.query(
            query_embeddings=[query_vector_tb],
            n_results=4,
            where={
                "$and": [
                    {"grade_level": clean_grade},
                    {"subject": clean_subject},
                    {"doc_type": "textbook"}
                ]
            }
        )

        textbook_items = []
        if textbook_res.get("documents") and textbook_res["documents"][0]:
            for doc, meta in zip(textbook_res["documents"][0], textbook_res["metadatas"][0]):
                if doc.strip():
                    textbook_items.append({
                        "content": f"[STUDENT TEXTBOOK SUPPLEMENTARY CONTENT]\n{doc}",
                        "metadata": meta,
                        "source": meta.get("source", "PDF"),
                        "doc_type": meta.get("doc_type", "textbook")
                    })

        return {
            "competency_level": target_level,
            "tig_guidelines": tig_items,
            "textbook_paragraphs": textbook_items
        }

    def retrieve_3tier_boundaries(
        self,
        query: str,
        target_grade: str = "Grade 8",
        subject: str = "Civic Education"
    ) -> Dict[str, Any]:
        query_vector = self.embedder.encode(query).tolist()
        clean_grade = target_grade.strip()
        clean_subject = subject.strip()

        grade_num_match = re.search(r"\d+", clean_grade)
        curr_g = int(grade_num_match.group(0)) if grade_num_match else 8

        prereq_g_str = f"Grade {max(6, curr_g - 1)}"
        upper_g_str = f"Grade {min(9, curr_g + 1)}"

        target_res = self.collection.query(
            query_embeddings=[query_vector],
            n_results=5,
            where={
                "$and": [
                    {"grade_level": clean_grade},
                    {"subject": clean_subject}
                ]
            }
        )

        prereq_res = self.collection.query(
            query_embeddings=[query_vector],
            n_results=3,
            where={
                "$and": [
                    {"grade_level": prereq_g_str},
                    {"subject": clean_subject}
                ]
            }
        )

        upper_res = self.collection.query(
            query_embeddings=[query_vector],
            n_results=3,
            where={
                "$and": [
                    {"grade_level": upper_g_str},
                    {"subject": clean_subject}
                ]
            }
        )

        exemplar_content = self.retrieve_exemplar_lesson_plan(subject=clean_subject)

        def format_results(res) -> List[Dict[str, Any]]:
            items = []
            if res.get("documents") and res["documents"][0]:
                for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
                    items.append({
                        "content": doc,
                        "metadata": meta,
                        "competency": meta.get("competence", meta.get("competency", "General")),
                        "competency_level": meta.get("competency_level", "General"),
                        "source": meta.get("source", "TIG"),
                        "doc_type": meta.get("doc_type", "teacher_guide")
                    })
            return items

        return {
            "tier_1_target_content": format_results(target_res),
            "tier_2_prerequisites": format_results(prereq_res),
            "tier_3_upper_boundaries": format_results(upper_res),
            "practical_exemplars": [{"content": exemplar_content, "source": "Ingested Sample Plan"}]
        }