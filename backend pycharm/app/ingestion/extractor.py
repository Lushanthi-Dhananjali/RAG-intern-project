import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from schema import LessonPlanSchema

# Load API key from .env file
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_structured_lesson_plan(raw_text: str) -> LessonPlanSchema:
    """
    Takes raw, unstructured lesson plan text and uses GPT-4 to parse and normalize
    it into a strict LessonPlanSchema object.
    """
    system_prompt = (
        "You are an expert Civic Education curriculum normalization engine. "
        "Your task is to parse unstructured Civic Education lesson plans and curriculum benchmarks "
        "into a clean, standardized structure. Ensure accurate mapping of Grade Level, Subject "
        "(Civic Education), Specific Topic, Constitutional/National Standards, and Learning Outcomes while "
        "preserving logical flow: Learning Outcomes -> Materials -> Procedures -> Verification."
    )

    # Use OpenAI's structured output parser
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # gpt-4o-mini is fast, accurate, and low-cost for extraction
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract and normalize this raw lesson plan:\n\n{raw_text}"}
        ],
        response_format=LessonPlanSchema,
    )

    # Return parsed Pydantic object
    return response.choices[0].message.parsed


# --- Demonstration Run ---
if __name__ == "__main__":
    # Sample raw unstructured text (simulating text extracted from a messy PDF or website)
    sample_raw_pdf_text = """
    LESSON PLAN: Grade 8 Photosynthesis Basics
    Teacher: Science Dept | Duration: 45 Mins
    Goal: Standard 8.LS.1 - Understand cellular food synthesis in green plants.

    What kids will learn:
    1. Define photosynthesis in simple words.
    2. Name inputs (water, CO2, sunlight) and outputs (glucose, oxygen).

    Stuff needed for class:
    - 30 copies of Chloroplast diagram worksheet (1 per student)
    - 1 Pottered green plant for teacher demonstration
    - Digital projector for short 3-minute video

    How the lesson goes:
    Phase 1: Hook (7 min) - Teacher shows green plant vs dark-stored plant. Students guess why one is yellowing.
    Phase 2: Direct Instruction (18 min) - Teacher presents 5 slides on chemical inputs and outputs. Students take guided notes.
    Phase 3: Group Activity (12 min) - Students label the chloroplast diagram in pairs.
    Phase 4: Wrap-up (8 min) - Review main takeaways together.

    Assessment:
    Exit ticket check: 'Write down 2 inputs and 1 output of photosynthesis.'
    Alignment check: The exit ticket directly verifies if student met Objective 2.
    """

    print("⏳ Sending raw text to GPT-4 for structured normalization...")

    try:
        normalized_data: LessonPlanSchema = extract_structured_lesson_plan(sample_raw_pdf_text)

        print("\n✅ Extraction Successful!")
        print(f"Title: {normalized_data.title}")
        print(f"Subject: {normalized_data.subject}")
        print(f"Educational Goal: {normalized_data.educational_goal}")

        print("\n--- Extracted Objectives ---")
        for obj in normalized_data.objectives:
            print(f" [{obj.id}] {obj.description} (Bloom's: {obj.blooms_taxonomy_level})")

        print("\n--- Extracted Procedures ---")
        for proc in normalized_data.procedures:
            print(f" Step {proc.step_number} ({proc.phase_title} - {proc.duration_minutes}m):")
            print(f"    Teacher: {proc.teacher_action}")
            print(f"    Student: {proc.student_action}")

        # Save normalized JSON output to file
        output_filename = "normalized_sample.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(normalized_data.model_dump_json(indent=2))
        print(f"\n💾 Saved clean JSON to '{output_filename}'")

    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        print("Note: Ensure you have added a valid OPENAI_API_KEY with active quota in your .env file.")