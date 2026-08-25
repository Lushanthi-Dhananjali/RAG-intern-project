import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Document Readers
from pypdf import PdfReader
import docx

# OpenAI & Updated Schema
from openai import OpenAI
from schema import LessonPlanSchema
from ingestion import ingest_document  # Uses universal PDF/DOCX/TXT/Web ingestion

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create data directories if they don't exist
RAW_DATA_DIR = Path("./data/raw")
DATASET_DIR = Path("./data/dataset")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)


# --- 1. GPT-4 CIVIC EDUCATION CURRICULUM EXTRACTOR ---

def parse_curriculum_with_gpt4(raw_text: str) -> LessonPlanSchema:
    """
    Parses raw document text into standardized LessonPlanSchema JSON using GPT-4,
    tailored specifically for Civic Education curriculum standards.
    """
    # 📌 UPDATED: Civic Education system prompt
    system_prompt = (
        "You are an expert Civic Education curriculum normalization engine. "
        "Extract raw Civic Education lesson plans, governance guidelines, or constitutional "
        "curriculum benchmarks into a clean, standardized structure. "
        "Accurately extract Grade Level, Subject (Civic Education), Topic, Educational Goals/Standards, "
        "and preserve the strict logical flow: Learning Outcomes -> Materials -> Procedures -> Verification."
    )

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract and normalize this Civic Education document:\n\n{raw_text}"}
        ],
        response_format=LessonPlanSchema,
    )
    return response.choices[0].message.parsed


# --- 2. DATASET NORMALIZATION & PAIR SAVER (FOR RAFT FINE-TUNING) ---

def save_normalized_pair(file_id: str, raw_text: str, schema_data: LessonPlanSchema) -> Path:
    """
    Saves a raw vs. normalized pair as JSON.
    Generates training dataset pairs for Qwen2-7B/72B fine-tuning.
    """
    pair_record: Dict[str, Any] = {
        "id": file_id,
        "subject": "Civic Education",
        "input_raw_text": raw_text,
        "normalized_output": schema_data.model_dump()
    }

    output_path = DATASET_DIR / f"{file_id}_dataset_pair.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pair_record, f, indent=2)

    return output_path


# --- FULL PHASE 1 PIPELINE EXECUTION ---

def process_single_source(source_path_or_url: str):
    """Executes Phase 1 end-to-end on a local file (.pdf, .docx, .txt) or Web URL."""
    print(f"\n📂 Processing source: {source_path_or_url}")

    # Step 1: Universal document/web ingestion
    raw_text = ingest_document(source_path_or_url)
    print(f"  └─ Extracted {len(raw_text)} raw characters.")

    # Step 2: Extract structured schema with GPT-4
    print("  └─ Sending to GPT-4 for Civic Education normalization...")
    structured_data = parse_curriculum_with_gpt4(raw_text)

    # Step 3: Save training dataset pair
    if source_path_or_url.startswith("http"):
        file_id = "web_civic_lesson"
    else:
        file_id = Path(source_path_or_url).stem

    saved_path = save_normalized_pair(file_id, raw_text, structured_data)

    print(f"  └─ ✅ Successfully normalized! Title: '{structured_data.title}'")
    print(f"  └─ 📌 Topic: '{structured_data.topic}' | Grade: '{structured_data.grade_level}'")
    print(f"  └─ 💾 Saved fine-tuning pair to '{saved_path}'")

    return structured_data


if __name__ == "__main__":
    # 📌 UPDATED: Default sample file set to Civic Education
    sample_file = RAW_DATA_DIR / "civic_education_sample.txt"

    if not sample_file.exists():
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("""
            LESSON PLAN: Grade 9 Civic Education - Democratic Rights and Responsibilities
            Subject: Civic Education | Grade: Grade 9 | Duration: 45 Mins
            Standard / Goal: Understand fundamental constitutional rights and duties of active citizens.

            Learning Outcomes:
            1. Differentiate between legal fundamental rights and civic duties.
            2. Evaluate how citizen participation strengthens local community democracy.

            Materials Needed:
            - Extracts from the Constitution on Rights & Freedoms (1 per pair)
            - Scenario cards covering local governance issues (voting, taxation, public duty)

            Procedures:
            Phase 1: Hook & Discussion (8m): Teacher asks 'What makes a good community member?'
            Phase 2: Direct Instruction (17m): Teacher presents key rights vs obligations.
            Phase 3: Scenario Activity (12m): Group analysis of civic duty scenario cards.
            Phase 4: Wrap-up (8m): Review key rights and citizenship commitments.

            Assessment & Verification:
            Formative Check: Exit ticket listing 1 fundamental right and 1 civic responsibility.
            Alignment: Exit ticket directly verifies Learning Outcomes 1 and 2.
            """)
        print(f"Created Civic Education sample file at: {sample_file}")

    # Run pipeline on Civic Education sample file
    result = process_single_source(str(sample_file))