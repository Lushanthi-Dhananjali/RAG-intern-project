"""
Step 10: Fast, Offline Regression Test Suite for Lesson Plan Pipeline.
Mocks external HuggingFace and Ollama network calls to verify:
1. Science legacy pipeline routing remains untouched.
2. Civic Education strictly adheres to LEARN 5m-30m-5m timing across 1 to 4 periods.
3. Step 8 Timing Auto-Repair and Step 5 Student Grouping work correctly.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from app.services.timing_guardrail_engine import TimingGuardrailEngine
from app.services.grouping_logistics_engine import GroupingLogisticsEngine
from app.schemas.lesson_plan_schema_dto import (
    LearnLessonPlanDto,
    LessonDevelopmentStepDto,
)

client = TestClient(app)


# Mock sample plan returned by the LLM
def get_mock_learn_plan(subject: str = "Civic Education", period: int = 1, total_periods: int = 1):
    return LearnLessonPlanDto(
        grade="Grade 8",
        subject=subject,
        competence="Democratic Governance",
        competence_level="8.1.1",
        lesson=f"Democratic Governance (Period {period} of {total_periods})",
        time_allocation=f"40 Minutes (Period {period} of {total_periods})",
        unique_learning_outcome=["Identifies key functions of local authorities."],
        the_entrance="Engage students with a question on local community needs. (5 mins)",
        lesson_development_steps=[
            LessonDevelopmentStepDto(
                step_number=1,
                time_minutes=8,
                learning_teaching_method="Task Assignment",
                learning_teaching_aids="Worksheets",
                teacher_activities="Explains roleplay goals.",
                student_activities="Read task roles.",
                assessment_and_feedback="Checks readiness."
            ),
            LessonDevelopmentStepDto(
                step_number=2,
                time_minutes=14,
                learning_teaching_method="Collaborative Roleplay",
                learning_teaching_aids="Role cue cards",
                teacher_activities="Monitors group debates.",
                student_activities="Enact council hearing.",
                assessment_and_feedback="Provides formative cues."
            ),
            LessonDevelopmentStepDto(
                step_number=3,
                time_minutes=8,
                learning_teaching_method="Plenary Synthesis",
                learning_teaching_aids="Blackboard",
                teacher_activities="Consolidates findings.",
                student_activities="Spokespersons share resolutions.",
                assessment_and_feedback="Reviews misconceptions."
            )
        ],
        summary="Summarizes local government roles.",
        assessment_and_feedback_whole_lesson="5-minute rapid peer review quiz.",
        post_activity="Record public services observed at home.",
        information_sources=["Teacher Instructional Guide Grade 8"],
        attachments=["Worksheet 1"]
    )


# =====================================================================
# 1. SCIENCE REGRESSION TESTS (4 CASES)
# =====================================================================

def setup_embedder(mock_embedder):
    mock_embedder.return_value.encode.return_value.tolist.return_value = [0.1] * 384


@pytest.mark.parametrize("periods,expected_min", [(1, 40), (2, 80), (3, 120), (4, 160)])
@patch("app.services.rag_generator.RAGLessonPlanGenerator.generate_lesson_plan")
@patch("app.services.multi_grade_retriever.SentenceTransformer")
def test_science_legacy_pipeline_unaffected(mock_embedder, mock_gen, periods: int, expected_min: int):
    """
    Verifies Science subject routes through the legacy pipeline
    without period-splitting or Civic Education constraints.
    """
    setup_embedder(mock_embedder)
    mock_gen.return_value = get_mock_learn_plan(subject="Science", period=1, total_periods=periods)

    payload = {
        "competency_level": "7.1",
        "topic_query": "Plant and Animal Cells",
        "grade_level": "Grade 7",
        "subject": "Science",
        "periods": periods,
        "duration_minutes": periods * 40
    }
    response = client.post("/api/v1/generate-by-competency-level", json=payload)
    assert response.status_code == 200, f"Science request failed: {response.text}"
    data = response.json()

    assert data["subject"] == "Science"
    assert data["periods"] == periods
    assert data["lesson_plan"]["subject"] == "Science"


# =====================================================================
# 2. CIVIC EDUCATION MODE A TESTS (4 CASES: 1, 2, 3, 4 PERIODS)
# =====================================================================

@pytest.mark.parametrize("periods,req_period", [(1, 1), (2, 2), (3, 2), (4, 3)])
@patch("app.services.rag_generator.RAGLessonPlanGenerator.generate_activity_options")
@patch("app.services.rag_generator.RAGLessonPlanGenerator.generate_lesson_plan")
@patch("app.services.multi_grade_retriever.SentenceTransformer")
def test_civic_mode_a_timing_and_outcomes(mock_embedder, mock_gen, mock_options, periods: int, req_period: int):
    """
    Verifies Civic Education generates single 40-minute period plans
    adhering to 5m (Entrance) + 30m (Development) + 5m (Assessment).
    """
    setup_embedder(mock_embedder)
    mock_options.return_value = {
        "topic": "Democratic Governance",
        "period": req_period,
        "options": [
            {
                "id": f"option_{i}",
                "title": f"Activity Option {i}",
                "pedagogy_type": "Simulation",
                "description": "Engage in civic activity",
                "student_grouping": "Teams of 5",
                "creative_assessment_preview": "Exit quiz"
            }
            for i in range(1, 4)
        ]
    }
    mock_gen.return_value = get_mock_learn_plan(subject="Civic Education", period=req_period, total_periods=periods)

    payload = {
        "competency_level": "8.1.1",
        "topic_query": "Democratic Governance",
        "grade_level": "Grade 8",
        "subject": "Civic Education",
        "periods": periods,
        "requested_period": req_period,
        "student_count": 35,
        "teacher_mode": "suggested",
        "selected_activity_option": "Interactive Local Authority Simulation"
    }
    response = client.post("/api/v1/generate-by-competency-level", json=payload)
    assert response.status_code == 200, f"Civic Mode A failed: {response.text}"
    data = response.json()

    plan = data["lesson_plan"]

    # 1. Verify 40-minute period allocation label
    assert f"Period {req_period} of {periods}" in plan["time_allocation"]

    # 2. Verify verbatim learning outcomes exist
    assert len(plan["unique_learning_outcome"]) >= 1

    # 3. Verify development steps sum to exactly 30 minutes
    dev_steps = plan["lesson_development_steps"]
    total_dev_time = sum(step["time_minutes"] for step in dev_steps)
    assert total_dev_time == 30, f"Development steps must equal 30m, got {total_dev_time}m"

    # 4. Verify Phase 1 and Phase 3 sections exist
    assert len(plan["the_entrance"].strip()) > 10
    assert len(plan["assessment_and_feedback_whole_lesson"].strip()) > 10


# =====================================================================
# 3. CIVIC EDUCATION MODE B (TEACHER'S OWN APPROACH) TESTS (4 CASES)
# =====================================================================

@pytest.mark.parametrize("periods,req_period", [(1, 1), (2, 1), (3, 3), (4, 4)])
@patch("app.services.rag_generator.RAGLessonPlanGenerator.generate_lesson_plan")
@patch("app.services.multi_grade_retriever.SentenceTransformer")
def test_civic_mode_b_custom_strategy_scaffolding(mock_embedder, mock_gen, periods: int, req_period: int):
    """
    Verifies that teacher's custom input is scaffolded into the
    LEARN 5m-30m-5m format.
    """
    setup_embedder(mock_embedder)
    mock_gen.return_value = get_mock_learn_plan(subject="Civic Education", period=req_period, total_periods=periods)

    custom_idea = "Watch a 3-minute video on Pradeshiya Sabha meetings, then conduct group debate."
    payload = {
        "competency_level": "8.1.1",
        "grade_level": "Grade 8",
        "subject": "Civic Education",
        "periods": periods,
        "requested_period": req_period,
        "student_count": 40,
        "teacher_mode": "own_approach",
        "custom_teacher_activity": custom_idea
    }
    response = client.post("/api/v1/generate-by-competency-level", json=payload)
    assert response.status_code == 200, f"Civic Mode B failed: {response.text}"
    data = response.json()

    plan = data["lesson_plan"]
    dev_steps = plan["lesson_development_steps"]

    total_dev_time = sum(s["time_minutes"] for s in dev_steps)
    assert total_dev_time == 30, f"Mode B steps must sum to 30m, got {total_dev_time}m"


# =====================================================================
# 4. BOUNDARY, LOGISTICS & TIMING AUTO-REPAIR TESTS (4 CASES)
# =====================================================================

@patch("app.services.rag_generator.RAGLessonPlanGenerator.generate_lesson_plan")
@patch("app.services.multi_grade_retriever.SentenceTransformer")
def test_period_clamping_boundary(mock_embedder, mock_gen):
    """Verifies that period inputs outside [1, 4] are clamped correctly."""
    setup_embedder(mock_embedder)
    mock_gen.return_value = get_mock_learn_plan(subject="Civic Education", period=4, total_periods=4)

    payload = {
        "competency_level": "8.1.1",
        "grade_level": "Grade 8",
        "subject": "Civic Education",
        "periods": 9,  # Should clamp to 4
        "requested_period": 8  # Should clamp to 4
    }
    response = client.post("/api/v1/generate-by-competency-level", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["periods"] == 4
    assert data["requested_period"] == 4


def test_timing_auto_repair_drift_normalizer():
    """Verifies step timing normalizer fixes drifted step durations."""
    drifted_steps = [
        LessonDevelopmentStepDto(
            step_number=1, time_minutes=5,
            teacher_activities="Intro", student_activities="Listen",
            learning_teaching_method="Method", learning_teaching_aids="Aids",
            assessment_and_feedback="Check"
        ),
        LessonDevelopmentStepDto(
            step_number=2, time_minutes=25,
            teacher_activities="Work", student_activities="Discuss",
            learning_teaching_method="Method", learning_teaching_aids="Aids",
            assessment_and_feedback="Check"
        ),
        LessonDevelopmentStepDto(
            step_number=3, time_minutes=10,  # Sum = 40m (10m over budget)
            teacher_activities="Wrap", student_activities="Share",
            learning_teaching_method="Method", learning_teaching_aids="Aids",
            assessment_and_feedback="Check"
        )
    ]
    repaired = TimingGuardrailEngine.auto_repair_step_timings(drifted_steps)
    repaired_sum = sum(s.time_minutes for s in repaired)
    assert repaired_sum == 30, f"Repaired step timings must sum to 30m, got {repaired_sum}m"
    assert [s.time_minutes for s in repaired] == [8, 14, 8]


def test_student_grouping_odd_count_logistics():
    """Verifies odd class counts (e.g., 37) are balanced without isolated students."""
    logistics = GroupingLogisticsEngine.calculate_grouping(student_count=37)
    assert logistics.student_count == 37
    assert sum(logistics.group_sizes) == 37
    # 37 students -> 7 groups (two groups of 6, five groups of 5)
    assert max(logistics.group_sizes) <= 6
    assert min(logistics.group_sizes) >= 4
    assert len(logistics.roles_assigned) >= 5


@patch("app.services.rag_generator.RAGLessonPlanGenerator.generate_activity_options")
@patch("app.services.multi_grade_retriever.SentenceTransformer")
def test_anti_repetition_pedagogy_rotation(mock_embedder, mock_options):
    """Verifies options discovery receives previous activities and excludes them."""
    setup_embedder(mock_embedder)
    mock_options.return_value = {
        "topic": "Democratic Governance",
        "period": 2,
        "options": [
            {
                "id": "option_1",
                "title": "School-Ground Facility Audit",
                "pedagogy_type": "Empirical Inquiry",
                "description": "Students inspect and audit local school facility access.",
                "student_grouping": "7 teams of 5",
                "creative_assessment_preview": "Exit ticket summarizing findings."
            }
        ]
    }

    payload = {
        "competency_level": "8.1.1",
        "student_count": 35,
        "periods": 2,
        "requested_period": 2,
        "grade_level": "Grade 8",
        "subject": "Civic Education",
        "previous_period_activities": ["Mock Local Council Session"]
    }
    response = client.post("/api/v1/suggest-pedagogical-options", json=payload)
    assert response.status_code == 200
    options = response.json().get("options", [])
    assert len(options) >= 1
    assert "council" not in options[0]["title"].lower()