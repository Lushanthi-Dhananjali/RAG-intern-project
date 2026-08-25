from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import chromadb
from typing import Optional

from schema import LessonPlanSchema
from extractor import extract_structured_lesson_plan
from rag_generator import RAGLessonPlanGenerator
from alignment_evaluator import AlignmentEvaluator
from evaluator import RAGFactCheckingAgent

from api_models import (
    CurriculumExtractRequest,
    LessonPlanGenerateRequest,
    VerifyAlignmentRequest,
    LessonPlanResponse
)

# =====================================================================
# FASTAPI APP CONFIGURATION
# =====================================================================

app = FastAPI(
    title="Civic Education ML Microservice API",
    description="Python FastAPI ML microservice for Curriculum Extraction, RAG Lesson Plan Generation, and Alignment Verification.",
    version="1.0.0"
)

# CORS Middleware for ASP.NET Core API Gateway & Next.js Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# SINGLETONS & CHROMADB INITIALIZATION
# =====================================================================

# Initialize RAG Pipeline Singletons
rag_engine = RAGLessonPlanGenerator()
standalone_alignment_evaluator = AlignmentEvaluator(threshold=0.75)

# Connect to Local Persistent ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection(
    name="lesson_plans_db",
    metadata={"hnsw:space": "cosine"}
)


# =====================================================================
# ENDPOINTS
# =====================================================================

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "service": "Civic Education ML Microservice",
        "version": "1.0.0"
    }


@app.post(
    "/api/v1/extract-curriculum",
    response_model=LessonPlanSchema,
    status_code=status.HTTP_200_OK,
    tags=["Extraction"]
)
async def extract_curriculum(request: CurriculumExtractRequest):
    """
    POST /api/v1/extract-curriculum
    Normalizes raw, unstructured curriculum text into a structured LessonPlanSchema JSON.
    """
    if not request.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'raw_text' cannot be empty."
        )

    try:
        structured_plan = extract_structured_lesson_plan(request.raw_text)
        return structured_plan
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Curriculum extraction failed: {str(e)}"
        )


@app.post(
    "/api/v1/generate-lesson-plan",
    response_model=LessonPlanResponse,
    status_code=status.HTTP_200_OK,
    tags=["RAG Generation"]
)
async def generate_lesson_plan(request: LessonPlanGenerateRequest):
    """
    POST /api/v1/generate-lesson-plan
    Runs Full RAG Pipeline:
    1. Hybrid context retrieval via ChromaDB (with metadata filters for subject & grade)
    2. Prompt construction with distractor immunity & logical sequence constraints
    3. Structured JSON generation (Ollama / Llama 3)
    4. Sequence completeness validation
    5. Fact-checking & Goal-Alignment evaluation guardrails
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'query' cannot be empty."
        )

    try:
        # --- Step 1: ChromaDB Vector Context Search ---
        retrieved_context_chunks = []
        subject_name = getattr(request, 'subject', 'Civic Education')

        # Query ChromaDB if RAG search is enabled
        use_rag = getattr(request, 'use_rag', True)
        if use_rag:
            try:
                chroma_results = chroma_collection.query(
                    query_texts=[request.query],
                    n_results=3,
                    where={
                        "$and": [
                            {"grade_level": request.grade_level},
                            {"subject": subject_name}
                        ]
                    }
                )
                docs = chroma_results.get("documents", [[]])[0]
                if docs:
                    retrieved_context_chunks = docs
                    print(f"🔍 ChromaDB Vector Retrieval Success: Found {len(docs)} syllabus context chunks.")
            except Exception as chroma_err:
                print(f"⚠️ ChromaDB Query Warning (Falling back to default retriever): {chroma_err}")

        # --- Step 2: RAG Engine Generation ---
        plan = rag_engine.generate_lesson_plan(
            query=request.query,
            grade_level=request.grade_level
        )

        # --- Step 3: Fact-Checking Evaluation ---
        contexts = retrieved_context_chunks if retrieved_context_chunks else rag_engine.retriever.retrieve_context(
            query=request.query,
            subject=subject_name,
            grade_level=request.grade_level
        ).get("contexts", [])

        fact_check = rag_engine.evaluator.evaluate_lesson_plan(plan, contexts)

        # --- Step 4: Alignment Evaluation ---
        alignment = rag_engine.alignment_evaluator.evaluate_alignment(plan)

        return LessonPlanResponse(
            lesson_plan=plan,
            fact_check_report=fact_check,
            alignment_report=alignment
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG Lesson Plan Generation failed: {str(e)}"
        )


@app.post(
    "/api/v1/verify-alignment",
    status_code=status.HTTP_200_OK,
    tags=["Verification & Metrics"]
)
async def verify_alignment(request: VerifyAlignmentRequest):
    """
    POST /api/v1/verify-alignment
    Stand-alone verification endpoint calculating vector semantic similarity and
    qualitative pedagogical alignment scores between an Educational Goal and Objectives.
    """
    if not request.educational_goal.strip() or not request.lesson_objectives:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fields 'educational_goal' and 'lesson_objectives' must be provided."
        )

    try:
        from schema import LearningOutcome
        outcomes = [
            LearningOutcome(id=idx, description=obj)
            for idx, obj in enumerate(request.lesson_objectives, 1)
        ]

        dummy_plan = LessonPlanSchema(
            title="Alignment Verification Request",
            subject="Civic Education",
            grade_level="N/A",
            topic="Verification",
            educational_goal_or_standard=request.educational_goal,
            learning_outcomes=outcomes,
            materials=[],
            procedures=[],
            verification={"formative_assessment": "Check"}
        )

        alignment_report = standalone_alignment_evaluator.evaluate_alignment(dummy_plan)
        return alignment_report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alignment verification failed: {str(e)}"
        )


# =====================================================================
# SERVER RUNNER
# =====================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)