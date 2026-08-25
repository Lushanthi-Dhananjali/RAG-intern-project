import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from vector_store import ChromaVectorStore

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATASET_DIR = Path("./data/dataset")
RAFT_OUTPUT_FILE = Path("./data/raft_training_dataset.jsonl")


# --- Pydantic Schema for GPT-4 RAFT Answer Generation ---

class RAFTChainOfThoughtAnswer(BaseModel):
    """Schema forcing GPT-4 to generate a Chain-of-Thought + Structured Lesson Plan."""
    reasoning_and_citation: str = Field(
        description="Chain-of-Thought reasoning. Identify which document is the Oracle (relevant), "
                    "quote verbatim key standards from it, and explain why other documents are distractors."
    )
    title: str = Field(description="Lesson plan title")
    subject: str = Field(default="Civic Education", description="Subject name")
    grade_level: str = Field(description="Target grade level")
    educational_goal_or_standard: str = Field(description="Aligned educational goal or constitutional standard")
    objectives: List[str] = Field(description="List of specific, measurable learning objectives")
    materials: List[str] = Field(description="Required physical or digital teaching materials")
    procedures: List[Dict[str, str]] = Field(
        description="Step-by-step instructional flow (e.g., Phase Title, Duration, Teacher Action, Student Action)"
    )
    verification: str = Field(description="Assessment check and standard alignment explanation")


# --- Helper Functions ---

def get_distractor_documents(chroma_db: ChromaVectorStore, count: int = 2) -> List[str]:
    """Retrieves random distractor documents from ChromaDB or fallback snippets."""
    try:
        # Fetch generic chunks across different subjects to act as noise
        all_docs = chroma_db.collection.get(limit=20).get("documents", [])
        if len(all_docs) >= count:
            return random.sample(all_docs, count)
    except Exception as e:
        print(f"⚠️ Could not pull distractors from ChromaDB: {e}")

    # Fallback static distractors if ChromaDB is empty
    fallback_distractors = [
        "Grade 10 Mathematics: Solving quadratic equations using the quadratic formula x = (-b ± √(b² - 4ac)) / 2a.",
        "Grade 8 General Science: Photosynthesis is the chemical reaction where plants convert CO2 and H2O into glucose and O2."
    ]
    return fallback_distractors[:count]


def generate_single_raft_triplet(
    raw_pair: Dict[str, Any],
    chroma_db: ChromaVectorStore,
    include_oracle: bool = True
) -> Dict[str, Any]:
    """
    Generates one RAFT training triplet (Q, Context [Oracle + Distractors], CoT Answer).
    """
    normalized = raw_pair.get("normalized_output", {})
    topic = normalized.get("topic", "Civic Education Principles")
    grade = normalized.get("grade_level", "Grade 9")
    subject = normalized.get("subject", "Civic Education")

    # 1. User Question (Q)
    question = f"Generate a detailed, aligned {subject} lesson plan for {grade} on the topic of '{topic}'."

    # 2. Prepare Context Documents
    oracle_doc = f"CORRECT CURRICULUM REFERENCE:\n{json.dumps(normalized, indent=2)}"
    distractors = get_distractor_documents(chroma_db, count=2)

    retrieved_docs = []
    if include_oracle:
        retrieved_docs.append({"doc_id": "Doc_1 (Oracle)", "text": oracle_doc})
        for idx, dist in enumerate(distractors, 2):
            retrieved_docs.append({"doc_id": f"Doc_{idx} (Distractor)", "text": dist})
    else:
        # 20% of RAFT data includes ONLY distractors to teach the model fallback reasoning
        for idx, dist in enumerate(distractors, 1):
            retrieved_docs.append({"doc_id": f"Doc_{idx} (Distractor)", "text": dist})

    # Shuffle document order so Oracle isn't always Doc_1
    random.shuffle(retrieved_docs)

    # Format context block
    context_str = "\n\n".join([f"[{d['doc_id']}]\n{d['text']}" for d in retrieved_docs])

    # 3. Use GPT-4 to generate Chain-of-Thought Answer (A*)
    system_prompt = (
        "You are an expert RAFT (Retrieval-Augmented Fine-Tuning) teacher training engine. "
        "Your job is to generate a Chain-of-Thought answer based on retrieved context documents.\n"
        "1. In 'reasoning_and_citation', analyze the provided documents. Explicitly state which document "
        "contains the correct curriculum standard and quote relevant parts verbatim. Explain why other documents are distractors.\n"
        "2. Then generate the final structured lesson plan matching the curriculum context."
    )

    user_prompt = f"Question: {question}\n\nRetrieved Context Documents:\n{context_str}"

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=RAFTChainOfThoughtAnswer
    )

    parsed_answer = response.choices[0].message.parsed

    # Format complete RAFT record
    raft_record = {
        "instruction": system_prompt,
        "input": f"Question: {question}\n\nRetrieved Documents:\n{context_str}",
        "output": f"## Chain-of-Thought Reasoning:\n{parsed_answer.reasoning_and_citation}\n\n"
                  f"## Generated Lesson Plan:\n"
                  f"**Title:** {parsed_answer.title}\n"
                  f"**Subject:** {parsed_answer.subject} | **Grade:** {parsed_answer.grade_level}\n"
                  f"**Standard:** {parsed_answer.educational_goal_or_standard}\n\n"
                  f"### Objectives:\n" + "\n".join([f"- {o}" for o in parsed_answer.objectives]) + "\n\n"
                  f"### Materials:\n" + "\n".join([f"- {m}" for m in parsed_answer.materials]) + "\n\n"
                  f"### Procedures:\n" + "\n".join([f"Step {idx+1}: {p.get('phase_title', 'Phase')} ({p.get('duration', '10m')})\n  Teacher: {p.get('teacher_action', '')}\n  Student: {p.get('student_action', '')}" for idx, p in enumerate(parsed_answer.procedures)]) + "\n\n"
                  f"### Verification & Assessment:\n{parsed_answer.verification}"
    }

    return raft_record


# --- Main Dataset Generation Loop ---

def generate_full_raft_dataset(oracle_ratio: float = 0.8):
    """
    Reads all Phase 1 pair files and creates a `.jsonl` dataset for RAFT fine-tuning.
    :param oracle_ratio: 80% with Oracle + Distractors, 20% with Distractors only (per RAFT paper).
    """
    chroma_db = ChromaVectorStore(embedding_provider="openai")
    dataset_files = list(DATASET_DIR.glob("*_pair.json"))

    if not dataset_files:
        print(f"❌ No dataset pairs found in '{DATASET_DIR}'. Run Phase 1 pipeline first!")
        return

    print(f"🚀 Generating RAFT Dataset from {len(dataset_files)} input pairs...")

    raft_data_points = []
    for file_path in dataset_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_pair = json.load(f)

        # Decide whether to include Oracle (80% probability)
        include_oracle = random.random() < oracle_ratio

        print(f"  ├─ Processing '{file_path.name}' (Oracle Included: {include_oracle})...")
        record = generate_single_raft_triplet(raw_pair, chroma_db, include_oracle=include_oracle)
        raft_data_points.append(record)

    # Save to JSONL
    with open(RAFT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in raft_data_points:
            f.write(json.dumps(record) + "\n")

    print(f"\n✅ Successfully generated {len(raft_data_points)} RAFT training records!")
    print(f"💾 Saved RAFT dataset to: '{RAFT_OUTPUT_FILE}'")


if __name__ == "__main__":
    generate_full_raft_dataset()