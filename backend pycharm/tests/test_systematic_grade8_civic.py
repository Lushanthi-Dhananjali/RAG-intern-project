import os
import sys
import json
import asyncio
from datetime import datetime

# Adjust paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.multi_grade_retriever import MultiGradeBoundaryRetriever
from app.services.lesson_plan_service import LessonPlanMlService
from app.services.i_lesson_plan_service import LessonPlanGenerateRequest

TEST_CASES = [
    {
        "id": "TC-01",
        "unit": "Public Services",
        "competency_level": "8.1.1",
        "periods": 1,
        "expected_duration": 40,
        "min_steps": 2
    },
    {
        "id": "TC-02",
        "unit": "Disaster Situations",
        "competency_level": "8.4.2",
        "periods": 2,
        "expected_duration": 80,
        "min_steps": 3
    },
    {
        "id": "TC-03",
        "unit": "Worker Performance",
        "competency_level": "8.6.8",
        "periods": 3,
        "expected_duration": 120,
        "min_steps": 4
    },
    {
        "id": "TC-04",
        "unit": "Workplace Ethics",
        "competency_level": "8.6.9",
        "periods": 4,
        "expected_duration": 160,
        "min_steps": 5
    },
    {
        "id": "TC-05",
        "unit": "Public Institutions",
        "competency_level": "8.1.2",
        "periods": 2,
        "expected_duration": 80,
        "min_steps": 3
    }
]


async def run_systematic_tests():
    print("=" * 80)
    print("STARTING SYSTEMATIC EVALUATION: GRADE 8 CIVIC EDUCATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    retriever = MultiGradeBoundaryRetriever()
    service = LessonPlanMlService()
    results = []

    for tc in TEST_CASES:
        print(f"\nExecuting {tc['id']} [Competency: {tc['competency_level']} | {tc['periods']} Period(s)]...")

        # 1. Test Retrieval Isolation
        retrieval_res = retriever.retrieve_tig_and_textbook_for_level(
            competency_level=tc["competency_level"],
            query=tc["unit"],
            grade_level="Grade 8",
            subject="Civic Education"
        )
        tig_count = len(retrieval_res.get("tig_guidelines", []))
        tb_count = len(retrieval_res.get("textbook_paragraphs", []))
        retrieval_pass = tig_count > 0

        # 2. Test Generation & Structural Validation
        req_dto = LessonPlanGenerateRequest(
            query=f"Competency {tc['competency_level']}: {tc['unit']}",
            competency_level=tc["competency_level"],
            grade_level="Grade 8",
            subject="Civic Education",
            periods=tc["periods"],
            duration_minutes=tc["expected_duration"],
            time_slot=f"{tc['expected_duration']} Minutes ({tc['periods']} Periods)"
        )

        try:
            response = await service.generate_lesson_plan_async(req_dto)
            plan = response.lesson_plan

            # Structural Checks
            steps = plan.lesson_development_steps
            total_step_time = sum(step.time_minutes for step in steps)
            multiples_of_five = all(step.time_minutes % 5 == 0 for step in steps)
            step_count_pass = len(steps) >= tc["min_steps"]
            duration_pass = total_step_time == tc["expected_duration"]
            outcomes_exist = len(plan.unique_learning_outcome) > 0

            grounding_score = response.fact_check_report.get("grounding_score",
                                                             1.0) if response.fact_check_report else 1.0

            overall_pass = (
                    retrieval_pass and
                    duration_pass and
                    multiples_of_five and
                    step_count_pass and
                    outcomes_exist
            )

            results.append({
                "id": tc["id"],
                "competency": tc["competency_level"],
                "periods": tc["periods"],
                "retrieved_chunks": tig_count + tb_count,
                "step_count": f"{len(steps)} (min {tc['min_steps']})",
                "duration_check": f"{total_step_time}/{tc['expected_duration']}m",
                "multiples_of_5": "PASS" if multiples_of_five else "FAIL",
                "grounding": f"{grounding_score * 100:.1f}%",
                "status": "PASS" if overall_pass else "FAIL"
            })

        except Exception as err:
            results.append({
                "id": tc["id"],
                "competency": tc["competency_level"],
                "periods": tc["periods"],
                "retrieved_chunks": tig_count + tb_count,
                "step_count": "N/A",
                "duration_check": "ERROR",
                "multiples_of_5": "N/A",
                "grounding": "0.0%",
                "status": f"FAIL ({str(err)[:20]})"
            })

    # Summary Display
    print("\n" + "=" * 80)
    print("SYSTEMATIC TEST REPORT SUMMARY")
    print("=" * 80)
    print(
        f"{'ID':<7} | {'Level':<7} | {'Periods':<7} | {'Steps':<12} | {'Duration':<10} | {'5m Rules':<8} | {'Grounding':<9} | {'Status'}")
    print("-" * 80)
    for r in results:
        print(
            f"{r['id']:<7} | {r['competency']:<7} | {r['periods']:<7} | {r['step_count']:<12} | {r['duration_check']:<10} | {r['multiples_of_5']:<8} | {r['grounding']:<9} | {r['status']}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_systematic_tests())