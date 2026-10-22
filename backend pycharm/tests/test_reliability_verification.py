"""
Verification Test Suite covering Requirements 16 & 17 (Tests A through H).
Directly tests:
- Test A: Multiple Periods (4 periods, 3 distinct options/period, selection controls plan)
- Test B: Different Competency Levels (relevance, no indiscriminate reuse)
- Test C: Different Student Counts (small class vs large class logistics & grouping)
- Test D: Custom Teacher Activity (Mode B preservation in website & JSON)
- Test E: Introduction & Assignment (5m introduction + 5m in-class assignment + 30m development)
- Test F: JSON Consistency (serialization fidelity, all fields match)
- Test G: Saving and Viewing (period-wise lookup, all_period_plans retrieval)
- Test H: Regression Testing (Science subject and Classic Generator intact)
"""

import json
import pytest
from unittest.mock import Mock, patch

from app.schemas.lesson_plan_schema_dto import (
    LearnLessonPlanDto,
    LessonDevelopmentStepDto,
    LessonPlanSchemaDto,
)
from app.services.activity_options_engine import (
    generate_fallback_options,
)
from app.services.grouping_logistics_engine import (
    GroupingLogisticsEngine,
)
from app.services.i_lesson_plan_service import (
    LessonPlanGenerateRequest,
)
from app.services.lesson_plan_service import (
    LessonPlanMlService,
)
from app.services.outcome_allocator import (
    allocate_learning_outcomes_across_periods,
)
from app.services.timing_guardrail_engine import (
    TimingGuardrailEngine,
)
from app.services import generated_plans_manager


OFFICIAL_OUTCOMES_8_1_1 = [
    "Identifies the public services.",
    "Explains the need of public services.",
    "Investigates information on the beginning and progress of public services.",
    "Presents views appreciating the importance of public services of the times.",
    "Explains the common features related to public services.",
]

OFFICIAL_OUTCOMES_8_4_2 = [
    "Identifies fundamental human rights recognized in Sri Lanka.",
    "Explains the responsibilities associated with fundamental rights.",
    "Demonstrates respect for diversity and the rights of others.",
]


def make_mock_plan(
    competency: str = "8.1.1",
    period: int = 1,
    total_periods: int = 4,
    activity_title: str = "Inquiry Activity",
    outcomes: list = None
):
    outcomes = outcomes or [OFFICIAL_OUTCOMES_8_1_1[0]]
    return LessonPlanSchemaDto(
        grade="Grade 8",
        subject="Civic Education",
        time_allocation=f"40 Minutes (Period {period} of {total_periods})",
        competence="Democratic Governance",
        competence_level=competency,
        lesson=f"Public Services ({activity_title})",
        unique_learning_outcome=outcomes,
        the_entrance="5-minute introduction: The teacher poses a real-world civic prompt and students discuss in pairs.",
        lesson_development_steps=[
            LessonDevelopmentStepDto(
                step_number=1,
                time_minutes=15,
                learning_teaching_method="Guided Inquiry",
                learning_teaching_aids="Task Cards",
                teacher_activities="Organizes teams and guides investigative tasks.",
                student_activities="Collaborate in assigned roles to analyze evidence.",
                assessment_and_feedback="Observes team dialogue and clarifies instructions."
            ),
            LessonDevelopmentStepDto(
                step_number=2,
                time_minutes=15,
                learning_teaching_method="Plenary Discussion",
                learning_teaching_aids="Blackboard",
                teacher_activities="Facilitates group presentations and highlights key insights.",
                student_activities="Present team findings and record feedback.",
                assessment_and_feedback="Provides formative reinforcement."
            )
        ],
        summary="Synthesizes core student findings and civic values.",
        assessment_and_feedback_whole_lesson="5-minute rapid formative exit check.",
        post_activity=f"5-minute in-class assignment: Each student writes an exit response on {outcomes[0]}.",
        period_number=period,
        total_periods=total_periods,
        selected_activity_title=activity_title,
    )


# =============================================================================
# TEST A: MULTIPLE PERIODS (4 Periods, 3 distinct options each, selection controls plan)
# =============================================================================
def test_test_a_multiple_periods_independent_options_and_selection():
    """Verify 4 periods produce 3 distinct options per period and selection controls plan."""
    previous_activities = []
    period_options_map = {}

    for period in range(1, 5):
        opts = generate_fallback_options(
            competency_level="8.1.1",
            period_outcomes=[OFFICIAL_OUTCOMES_8_1_1[min(period - 1, len(OFFICIAL_OUTCOMES_8_1_1) - 1)]],
            current_period=period,
            total_periods=4,
            student_count=35,
            lesson_topic="Public services",
            previous_activities=previous_activities,
        )
        options = opts["options"]
        assert len(options) == 3, f"Period {period} must have exactly 3 activity options"

        # Check options differ meaningfully from earlier periods
        titles = [o["title"] for o in options]
        for t in titles:
            assert t not in previous_activities, f"Option '{t}' was repeated in Period {period}"

        # Select the 1st option for this period
        chosen = titles[0]
        previous_activities.append(chosen)
        period_options_map[period] = (chosen, options)

    assert len(previous_activities) == 4
    # All 4 selected activities across periods are unique
    assert len(set(previous_activities)) == 4


# =============================================================================
# TEST B: DIFFERENT COMPETENCY LEVELS (Relevance, no indiscriminate reuse)
# =============================================================================
def test_test_b_different_competency_levels_produce_aligned_activities():
    """Verify activities differ across different competency levels."""
    opts_811 = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=OFFICIAL_OUTCOMES_8_1_1[:2],
        current_period=1,
        total_periods=2,
        student_count=35,
        lesson_topic="Public services in Sri Lanka",
    )
    opts_842 = generate_fallback_options(
        competency_level="8.4.2",
        period_outcomes=OFFICIAL_OUTCOMES_8_4_2[:2],
        current_period=1,
        total_periods=2,
        student_count=35,
        lesson_topic="Fundamental human rights",
    )

    titles_811 = {o["title"].casefold() for o in opts_811["options"]}
    titles_842 = {o["title"].casefold() for o in opts_842["options"]}

    # No identical titles reused indiscriminately across different competencies
    assert len(titles_811.intersection(titles_842)) == 0
    # Outcomes are strictly bound to their respective options
    for opt in opts_811["options"]:
        assert opt["learning_outcomes_addressed"] == OFFICIAL_OUTCOMES_8_1_1[:2]
    for opt in opts_842["options"]:
        assert opt["learning_outcomes_addressed"] == OFFICIAL_OUTCOMES_8_4_2[:2]


# =============================================================================
# TEST C: DIFFERENT STUDENT COUNTS (Small class vs Large class logistics)
# =============================================================================
def test_test_c_student_count_influences_activity_generation_and_roles():
    """Verify group organization and student participation adapt to class size."""
    small_class = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=[OFFICIAL_OUTCOMES_8_1_1[0]],
        current_period=1,
        total_periods=1,
        student_count=12,  # Small class
        lesson_topic="Public services",
    )
    large_class = generate_fallback_options(
        competency_level="8.1.1",
        period_outcomes=[OFFICIAL_OUTCOMES_8_1_1[0]],
        current_period=1,
        total_periods=1,
        student_count=60,  # Large class
        lesson_topic="Public services",
    )

    small_grouping = small_class["options"][0]["student_grouping"]
    large_grouping = large_class["options"][0]["student_grouping"]

    # Grouping string and counts must differ appropriately
    assert small_grouping != large_grouping
    assert "12" in small_grouping or "triad" in small_grouping.casefold() or "pair" in small_grouping.casefold() or "group" in small_grouping.casefold()
    assert "60" in large_grouping or "team" in large_grouping.casefold() or "group" in large_grouping.casefold()

    # Small class participation notes emphasize intimate active teams
    assert "small class" in small_class["options"][0]["student_action_summary"].casefold()
    # Large class emphasizes assigned rotating roles to eliminate bystanders
    assert "zero passive bystanders" in large_class["options"][0]["student_action_summary"].casefold()


# =============================================================================
# TEST D: CUSTOM TEACHER ACTIVITY (Mode B preserved in website & JSON)
# =============================================================================
def test_test_d_custom_teacher_activity_preservation():
    """Verify custom teacher activity controls the lesson plan and appears in JSON."""
    custom_idea = "Students conduct an investigative interview with the school principal regarding school water services."
    plan = make_mock_plan(
        activity_title=f"Teacher approach: {custom_idea}"
    )
    plan.custom_teacher_activity = custom_idea
    plan.selected_activity = custom_idea

    repaired = TimingGuardrailEngine.enforce_invariants_and_inject_outcomes(
        plan=plan,
        verbatim_outcomes=[OFFICIAL_OUTCOMES_8_1_1[0]],
        requested_period=1,
        total_periods=1,
        lesson_topic="School Water Public Services",
        selected_activity=custom_idea,
    )

    assert repaired.custom_teacher_activity == custom_idea
    assert custom_idea in repaired.selected_activity
    # Both the entrance and assignment reference the custom activity
    assert "interview" in repaired.the_entrance.casefold() or "water" in repaired.the_entrance.casefold()

    # Verify JSON serialization includes custom_teacher_activity
    serialized = json.loads(repaired.model_dump_json())
    assert serialized["custom_teacher_activity"] == custom_idea
    assert serialized["selected_activity"] == custom_idea


# =============================================================================
# TEST E: INTRODUCTION AND ASSIGNMENT (5m introduction + 5m assignment + 30m development)
# =============================================================================
def test_test_e_introduction_and_assignment_5m_invariants():
    """Verify introduction is 5m, in-class assignment is 5m, development steps sum to 30m."""
    plan = make_mock_plan()
    plan.the_entrance = "Students discuss a service."  # Missing 5m phrasing and teacher/student structure
    plan.post_activity = "Take-home homework: find a service."  # Homework is disallowed

    repaired = TimingGuardrailEngine.enforce_invariants_and_inject_outcomes(
        plan=plan,
        verbatim_outcomes=[OFFICIAL_OUTCOMES_8_1_1[1]],
        requested_period=1,
        total_periods=2,
        lesson_topic="Explains the need of public services",
        selected_activity="Mock Council Roleplay",
    )

    # 1. Introduction is 5 minutes with teacher and student actions
    assert "5-minute" in repaired.the_entrance.casefold()
    assert "teacher" in repaired.the_entrance.casefold()
    assert "students" in repaired.the_entrance.casefold()
    assert repaired.entrance_duration_minutes == 5

    # 2. Assignment is 5 minutes, in-class, not homework
    assert "5-minute in-class assignment" in repaired.post_activity.casefold()
    assert "homework" not in repaired.post_activity.casefold()
    assert repaired.assignment_duration_minutes == 5

    # 3. Development steps strictly sum to exactly 30 minutes
    dev_time = sum(s.time_minutes for s in repaired.lesson_development_steps)
    assert dev_time == 30


# =============================================================================
# TEST F: JSON CONSISTENCY (All fields serialized and match)
# =============================================================================
def test_test_f_json_consistency():
    """Verify JSON output contains all required fields without dropping."""
    plan = make_mock_plan(activity_title="Collaborative Inquiry Jigsaw")
    plan.period_number = 2
    plan.total_periods = 3
    plan.selected_activity = "Station Jigsaw on Public Services"
    plan.information_sources = ["civic_grade_8_tig.pdf (page 12)"]
    plan.attachments = ["Task Card A", "Observation Sheet"]

    dumped_str = plan.model_dump_json()
    parsed = json.loads(dumped_str)

    required_fields = [
        "grade", "subject", "time_allocation", "competence", "competence_level",
        "lesson", "unique_learning_outcome", "the_entrance", "lesson_development_steps",
        "summary", "assessment_and_feedback_whole_lesson", "post_activity",
        "period_number", "total_periods", "selected_activity_title",
        "information_sources", "attachments"
    ]
    for field in required_fields:
        assert field in parsed, f"Field '{field}' missing from serialized JSON"

    assert parsed["period_number"] == 2
    assert parsed["total_periods"] == 3
    assert parsed["selected_activity_title"] == "Collaborative Inquiry Jigsaw"
    assert parsed["information_sources"] == ["civic_grade_8_tig.pdf (page 12)"]


# =============================================================================
# TEST G: SAVING AND VIEWING (Multi-period lookup and persistence)
# =============================================================================
def test_test_g_saving_and_viewing_multi_period_plans(tmp_path, monkeypatch):
    """Verify saved period plans are properly ordered and all_period_plans returned."""
    monkeypatch.setattr(generated_plans_manager, "GENERATED_PLANS_DIR", str(tmp_path))

    for p in range(1, 4):
        plan_data = make_mock_plan(period=p, total_periods=3, activity_title=f"Activity {p}").model_dump()
        generated_plans_manager.save_generated_plan(
            plan_data,
            f"Grade_8_comp_8_1_1_p{p}.json"
        )

    summaries = generated_plans_manager.list_generated_plans()
    assert len(summaries) == 3

    # find_plan_by_competency returns Period 1 as primary and attaches all 3 period plans
    result = generated_plans_manager.find_plan_by_competency("8.1.1", "Grade 8", "Civic Education")
    assert result is not None
    assert result["plan"]["period_number"] == 1
    assert "all_period_plans" in result
    assert len(result["all_period_plans"]) == 3
    assert [p["period_number"] for p in result["all_period_plans"]] == [1, 2, 3]


# =============================================================================
# TEST H: REGRESSION TESTING (Science and Classic Generator intact)
# =============================================================================
@pytest.mark.asyncio
async def test_test_h_regression_science_pipeline_unaffected():
    """Verify Science subject passes cleanly through legacy pipeline without Civic guardrails."""
    service = LessonPlanMlService()
    mock_science_plan = LessonPlanSchemaDto(
        grade="Grade 7",
        subject="Science",
        time_allocation="80 Minutes (2 Periods)",
        competence="Biological Systems",
        competence_level="7.1",
        lesson="Plant and Animal Cells",
        unique_learning_outcome=["Identifies plant cell structures."],
        the_entrance="Teacher displays microscope slide.",
        lesson_development_steps=[
            LessonDevelopmentStepDto(
                step_number=1,
                time_minutes=15,
                learning_teaching_method="Practical Work",
                learning_teaching_aids="Microscope",
                teacher_activities="Demonstrates slide preparation.",
                student_activities="Observe onion epidermis cells.",
                assessment_and_feedback="Checks slide focus."
            ),
            LessonDevelopmentStepDto(
                step_number=2,
                time_minutes=15,
                learning_teaching_method="Diagram Drawing",
                learning_teaching_aids="Drawing book",
                teacher_activities="Guides labeling.",
                student_activities="Draw and label cell wall and nucleus.",
                assessment_and_feedback="Reviews diagrams."
            )
        ],
        summary="Summarizes cell structure differences.",
        assessment_and_feedback_whole_lesson="Formative check on cell diagrams.",
        post_activity="Review textbook cell diagrams.",
    )

    with patch.object(service.rag_engine, "generate_lesson_plan", return_value=mock_science_plan), \
         patch.object(service.rag_engine.retriever, "retrieve_tig_and_textbook_for_level", return_value={"tig_guidelines": [], "textbook_paragraphs": []}):

        req = LessonPlanGenerateRequest(
            query="Plant and Animal Cells",
            competency_level="7.1",
            grade_level="Grade 7",
            subject="Science",
            periods=2,
        )
        resp = await service.generate_lesson_plan_async(req)

        assert resp.lesson_plan.subject == "Science"
        assert resp.lesson_plan.grade == "Grade 7"
        assert resp.lesson_plan.competence_level == "7.1"
        assert len(resp.lesson_plans) >= 1
