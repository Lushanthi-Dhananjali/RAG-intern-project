import os
import sys
import re
import json
import logging
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

logger = logging.getLogger("CurriculumExtractor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Safe Import for Peradeniya Lesson Plan Schema
try:
    from app.schemas.lesson_plan_schema_dto import PeradeniyaLessonPlanDto
except ModuleNotFoundError:
    try:
        from schemas.lesson_plan_schema_dto import PeradeniyaLessonPlanDto
    except ModuleNotFoundError:
        try:
            from lesson_plan_schema_dto import PeradeniyaLessonPlanDto
        except ModuleNotFoundError:
            try:
                from schema import LessonPlanSchema as PeradeniyaLessonPlanDto
            except ModuleNotFoundError:
                PeradeniyaLessonPlanDto = None

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


# =====================================================================
# 1. TIG MULTI-PAGE CHUNKING BY COMPETENCY BOUNDARY
# =====================================================================
def chunk_tig_by_competency_level(full_pdf_text: str) -> List[Dict[str, Any]]:
    """
    Splits the full text of the Teacher Instructional Guide (TIG) based on
    Competency Level headers rather than arbitrary page breaks.

    Guarantees that tables spanning across page breaks (such as 8.1.3 learning
    outcomes extending into subsequent pages) remain unified under the active
    competency level key until the next level is formally initiated.
    """
    if not full_pdf_text or not full_pdf_text.strip():
        return []

    # Regex matches patterns like "Competency Level 8.1.3", "Competency Level: 8.1.3", or isolated "8.1.3"
    pattern = r"(?:Competency\s*Level\s*[:\-]?\s*(\d+\.\d+\.\d+)|\b(\d+\.\d+\.\d+)\b)"

    matches = list(re.finditer(pattern, full_pdf_text, flags=re.IGNORECASE))

    if not matches:
        logger.warning("No competency level identifiers found matching pattern '\\d+.\\d+.\\d+'.")
        return [{
            "competency_level": "General",
            "content": full_pdf_text.strip()
        }]

    competency_chunks: List[Dict[str, Any]] = []

    for idx, match in enumerate(matches):
        comp_level = match.group(1) or match.group(2)
        start_pos = match.start()

        # Chunk extends up to the start of the next competency level or end of document
        if idx + 1 < len(matches):
            end_pos = matches[idx + 1].start()
            section_content = full_pdf_text[start_pos:end_pos].strip()
        else:
            section_content = full_pdf_text[start_pos:].strip()

        if section_content:
            competency_chunks.append({
                "competency_level": comp_level,
                "content": section_content
            })

    logger.info("Successfully extracted %d unbroken competency level chunks from TIG context.", len(competency_chunks))
    return competency_chunks


# =====================================================================
# 2. LOCAL EXTRACTION ENGINE (OLLAMA / LLAMA 3)
# =====================================================================
def extract_structured_lesson_plan(
        raw_text: str,
        model_name: str = OLLAMA_MODEL,
        ollama_url: str = OLLAMA_BASE_URL
) -> Any:
    """
    Parses unstructured syllabus or exemplar lesson plan text into a clean,
    standardized Peradeniya Practice Teaching structure using local Ollama.
    """
    if not PeradeniyaLessonPlanDto:
        raise ImportError("PeradeniyaLessonPlanDto could not be imported from schemas.")

    pydantic_schema = PeradeniyaLessonPlanDto.model_json_schema()

    system_prompt = (
        "You are an expert Sri Lankan Civic Education curriculum normalization engine following the "
        "University of Peradeniya practice teaching framework. "
        "Your task is to parse unstructured curriculum text into a strictly normalized JSON format. "
        "Extract ALL unique learning outcomes without omitting any items across page boundaries, "
        "and structure classroom steps with full teacher, student, method, aids, and assessment fields."
    )

    prompt = f"""### SYSTEM INSTRUCTION:
{system_prompt}

### RAW CURRICULUM TEXT TO NORMALIZE:
{raw_text}

Extract every single learning outcome and sequential classroom procedure into the required schema.
Output ONLY raw JSON matching this schema:
{json.dumps(pydantic_schema, indent=2)}

JSON Output:"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": pydantic_schema,
        "options": {
            "temperature": 0.1,
            "num_predict": 3072
        }
    }

    logger.info("Sending extraction payload to local Ollama (%s)...", model_name)

    try:
        response = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=180)
        response.raise_for_status()
        raw_output = response.json().get("response", "{}")
    except requests.RequestException as err:
        logger.error("Failed to connect to local Ollama server at %s: %s", ollama_url, err)
        raise ConnectionError(f"Ollama connection failure: {err}")

    clean_json_str = (
        raw_output.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
    )

    try:
        parsed_plan = PeradeniyaLessonPlanDto.model_validate_json(clean_json_str)
        return parsed_plan
    except Exception as validation_err:
        logger.error("Pydantic validation failed for extracted plan: %s", validation_err)
        logger.debug("Raw JSON received: %s", clean_json_str)
        raise ValueError(f"Extracted output violated PeradeniyaLessonPlanDto: {validation_err}")


# =====================================================================
# STANDALONE VERIFICATION TEST
# =====================================================================
if __name__ == "__main__":
    # Simulated Multi-Page TIG Text where Level 8.1.3 crosses a page break
    sample_multi_page_tig_text = """
    =================== PAGE 42 ===================
    Competency Level 8.1.2: Evaluates citizen duties.
    Learning Outcomes:
    - Lists constitutional duties of citizens.
    - Demonstrates awareness of civic obligations.
    Activities: Classroom discussion and chart display.

    =================== PAGE 43 ===================
    Competency Level 8.1.3: Explains the structure and functions of Local Government.
    Learning Outcomes:
    1. Identifies the three types of Local Government bodies in Sri Lanka.
    2. Explains the municipal services provided to residents in urban areas.

    --- [PAGE BREAK / HEADER: CIVIC EDUCATION GRADE 8 TEACHER GUIDE] ---
    =================== PAGE 44 ===================
    3. Evaluates community participation in local government developmental projects.

    Suggested Teaching Learning Process:
    Step 1: Introduction using municipal service photos.
    Step 2: Group activities analyzing village council functions.

    =================== PAGE 45 ===================
    Competency Level 8.1.4: Examines the rule of law.
    Learning Outcomes:
    - Defines the rule of law.
    """

    print("=" * 80)
    print("🔍 TESTING CROSS-PAGE COMPETENCY BOUNDARY CHUNKING")
    print("=" * 80)

    chunks = chunk_tig_by_competency_level(sample_multi_page_tig_text)

    for i, c in enumerate(chunks, 1):
        print(f"\n📦 [Chunk {i}] Competency Level: {c['competency_level']}")
        print(f"📄 Content Length: {len(c['content'])} characters")
        print("--- Content Preview ---")
        lines = c['content'].split("\n")
        print("\n".join(lines[:4]) + "\n...")
        if "Evaluates community participation" in c['content']:
            print("🎯 Success: 3rd cross-page learning outcome successfully preserved in this chunk!")

    # Verify normalization on chunk 8.1.3
    target_chunk = next((ch["content"] for ch in chunks if ch["competency_level"] == "8.1.3"), None)

    if target_chunk:
        print("\n" + "=" * 80)
        print("🚀 RUNNING LOCAL EXTRACTION ON PRESERVED 8.1.3 CHUNK")
        print("=" * 80)
        try:
            extracted_dto = extract_structured_lesson_plan(target_chunk)
            print(f"✅ Extracted Lesson Title: {extracted_dto.lesson}")
            print(f"🎯 Total Learning Outcomes Extracted: {len(extracted_dto.unique_learning_outcome)}")
            for idx, outcome in enumerate(extracted_dto.unique_learning_outcome, 1):
                print(f"   [{idx}] {outcome}")

            output_file = "extracted_8_1_3_plan.json"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted_dto.model_dump_json(indent=2))
            print(f"\n💾 Saved normalized output to '{output_file}'")

        except Exception as exc:
            print(f"⚠️ Extraction execution skipped or failed: {exc}")