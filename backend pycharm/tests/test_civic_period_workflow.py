import inspect
import json
from unittest.mock import Mock, patch

import pytest

from app.schemas.lesson_plan_schema_dto import (
    LessonDevelopmentStepDto,
    LessonPlanSchemaDto,
)
from app.services.activity_options_engine import (
    build_period_options_prompt,
    generate_fallback_options,
)
from app.services.i_lesson_plan_service import LessonPlanGenerateRequest
from app.services.lesson_plan_service import LessonPlanMlService
from app.services.multi_grade_retriever import format_retrieved_source_references
from app.services import generated_plans_manager
from app.services.outcome_allocator import (
    allocate_learning_outcomes_across_periods,
    extract_civic_tig_learning_outcomes,
)
from app.services.rag_generator import RAGLessonPlanGenerator
from app.services.timing_guardrail_engine import TimingGuardrailEngine
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


def test_information_sources_preserve_retrieved_names_and_pages_without_inventing_sources():
    sources = format_retrieved_source_references([
        {
            "content": "curriculum text",
            "metadata": {"source_file": "C:\\curriculum\\guide.pdf", "page": 8},
        },
        {
            "content": "more curriculum text",
            "metadata": {"source_file": "C:\\curriculum\\guide.pdf", "page": 9},
        },
        {
            "content": "textbook text",
            "metadata": {"source": "https://example.edu/textbook/8"},
        },
        {"content": "no source metadata", "metadata": {}},
        {"content": "generic placeholder", "source": "PDF"},
    ])

    assert sources == [
        "guide.pdf (pages 8, 9)",
        "https://example.edu/textbook/8",
    ]


def test_saved_plan_summaries_expose_period_metadata_and_lookup_prefers_period_one(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(generated_plans_manager, "GENERATED_PLANS_DIR", str(tmp_path))
    common_plan = {
        "grade": "Grade 8",
        "subject": "Civic Education",
        "competence_level": "8.1.1",
        "competence": "Public services",
        "lesson": "Public service investigation",
        "unique_learning_outcome": ["Investigates public services."],
        "lesson_development_steps": [],
    }
    generated_plans_manager.save_generated_plan(
        {**common_plan, "period_number": 2, "total_periods": 2,
         "selected_activity_title": "Group investigation"},
        "Grade_8_comp_8_1_1_p2.json",
    )
    generated_plans_manager.save_generated_plan(
        {**common_plan, "period_number": 1, "total_periods": 2,
         "selected_activity_title": "Guided observation"},
        "Grade_8_comp_8_1_1_p1.json",
    )

    summaries = generated_plans_manager.list_generated_plans()
    selected = generated_plans_manager.find_plan_by_competency(
        "8.1.1", "Grade 8", "Civic Education"
    )

    assert [(plan["period_number"], plan["total_periods"]) for plan in summaries] == [
        (1, 2),
        (2, 2),
    ]
    assert summaries[0]["selected_activity_title"] == "Guided observation"
    assert selected["plan"]["period_number"] == 1


def test_guardrail_repairs_missing_intro_and_homework_with_period_specific_five_minute_tasks():
    plan = make_plan()
    plan.the_entrance = ""
    plan.post_activity = "Take-home homework: find a service."

    repaired = TimingGuardrailEngine.enforce_invariants_and_inject_outcomes(
        plan=plan,
        verbatim_outcomes=[OFFICIAL_OUTCOMES[2]],
        requested_period=2,
        total_periods=3,
        lesson_topic="Public services investigation",
        selected_activity="Activity: Community Evidence Mapping",
    )

    assert repaired.entrance_duration_minutes == 5
    assert repaired.assignment_duration_minutes == 5
    assert "teacher" in repaired.the_entrance.casefold()
    assert "students" in repaired.the_entrance.casefold()
    assert "Community Evidence Mapping" in repaired.the_entrance
    assert "investigates information" in repaired.post_activity.casefold()
    assert "Community Evidence Mapping" in repaired.post_activity
    assert "5-minute" in repaired.post_activity.casefold()
    assert sum(step.time_minutes for step in repaired.lesson_development_steps) == 30


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


def test_fallback_uses_distinct_activities_for_competency_levels_in_same_period():
    level_one = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=["Identifies the public services."],
        current_period=1,
        total_periods=2,
        student_count=35,
        lesson_topic="Public services",
    )
    level_two = generate_fallback_options(
        competency_level="8.2.1",
        period_outcomes=["Explains the need of public services."],
        current_period=1,
        total_periods=2,
        student_count=35,
        lesson_topic="Public services",
    )

    level_one_activities = {
        option["title"].split(":")[0] for option in level_one["options"]
    }
    level_two_activities = {
        option["title"].split(":")[0] for option in level_two["options"]
    }

    assert len(level_one_activities) == 3
    assert len(level_two_activities) == 3
    assert level_one_activities.isdisjoint(level_two_activities)


def test_activity_prompt_requires_competency_specific_cross_level_activities():
    prompt = build_period_options_prompt(
        competency_level="8.1.2",
        period_outcomes=["Explains the need of public services."],
        current_period=1,
        total_periods=2,
        student_count=35,
        lesson_topic="Public services",
        grade_level="Grade 8",
    )

    assert "Do not generate a generic activity set that could be reused" in prompt
    assert "these activities must be different from activities generated for every other competency level" in prompt
    assert "Explains the need of public services." in prompt


def test_llm_activity_repeats_are_replaced_to_keep_period_options_distinct():
    generator = RAGLessonPlanGenerator.__new__(RAGLessonPlanGenerator)
    generator.model_name = "test-model"
    generator.ollama_url = "http://localhost"
    generator.retriever = Mock()
    generator.retriever.retrieve_tig_and_textbook_for_level.return_value = {
        "tig_guidelines": [{"content": "Retrieved curriculum context"}],
    }
    llm_options = [
        {
            "id": "option_1",
            "title": "Used activity",
            "pedagogy_type": "Inquiry",
            "description": "Repeats a prior activity.",
            "student_grouping": "Pairs",
            "creative_assessment_preview": "Exit ticket",
        },
        {
            "id": "option_2",
            "title": "Fresh activity one",
            "pedagogy_type": "Simulation",
            "description": "A new activity.",
            "student_grouping": "Pairs",
            "creative_assessment_preview": "Exit ticket",
        },
        {
            "id": "option_3",
            "title": "Fresh activity two",
            "pedagogy_type": "Design",
            "description": "Another new activity.",
            "student_grouping": "Pairs",
            "creative_assessment_preview": "Exit ticket",
        },
    ]
    llm_response = Mock()
    llm_response.json.return_value = {"response": json.dumps({"options": llm_options})}

    with patch(
        "app.services.rag_generator.extract_civic_tig_learning_outcomes",
        return_value=OFFICIAL_OUTCOMES,
    ), patch(
        "app.services.rag_generator.requests.post",
        return_value=llm_response,
    ):
        result = generator.generate_activity_options(
            competency_level="8.1.1",
            periods=1,
            requested_period=1,
            previous_activities=["Used activity"],
        )

    assert len(result["options"]) == 3
    titles = {option["title"] for option in result["options"]}
    assert len(titles) == 3
    assert "Used activity" not in titles
    assert {"Fresh activity one", "Fresh activity two"} <= titles


def test_activity_options_restore_the_same_saved_outcomes_as_final_plan_generation():
    generator = RAGLessonPlanGenerator.__new__(RAGLessonPlanGenerator)
    generator.model_name = "test-model"
    generator.ollama_url = "http://localhost"
    generator.retriever = Mock()
    generator.retriever.retrieve_tig_and_textbook_for_level.return_value = {
        "tig_guidelines": [{"content": "Retrieved curriculum context"}],
    }
    saved_allocation = {
        1: [OFFICIAL_OUTCOMES[4]],
        2: [OFFICIAL_OUTCOMES[2]],
        3: [OFFICIAL_OUTCOMES[0], OFFICIAL_OUTCOMES[1], OFFICIAL_OUTCOMES[3]],
    }
    llm_options = [
        {
            "id": f"option_{index}",
            "title": f"Period two activity {index}",
            "pedagogy_type": "Inquiry",
            "description": "A period-specific investigation.",
            "student_grouping": "Pairs",
            "creative_assessment_preview": "Exit ticket",
        }
        for index in range(1, 4)
    ]
    llm_response = Mock()
    llm_response.json.return_value = {"response": json.dumps({"options": llm_options})}

    with patch(
        "app.services.rag_generator.extract_civic_tig_learning_outcomes",
        return_value=OFFICIAL_OUTCOMES,
    ), patch(
        "app.services.rag_generator.get_competency_period_plans",
        return_value={
            period: {
                "total_periods": 3,
                "outcome_allocation": {
                    str(saved_period): outcomes
                    for saved_period, outcomes in saved_allocation.items()
                },
            }
            for period in range(1, 4)
        },
    ), patch(
        "app.services.rag_generator.requests.post",
        return_value=llm_response,
    ) as post:
        result = generator.generate_activity_options(
            competency_level="8.1.1",
            periods=3,
            requested_period=2,
            lesson_topic="Public services",
        )

    expected_outcomes = saved_allocation[2]
    assert all(
        option["learning_outcomes_addressed"] == expected_outcomes
        for option in result["options"]
    )
    prompt = post.call_args.kwargs["json"]["prompt"]
    assert expected_outcomes[0] in prompt
    assert OFFICIAL_OUTCOMES[4] not in prompt


def test_fallback_uses_only_available_resources_and_adapts_non_outdoor_setting():
    result = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=[OFFICIAL_OUTCOMES[0]],
        current_period=1,
        total_periods=2,
        student_count=48,
        lesson_topic="Public services",
        classroom_environment="Standard Classroom",
        accessible_resources=["Blackboard"],
    )

    for option in result["options"]:
        assert option["required_materials"] == ["Blackboard"]
        assert "48 students" in option["teacher_facilitation_summary"]
        assert "9 teams" in option["teacher_facilitation_summary"]
    assert not any(
        "School-Ground Walk" in option["title"]
        or "Field Audit" in option["title"]
        for option in result["options"]
    )


def make_service():
    with patch("app.services.lesson_plan_service.RAGLessonPlanGenerator"), patch(
        "app.services.lesson_plan_service.chromadb.PersistentClient"
    ):
        service = LessonPlanMlService()
    service.rag_engine.retriever.retrieve_tig_and_textbook_for_level.return_value = {
        "tig_guidelines": [{
            "content": "Official curriculum outcomes",
            "source": "Civic_Education_Grade_8_Teacher_Guide.pdf",
            "metadata": {"page": 4},
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
            topic_query="Local public services",
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
    assert (
        service.rag_engine.generate_activity_options.call_args.kwargs["lesson_topic"]
        == "Local public services"
    )


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
                selected_activity_title="Community service mapping activity",
                activity_options=[
                    {
                        "id": "option_1",
                        "title": "Community service mapping activity",
                        "pedagogy_type": "Mapping",
                        "description": "Students map local services.",
                        "student_grouping": "Pairs",
                        "required_materials": ["Notebooks"],
                        "creative_assessment_preview": "Exit ticket",
                    }
                ],
            )
        )

    assert len(result.lesson_plans) == 1
    assert result.lesson_plan.selected_activity_title == "Community service mapping activity"
    assert len(service.rag_engine.generate_lesson_plan.call_args_list) == 1
    assert service.rag_engine.generate_lesson_plan.call_args.kwargs["current_period"] == 2
    assert service.rag_engine.generate_lesson_plan.call_args.kwargs["query"] == (
        "Investigates information on the beginning and progress of public services: "
        "Community service mapping activity"
    )
    assert result.lesson_plan.lesson == service.rag_engine.generate_lesson_plan.call_args.kwargs["query"]
    assert result.lesson_plan.period_number == 2
    assert result.lesson_plan.total_periods == 3
    assert result.lesson_plan.activity_options[0]["title"] == "Community service mapping activity"
    assert result.lesson_plan.selected_activity == "Community service mapping"
    assert service.rag_engine.generate_lesson_plan.call_args.kwargs["retrieved_outcomes"] == [
        OFFICIAL_OUTCOMES[2]
    ]
    saved_json = save_plan.call_args.args[0]
    assert saved_json["period_number"] == 2
    assert saved_json["total_periods"] == 3
    assert saved_json["selected_activity"] == "Community service mapping"
    assert saved_json["selected_activity_title"] == "Community service mapping activity"
    assert saved_json["lesson"] == service.rag_engine.generate_lesson_plan.call_args.kwargs["query"]
    assert saved_json["activity_options"][0]["title"] == "Community service mapping activity"
    assert saved_json["period_number"] == 2
    assert saved_json["total_periods"] == 3
    assert saved_json["entrance_duration_minutes"] == 5
    assert saved_json["assignment_duration_minutes"] == 5
    assert saved_json["outcome_allocation"] == saved_allocation
    assert saved_json["grade"] == "Grade 8"
    assert saved_json["the_entrance"] == "Students discuss a local service they use."
    assert saved_json["assessment_and_feedback_whole_lesson"] == "Students complete a short exit quiz."
    assert saved_json["information_sources"] == [
        "Civic_Education_Grade_8_Teacher_Guide.pdf (page 4)",
        "https://api.learn.kandy.lk/textbook/8.1.1",
    ]
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
