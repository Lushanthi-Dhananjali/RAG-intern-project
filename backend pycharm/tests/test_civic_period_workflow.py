import inspect
from unittest.mock import patch

import pytest

from app.schemas.lesson_plan_schema_dto import (
    LessonDevelopmentStepDto,
    LessonPlanSchemaDto,
)
from app.services.activity_options_engine import generate_fallback_options
from app.services.i_lesson_plan_service import LessonPlanGenerateRequest
from app.services.lesson_plan_service import LessonPlanMlService
from app.services.outcome_allocator import (
    allocate_learning_outcomes_across_periods,
    extract_civic_tig_learning_outcomes,
)
from app.services.rag_generator import RAGLessonPlanGenerator
from app.services.prompt_templates import build_lesson_plan_prompt
from app.services.subject_guard import resolve_civic_grade


OFFICIAL_OUTCOMES = [
    "Identifies the public services.",
    "Explains the need of public services.",
    "Investigates information on the beginning and progress of public services.",
    "Presents views appreciating the importance of public services of the times.",
    "Explains the common features related to public services.",
]

TIG_OUTCOME_SECTION = """Competency Level: 8.1.1
Public services
Competency Level
:
8.1.1
No. of Periods: 02
Learning Outcomes:
�
Identifies the public services.
�
Explains the need of public services
.
�
Investigates information on the beginning and progress of public services.
�
Presents views appreciating the importance of public services of the times.
�
Explains the common features related to public services.

Instructions for Lesson Planning:
Ask students to investigate public services and prepare a report.
• This instruction must not be extracted as an outcome.

Competency Level
;
8.1.2
Learning Outcomes:
• Identifies another competency's outcome.
"""


def test_civic_extractor_returns_only_verbatim_outcomes_for_selected_competency():
    outcomes = extract_civic_tig_learning_outcomes(TIG_OUTCOME_SECTION, "8.1.1")

    assert outcomes == OFFICIAL_OUTCOMES


def test_civic_extractor_does_not_use_a_different_competency_or_unstructured_text():
    outcomes = extract_civic_tig_learning_outcomes(TIG_OUTCOME_SECTION, "8.1.2")
    missing_header = extract_civic_tig_learning_outcomes(
        "Learning Outcomes:\n• Invented curriculum text", "8.1.1"
    )

    assert outcomes == ["Identifies another competency's outcome."]
    assert missing_header == []


def test_lesson_plan_generator_accepts_period_progression_context():
    parameters = inspect.signature(
        RAGLessonPlanGenerator.generate_lesson_plan
    ).parameters

    assert "progression_context" in parameters


def test_civic_prompt_keeps_assessment_in_closure_not_development_steps():
    civic_prompt = build_lesson_plan_prompt(
        query="Public services",
        grade="Grade 8",
        subject="Civic Education",
        competency_level="8.1.1",
    )
    science_prompt = build_lesson_plan_prompt(
        query="Plant growth",
        grade="Grade 8",
        subject="Science",
        competency_level="8.1.1",
    )

    assert '"assessment_and_feedback":' not in civic_prompt
    assert '"assessment_and_feedback":' in science_prompt
    assert "Pupil's Textbook" not in civic_prompt


def test_civic_grade_resolution_rejects_non_grade_values():
    assert resolve_civic_grade("Andhra Pradesh", "8.1.1") == "Grade 8"
    assert resolve_civic_grade("Grade 7", "8.1.1") == "Grade 7"


def make_plan():
    return LessonPlanSchemaDto(
        grade="Grade 8",
        subject="Civic Education",
        time_allocation="40 Minutes (Period 2 of 3)",
        competence="Democratic governance",
        competence_level="8.1.1",
        lesson="Public services",
        unique_learning_outcome=[OFFICIAL_OUTCOMES[0]],
        the_entrance="Students discuss a local service they use.",
        lesson_development_steps=[
            LessonDevelopmentStepDto(
                step_number=1,
                teacher_activities="Introduces the task.",
                student_activities="Discuss the scenario.",
                learning_teaching_method="Guided discussion",
                learning_teaching_aids="Scenario card",
                assessment_and_feedback="Teacher checks initial responses.",
                time_minutes=15,
            ),
            LessonDevelopmentStepDto(
                step_number=2,
                teacher_activities="Facilitates student presentations.",
                student_activities="Present group findings.",
                learning_teaching_method="Group presentation",
                learning_teaching_aids="Student notebooks",
                assessment_and_feedback="Peers give feedback.",
                time_minutes=15,
            ),
        ],
        summary="Students summarize how institutions provide services.",
        assessment_and_feedback_whole_lesson="Students complete a short exit quiz.",
        post_activity="Observe a public service used in the community.",
    )


@pytest.mark.parametrize("period_count", [1, 2, 3, 4])
def test_outcome_allocation_covers_official_outcomes_without_rewriting(period_count):
    allocation = allocate_learning_outcomes_across_periods(
        OFFICIAL_OUTCOMES,
        periods=period_count,
        competency_level="8.1.1",
    )

    allocated = [
        outcome
        for period in range(1, period_count + 1)
        for outcome in allocation.get_outcomes_for_period(period)
    ]
    assert set(allocated) == set(OFFICIAL_OUTCOMES)
    assert all(outcome in OFFICIAL_OUTCOMES for outcome in allocated)
    assert len(allocation.period_allocations) == period_count


def test_saved_outcome_allocation_can_be_restored_for_regeneration():
    allocation = allocate_learning_outcomes_across_periods(
        OFFICIAL_OUTCOMES,
        periods=3,
        competency_level="8.1.1",
    )
    saved_allocation = {
        1: [OFFICIAL_OUTCOMES[4]],
        2: [OFFICIAL_OUTCOMES[2]],
        3: [OFFICIAL_OUTCOMES[0], OFFICIAL_OUTCOMES[1], OFFICIAL_OUTCOMES[3]],
    }

    assert allocation.restore_period_allocations(saved_allocation)
    assert allocation.get_outcomes_for_period(2) == [OFFICIAL_OUTCOMES[2]]


def test_fallback_activity_options_are_three_and_avoid_prior_activity():
    first_period = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=OFFICIAL_OUTCOMES[:2],
        current_period=1,
        total_periods=3,
        student_count=35,
        lesson_topic="Public services",
    )
    previous_title = first_period["options"][0]["title"].split(":")[0]
    second_period = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=OFFICIAL_OUTCOMES[2:4],
        current_period=2,
        total_periods=3,
        student_count=48,
        lesson_topic="Public services",
        previous_activities=[previous_title],
    )

    assert len(first_period["options"]) == 3
    assert len(second_period["options"]) == 3
    assert all(
        previous_title.lower() not in option["title"].lower()
        for option in second_period["options"]
    )
    assert all("9 teams" in option["student_grouping"] for option in second_period["options"])


def make_service():
    with patch("app.services.lesson_plan_service.RAGLessonPlanGenerator"), patch(
        "app.services.lesson_plan_service.chromadb.PersistentClient"
    ):
        service = LessonPlanMlService()
    service.rag_engine.retriever.retrieve_tig_and_textbook_for_level.return_value = {
        "tig_guidelines": [{
            "content": "Official curriculum outcomes",
            "source": "Civic_Education_Grade_8_Teacher_Guide.pdf",
        }],
        "textbook_paragraphs": [{
            "content": "Supplemental textbook material",
            "source": "https://api.learn.kandy.lk/textbook/8.1.1",
        }],
    }
    service.rag_engine.generate_lesson_plan.return_value = make_plan()
    service.rag_engine.evaluator.evaluate_lesson_plan.return_value = {
        "grounding_score": 1.0,
        "passed": True,
        "unsupported_claims": [],
    }
    service.rag_engine.alignment_evaluator.evaluate_alignment.return_value = {
        "overall_alignment_score": 1.0,
        "passed_alignment_guardrail": True,
    }
    return service


@pytest.mark.asyncio
async def test_activity_discovery_uses_saved_sequence_activity_history():
    service = make_service()
    service.rag_engine.generate_activity_options.return_value = {"options": []}
    with patch(
        "app.services.lesson_plan_service.get_competency_period_plans",
        return_value={
            1: {"total_periods": 3, "selected_activity": "Earlier role-play"},
            2: {"total_periods": 3, "selected_activity": "Current rejected activity"},
            3: {"total_periods": 3, "selected_activity": "Future plan activity"},
        },
    ):
        await service.suggest_pedagogical_options_async(
            competency_level="8.1.1",
            grade_level="Andhra Pradesh",
            subject="Civic Education",
            periods=3,
            requested_period=2,
            previous_period_activities=["Browser session history"],
        )

    assert service.rag_engine.generate_activity_options.call_args.kwargs["grade_level"] == "Grade 8"
    passed_activities = service.rag_engine.generate_activity_options.call_args.kwargs[
        "previous_activities"
    ]
    assert passed_activities == [
        "Browser session history",
        "Earlier role-play",
        "Current rejected activity",
    ]


@pytest.mark.asyncio
async def test_single_period_request_generates_and_persists_only_requested_period():
    service = make_service()
    saved_allocation = {
        "1": [OFFICIAL_OUTCOMES[4]],
        "2": [OFFICIAL_OUTCOMES[2]],
        "3": [OFFICIAL_OUTCOMES[0], OFFICIAL_OUTCOMES[1], OFFICIAL_OUTCOMES[3]],
    }
    with patch(
        "app.services.lesson_plan_service.extract_civic_tig_learning_outcomes",
        return_value=OFFICIAL_OUTCOMES,
    ), patch(
        "app.services.lesson_plan_service.get_competency_period_plans",
        return_value={
            1: {
                "total_periods": 3,
                "outcome_allocation": saved_allocation,
            }
        },
    ), patch("app.services.lesson_plan_service.save_generated_plan") as save_plan:
        result = await service.generate_lesson_plan_async(
            LessonPlanGenerateRequest(
                query="Public services",
                competency_level="8.1.1",
                grade_level="Andhra Pradesh",
                subject="Civic Education",
                periods=3,
                current_period=2,
                single_period_only=True,
                selected_activity_option="Community service mapping",
            )
        )

    assert len(result.lesson_plans) == 1
    assert len(service.rag_engine.generate_lesson_plan.call_args_list) == 1
    assert service.rag_engine.generate_lesson_plan.call_args.kwargs["current_period"] == 2
    assert service.rag_engine.generate_lesson_plan.call_args.kwargs["retrieved_outcomes"] == [
        OFFICIAL_OUTCOMES[2]
    ]
    saved_json = save_plan.call_args.args[0]
    assert saved_json["period_number"] == 2
    assert saved_json["total_periods"] == 3
    assert saved_json["selected_activity"] == "Community service mapping"
    assert saved_json["outcome_allocation"] == saved_allocation
    assert saved_json["grade"] == "Grade 8"
    assert saved_json["the_entrance"] == "Students discuss a local service they use."
    assert saved_json["assessment_and_feedback_whole_lesson"] == "Students complete a short exit quiz."
    assert saved_json["information_sources"] == ["Civic_Education_Grade_8_Teacher_Guide.pdf"]
    assert all(not step["assessment_and_feedback"] for step in saved_json["lesson_development_steps"])
    assert save_plan.call_args.args[1] == "Grade_8_comp_8_1_1_p2.json"
    service.rag_engine.retriever.retrieve_tig_and_textbook_for_level.assert_called_once_with(
        "8.1.1",
        "Public services",
        "Grade 8",
        "Civic Education",
    )


@pytest.mark.asyncio
async def test_civic_generation_stops_when_curriculum_outcomes_are_unavailable():
    service = make_service()
    with patch(
        "app.services.lesson_plan_service.extract_civic_tig_learning_outcomes",
        return_value=[],
    ):
        with pytest.raises(ValueError, match="No official learning outcomes were retrieved"):
            await service.generate_lesson_plan_async(
                LessonPlanGenerateRequest(
                    query="Public services",
                    competency_level="8.1.1",
                    grade_level="Grade 8",
                    subject="Civic Education",
                    periods=2,
                    current_period=2,
                    single_period_only=True,
                )
            )

    service.rag_engine.generate_lesson_plan.assert_not_called()


def test_period_plans_are_individually_visible_in_generated_plan_library(tmp_path, monkeypatch):
    from app.services import generated_plans_manager

    monkeypatch.setattr(generated_plans_manager, "GENERATED_PLANS_DIR", str(tmp_path))
    plan = make_plan().model_dump(mode="json")
    plan["period_number"] = 1
    generated_plans_manager.save_generated_plan(plan, "Grade_8_comp_8_1_1_p1.json")
    plan["period_number"] = 2
    generated_plans_manager.save_generated_plan(plan, "Grade_8_comp_8_1_1_p2.json")

    summaries = generated_plans_manager.list_generated_plans(
        grade="Grade 8",
        subject="Civic Education",
    )

    assert [summary["filename"] for summary in summaries] == [
        "Grade_8_comp_8_1_1_p1.json",
        "Grade_8_comp_8_1_1_p2.json",
    ]
    saved = generated_plans_manager.get_generated_plan("Grade_8_comp_8_1_1_p2.json")
    assert saved["plan"]["period_number"] == 2
