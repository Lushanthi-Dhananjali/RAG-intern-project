import os
import sys
from typing import Dict, Any, List

# =====================================================================
# PATH RESOLUTION:
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.multi_grade_retriever import (
    MultiGradeBoundaryRetriever,
    extract_verbatim_tig_outcomes
)

# Grade 8 Civic Education - Official Test Suite
CIVIC_GRADE8_TEST_SUITE = [
    {"level": "8.1.1", "topic": "Public Services", "min_expected": 4},
    {"level": "8.1.2", "topic": "Public Institutions", "min_expected": 4},
    {"level": "8.1.3", "topic": "Institutions providing public services", "min_expected": 3},
    {"level": "8.4.1", "topic": "Disasters and emergency management", "min_expected": 5},
    {"level": "8.4.2", "topic": "Disasters and emergency management", "min_expected": 2},
    {"level": "8.4.3", "topic": "Disasters and emergency management", "min_expected": 5},
]


def run_systematic_civic_test():
    print("=" * 90)
    print("      SYSTEMATIC TEST RUNNER: GRADE 8 CIVIC EDUCATION TIG PIPELINE")
    print("=" * 90)
    print("Note: Fast-mode verification. No LLM generation calls will be triggered.\n")

    retriever = MultiGradeBoundaryRetriever()
    test_results: List[Dict[str, Any]] = []

    for test in CIVIC_GRADE8_TEST_SUITE:
        lvl = test["level"]
        topic = test["topic"]
        expected_min = test["min_expected"]

        print(f"[*] Testing Competency Level {lvl} ({topic})...")

        # 1. Test Retrieval
        retrieval_res = retriever.retrieve_tig_and_textbook_for_level(
            competency_level=lvl,
            query=topic,
            grade_level="Grade 8",
            subject="Civic Education"
        )

        tig_chunks = retrieval_res.get("tig_guidelines", [])
        tb_chunks = retrieval_res.get("textbook_paragraphs", [])

        # 2. Test Outcome Extraction on Priority 0 Chunk
        outcomes = []
        is_matrix_priority = False

        if tig_chunks:
            top_content = tig_chunks[0]["content"]
            is_matrix_priority = "[OFFICIAL NIE TIG SYLLABUS MATRIX]" in top_content
            outcomes = extract_verbatim_tig_outcomes(top_content, lvl)

        # 3. Status Evaluation
        passed = (
            len(tig_chunks) > 0 and
            is_matrix_priority and
            len(outcomes) >= expected_min
        )

        test_results.append({
            "level": lvl,
            "topic": topic,
            "tig_count": len(tig_chunks),
            "tb_count": len(tb_chunks),
            "is_matrix_p0": is_matrix_priority,
            "outcome_count": len(outcomes),
            "expected_min": expected_min,
            "outcomes": outcomes,
            "status": "PASS" if passed else "FAIL"
        })

    # Summary Report Rendering
    print("\n" + "=" * 90)
    print("                               TEST SUMMARY MATRIX")
    print("=" * 90)
    print(f"{'Level':<8} | {'TIG Chunks':<10} | {'TB Chunks':<10} | {'Matrix @ P0':<12} | {'Outcomes':<10} | {'Status':<6}")
    print("-" * 90)

    total_passed = 0
    for r in test_results:
        if r["status"] == "PASS":
            total_passed += 1
        p0_str = "YES" if r["is_matrix_p0"] else "NO"
        print(f"{r['level']:<8} | {r['tig_count']:<10} | {r['tb_count']:<10} | {p0_str:<12} | {r['outcome_count']} (exp >={r['expected_min']})  | {r['status']:<6}")

    print("-" * 90)
    print(f"Total Completed: {len(test_results)} | Passed: {total_passed} | Failed: {len(test_results) - total_passed}")
    print("=" * 90)

    # Detailed Inspect for Failures
    failed_cases = [r for r in test_results if r["status"] == "FAIL"]
    if failed_cases:
        print("\n[!] DETAILED INVESTIGATION FOR FAILED CASES:")
        for fc in failed_cases:
            print(f"\n--- Competency Level: {fc['level']} ---")
            print(f"Extracted ({fc['outcome_count']}): {fc['outcomes']}")
            if not fc['is_matrix_p0']:
                print("Issue: Priority 0 chunk is NOT rec   ognized as Syllabus Matrix table.")
            elif fc['outcome_count'] < fc['expected_min']:
                print(f"Issue: Extracted outcomes count ({fc['outcome_count']}) is below expected ({fc['expected_min']}). Check for broken/truncated chunk in DB.")
    else:
        print("\nAll Grade 8 Civic Education competency levels verified successfully!")


if __name__ == "__main__":
    run_systematic_civic_test()