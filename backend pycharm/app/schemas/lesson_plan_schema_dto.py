from typing import Any, Dict, List, Optional
import re
from pydantic import BaseModel, Field, model_validator


class LessonDevelopmentStepDto(BaseModel):
    step_number: int = Field(..., description="Step sequence number (1, 2, 3...)")
    teacher_activities: str = Field(..., description="Teacher facilitation and scaffolding actions based on TIG")
    student_activities: str = Field(..., description="Active student investigations, discussions, and presentations")
    learning_teaching_method: str = Field(..., description="e.g., Guided Inquiry, Cooperative Group Work, Simulation, Jigsaw")
    learning_teaching_aids: str = Field(..., description="Instructional materials used in this step (task cards, sheets, board)")
    assessment_and_feedback: str = Field(
        default="",
        description="Legacy formative checks field; the final assessment is in the lesson closure."
    )
    time_minutes: int = Field(default=10, description="Step duration in minutes (5-minute multiples, sum must equal 30)")
    other: Optional[str] = Field(default="", description="Blackboard layout, grouping remarks, or safety notes")


class LessonPlanSchemaDto(BaseModel):
    grade: str = Field(..., description="Target school grade level (e.g., Grade 8)")
    subject: str = Field(default="Civic Education", description="Academic subject area")
    time_allocation: str = Field(..., description="e.g., '40 Minutes (Period 1 of 2)'")
    competence: str = Field(..., description="Broad competency statement from official TIG")
    competence_level: str = Field(..., description="Competency level code and statement (e.g., 8.1.1)")
    lesson: str = Field(..., description="Lesson title or theme")
    unique_learning_outcome: List[str] = Field(
        default_factory=list,
        description="Official syllabus outcomes assigned to this 40-minute period (programmatically injected)"
    )
    the_entrance: str = Field(
        ...,
        description="Five-minute introduction with teacher actions, student actions, and a link to the selected activity"
    )
    lesson_development_steps: List[LessonDevelopmentStepDto] = Field(
        ...,
        min_length=2,
        description="Sequential development steps dynamically generated to match the chosen activity and outcomes (Sum must strictly equal 30 Minutes)"
    )
    summary: str = Field(..., description="Consolidation and synthesis of key student findings")
    assessment_and_feedback_whole_lesson: str = Field(
        ...,
        description="Generated formative assessment in the final closure; the summary and assessment together take 5 minutes."
    )
    post_activity: str = Field(
        ...,
        description="A specific five-minute in-class assignment or concluding learning task aligned with this period"
    )
    information_sources: List[str] = Field(default_factory=list, description="Curriculum sources (NIE TIG, Pupil Textbook)")
    attachments: List[str] = Field(default_factory=list, description="Concrete titles of worksheets, cue cards, or checklists")
    entrance_duration_minutes: int = Field(default=5, ge=5, le=5)
    assignment_duration_minutes: int = Field(default=5, ge=5, le=5)
    period_number: Optional[int] = None
    total_periods: Optional[int] = None
    selected_activity: Optional[str] = None
    selected_activity_title: Optional[str] = Field(
        default=None,
        description="Title of the activity selected for this individual period"
    )
    custom_teacher_activity: Optional[str] = None
    activity_options: List[Dict[str, Any]] = Field(default_factory=list)
    outcome_allocation: Dict[str, List[str]] = Field(default_factory=dict)
    filename: Optional[str] = Field(default=None, description="Exact filename in generated_plans storage")

    @model_validator(mode="before")
    @classmethod
    def sanitize_and_coerce_inputs(cls, data: Any) -> Any:
        """
        Robustly coerces LLM output variations (string arrays, string vs list, alternative keys)
        so that Ollama, Gemini, or OpenAI generations never fail Pydantic schema validation.
        """
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # 1. unique_learning_outcome: must be List[str]
        ulo = d.get("unique_learning_outcome")
        if ulo is None:
            d["unique_learning_outcome"] = []
        elif isinstance(ulo, str):
            d["unique_learning_outcome"] = [s.strip() for s in ulo.split("\n") if s.strip()] or [ulo.strip()]
        elif isinstance(ulo, list):
            d["unique_learning_outcome"] = [str(x).strip() for x in ulo if str(x).strip()]

        # 2. information_sources: must be List[str]
        info = d.get("information_sources")
        if info is None:
            d["information_sources"] = []
        elif isinstance(info, str):
            d["information_sources"] = [s.strip() for s in re.split(r"[\n,;]+", info) if s.strip()] or [info.strip()]
        elif isinstance(info, list):
            d["information_sources"] = [str(x).strip() for x in info if str(x).strip()]

        # 3. attachments: must be List[str]
        att = d.get("attachments")
        if att is None:
            d["attachments"] = []
        elif isinstance(att, str):
            d["attachments"] = [s.strip() for s in re.split(r"[\n,;]+", att) if s.strip()] or [att.strip()]
        elif isinstance(att, list):
            d["attachments"] = [str(x).strip() for x in att if str(x).strip()]

        # 4. activity_options: must be List[Dict[str, Any]]
        act = d.get("activity_options")
        if act is None:
            d["activity_options"] = []
        elif isinstance(act, list):
            clean_act = []
            for item in act:
                if isinstance(item, dict):
                    clean_act.append(item)
                elif isinstance(item, str) and item.strip():
                    clean_act.append({
                        "title": item.strip(),
                        "activity_strategy": item.strip(),
                        "description": item.strip()
                    })
            d["activity_options"] = clean_act
        elif isinstance(act, dict):
            d["activity_options"] = [act]
        elif isinstance(act, str) and act.strip():
            d["activity_options"] = [{"title": act.strip(), "description": act.strip()}]
        else:
            d["activity_options"] = []

        # 5. outcome_allocation: must be Dict[str, List[str]]
        oa = d.get("outcome_allocation")
        if oa is None:
            d["outcome_allocation"] = {}
        elif isinstance(oa, dict):
            clean_oa = {}
            for k, v in oa.items():
                if isinstance(v, list):
                    clean_oa[str(k)] = [str(x).strip() for x in v if str(x).strip()]
                elif isinstance(v, str):
                    clean_oa[str(k)] = [v.strip()] if v.strip() else []
                else:
                    clean_oa[str(k)] = [str(v)]
            d["outcome_allocation"] = clean_oa
        elif isinstance(oa, list):
            d["outcome_allocation"] = {"period_1": [str(x) for x in oa]}
        elif isinstance(oa, str) and oa.strip():
            d["outcome_allocation"] = {"period_1": [oa.strip()]}
        else:
            d["outcome_allocation"] = {}

        # 5b. lesson_development_steps
        steps = d.get("lesson_development_steps")
        if not steps or not isinstance(steps, list):
            for k in ["steps", "development_steps", "activities", "procedures", "development", "learning_activities"]:
                if d.get(k) and isinstance(d[k], list) and len(d[k]) > 0:
                    steps = d[k]
                    break
        act_raw = str(d.get("selected_activity_title") or d.get("selected_activity") or "Collaborative Inquiry").splitlines()[0]
        act_clean = re.sub(r"^Activity:\s*", "", act_raw, flags=re.IGNORECASE).strip() or "Collaborative Inquiry"
        topic_clean = str(d.get("lesson") or d.get("query") or "Civic Principles").strip()

        clean_steps = []
        if isinstance(steps, list):
            for idx, s in enumerate(steps, 1):
                if hasattr(s, "model_dump"):
                    s = s.model_dump()
                elif hasattr(s, "dict"):
                    s = s.dict()
                if isinstance(s, dict):
                    clean_steps.append({
                        "step_number": s.get("step_number") or idx,
                        "teacher_activities": str(s.get("teacher_activities") or s.get("teacher") or s.get("facilitation") or f"Teacher facilitates student engagement in {act_clean} on '{topic_clean}'.").strip(),
                        "student_activities": str(s.get("student_activities") or s.get("students") or s.get("task") or f"Students collaborate in groups executing {act_clean} on '{topic_clean}'.").strip(),
                        "learning_teaching_method": str(s.get("learning_teaching_method") or s.get("method") or s.get("pedagogy") or f"{act_clean} Step {idx}").strip(),
                        "learning_teaching_aids": str(s.get("learning_teaching_aids") or s.get("aids") or s.get("materials") or f"Task materials and worksheets for {act_clean}").strip(),
                        "assessment_and_feedback": "",
                        "time_minutes": int(s.get("time_minutes") or s.get("duration") or 10),
                        "other": str(s.get("other") or "").strip()
                    })

        if not clean_steps:
            clean_steps = [
                {
                    "step_number": 1,
                    "teacher_activities": f"Teacher introduces the Sri Lankan real-world scenario for '{topic_clean}', clarifies objectives, and distributes task cards for {act_clean}.",
                    "student_activities": f"Students review task cards, assume collaborative group roles, and begin investigations for {act_clean}.",
                    "learning_teaching_method": f"Orientation & {act_clean} Setup",
                    "learning_teaching_aids": f"Task cards and scenario prompts for {act_clean}",
                    "assessment_and_feedback": "",
                    "time_minutes": 10,
                    "other": "Group formation"
                },
                {
                    "step_number": 2,
                    "teacher_activities": f"Teacher facilitates {act_clean}, circulates among groups, scaffolds student inquiries into '{topic_clean}', and monitors collaborative progress.",
                    "student_activities": f"Students actively execute {act_clean}, collaborating in assigned roles to analyze civic situations related to '{topic_clean}'.",
                    "learning_teaching_method": f"Collaborative Deep-Dive: {act_clean}",
                    "learning_teaching_aids": f"Activity worksheets, scenario briefs, chart paper, markers for {act_clean}",
                    "assessment_and_feedback": "",
                    "time_minutes": 10,
                    "other": "Active investigation"
                },
                {
                    "step_number": 3,
                    "teacher_activities": f"Teacher moderates group spokesperson presentations, facilitates constructive peer review, and synthesizes key discoveries regarding '{topic_clean}'.",
                    "student_activities": f"Group spokespersons present findings on '{topic_clean}'; peer teams evaluate presentations using criteria and note constructive feedback.",
                    "learning_teaching_method": f"Presentation & Synthesis of {act_clean}",
                    "learning_teaching_aids": f"Student presentation charts, whiteboard for {act_clean}",
                    "assessment_and_feedback": "",
                    "time_minutes": 10,
                    "other": "Plenary synthesis"
                }
            ]
        d["lesson_development_steps"] = clean_steps

        # 6. the_entrance
        if not d.get("the_entrance") or not str(d.get("the_entrance", "")).strip():
            for k in ["entrance", "introduction", "intro", "hook", "opening", "motivational_hook", "phase_1"]:
                if d.get(k) and str(d[k]).strip():
                    d["the_entrance"] = str(d[k]).strip()
                    break
            if not d.get("the_entrance") or not str(d.get("the_entrance", "")).strip():
                d["the_entrance"] = "5-minute introduction: Teacher presents everyday scenario and motivational hook; students discuss and connect prior knowledge."

        # 7. time_allocation
        if not d.get("time_allocation") or not str(d.get("time_allocation", "")).strip():
            for k in ["duration", "time", "time_slot", "timing", "allocation"]:
                if d.get(k) and str(d[k]).strip():
                    d["time_allocation"] = str(d[k]).strip()
                    break
            if not d.get("time_allocation") or not str(d.get("time_allocation", "")).strip():
                d["time_allocation"] = "40 Minutes (Period 1 of 1)"

        # 8. competence & competence_level
        if not d.get("competence") or not str(d.get("competence", "")).strip():
            for k in ["competency", "broad_competence", "standard", "goal"]:
                if d.get(k) and str(d[k]).strip():
                    d["competence"] = str(d[k]).strip()
                    break
            if not d.get("competence") or not str(d.get("competence", "")).strip():
                d["competence"] = "Democratic Governance and Civic Participation"

        if not d.get("competence_level") or not str(d.get("competence_level", "")).strip():
            for k in ["level", "competency_code", "competency_level"]:
                if d.get(k) and str(d[k]).strip():
                    d["competence_level"] = str(d[k]).strip()
                    break
            if not d.get("competence_level") or not str(d.get("competence_level", "")).strip():
                d["competence_level"] = "8.1.1"

        # 9. lesson
        if not d.get("lesson") or not str(d.get("lesson", "")).strip():
            for k in ["topic", "title", "lesson_title", "theme", "lesson_topic", "name"]:
                if d.get(k) and str(d[k]).strip():
                    d["lesson"] = str(d[k]).strip()
                    break
            if not d.get("lesson") or not str(d.get("lesson", "")).strip():
                d["lesson"] = "Civic Education Lesson Standard"

        # 10. grade & subject
        if not d.get("grade") or not str(d.get("grade", "")).strip():
            d["grade"] = str(d.get("grade_level") or "Grade 8").strip()
        if not d.get("subject") or not str(d.get("subject", "")).strip():
            d["subject"] = "Civic Education"

        # 11. summary
        if not d.get("summary") or not str(d.get("summary", "")).strip():
            for k in ["conclusion", "synthesis", "review", "recap"]:
                if d.get(k) and str(d[k]).strip():
                    d["summary"] = str(d[k]).strip()
                    break
            if not d.get("summary") or not str(d.get("summary", "")).strip():
                d["summary"] = "Teacher and students synthesize core findings, reinforcing key civic competencies and takeaways."

        # 12. assessment_and_feedback_whole_lesson
        if not d.get("assessment_and_feedback_whole_lesson") or not str(d.get("assessment_and_feedback_whole_lesson", "")).strip():
            for k in ["assessment", "evaluation", "feedback", "final_assessment", "closure_assessment"]:
                if d.get(k) and str(d[k]).strip():
                    d["assessment_and_feedback_whole_lesson"] = str(d[k]).strip()
                    break
            if not d.get("assessment_and_feedback_whole_lesson") or not str(d.get("assessment_and_feedback_whole_lesson", "")).strip():
                d["assessment_and_feedback_whole_lesson"] = "Formative exit ticket questioning: 3 students share real-life application examples."

        # 13. post_activity
        if not d.get("post_activity") or not str(d.get("post_activity", "")).strip():
            for k in ["assignment", "homework", "followup", "in_class_task", "extension"]:
                if d.get(k) and str(d[k]).strip():
                    d["post_activity"] = str(d[k]).strip()
                    break
            if not d.get("post_activity") or not str(d.get("post_activity", "")).strip():
                d["post_activity"] = "Five-minute in-class assignment: Each student writes two key responsibilities on their reflection sheet."

        # 14. entrance_duration_minutes & assignment_duration_minutes
        d["entrance_duration_minutes"] = 5
        d["assignment_duration_minutes"] = 5

        return d

    @model_validator(mode="after")
    def balance_strict_40_minute_pacing(self):
        """
        Enforces the Strict LEARN Kandy 40-Minute Period Architecture:
        - Entrance: Exactly 5 mins
        - Development Steps: Exactly 30 mins (Sum across all development steps)
        - Creative Assessment: Exactly 5 mins
        - Total Period Duration: 5 + 30 + 5 = 40 Minutes.
        """
        TARGET_DEV_MINUTES = 30

        # 1. Fallback: If development steps are missing, synthesize dynamic steps from the topic and activity
        if not self.lesson_development_steps:
            act_title = (self.selected_activity_title or self.selected_activity or "Collaborative Investigation").splitlines()[0]
            act_title = re.sub(r"^Activity:\s*", "", act_title, flags=re.IGNORECASE).strip() or "Collaborative Inquiry"
            topic_clean = self.lesson or "Civic Core Principles"
            self.lesson_development_steps = [
                LessonDevelopmentStepDto(
                    step_number=1,
                    teacher_activities=f"Teacher introduces the Sri Lankan real-world situation for '{topic_clean}', arranges student groups, and provides {act_title} task cards and role assignments.",
                    student_activities=f"Students arrange into collaborative groups, review inquiry prompts for {act_title}, assign group roles, and formulate investigative questions.",
                    learning_teaching_method=f"Orientation & {act_title} Launch",
                    learning_teaching_aids=f"Task cards for {act_title}, scenario sheets, chalkboard",
                    assessment_and_feedback="",
                    time_minutes=10,
                    other="Group formation"
                ),
                LessonDevelopmentStepDto(
                    step_number=2,
                    teacher_activities=f"Teacher actively circulates among student groups as facilitator, scaffolds inquiry into '{topic_clean}', and monitors dynamic execution of {act_title}.",
                    student_activities=f"Students actively collaborate in assigned roles to execute {act_title}, analyzing Sri Lankan community scenarios and co-creating group findings.",
                    learning_teaching_method=f"Collaborative Deep-Dive: {act_title}",
                    learning_teaching_aids=f"Activity worksheets, inquiry cards, chart paper, markers for {act_title}",
                    assessment_and_feedback="",
                    time_minutes=10,
                    other="Collaborative inquiry"
                ),
                LessonDevelopmentStepDto(
                    step_number=3,
                    teacher_activities=f"Teacher moderates student team presentations, facilitates constructive peer review, and synthesizes discoveries regarding '{topic_clean}'.",
                    student_activities=f"Group spokespersons present findings on '{topic_clean}'; peers evaluate solutions using criteria and note constructive feedback.",
                    learning_teaching_method=f"Spokesperson Presentation & Plenary Synthesis: {act_title}",
                    learning_teaching_aids=f"Student presentation posters, whiteboard for {act_title}",
                    assessment_and_feedback="",
                    time_minutes=10,
                    other="Plenary synthesis"
                )
            ]

        # 2. If only 1 step was generated, split it to ensure a complete developmental scaffold in clean multiples of 5
        if len(self.lesson_development_steps) == 1:
            orig = self.lesson_development_steps[0]
            act_title = (self.selected_activity_title or self.selected_activity or "Collaborative Investigation").splitlines()[0]
            act_title = re.sub(r"^Activity:\s*", "", act_title, flags=re.IGNORECASE).strip() or "Collaborative Inquiry"
            topic_clean = self.lesson or "Civic Principles"
            orig.step_number = 1
            orig.time_minutes = 10
            self.lesson_development_steps = [
                orig,
                LessonDevelopmentStepDto(
                    step_number=2,
                    teacher_activities=f"Teacher circulates as facilitator among groups executing {act_title}, scaffolding student inquiries into '{topic_clean}' with probing questions.",
                    student_activities=f"Students actively collaborate in assigned roles to execute {act_title}, analyzing real-world civic situations related to '{topic_clean}'.",
                    learning_teaching_method=f"Collaborative Deep-Dive: {act_title}",
                    learning_teaching_aids=f"Activity worksheets, problem scenarios, and collaboration materials for {act_title}",
                    assessment_and_feedback="",
                    time_minutes=10,
                    other="Collaborative deep-dive"
                ),
                LessonDevelopmentStepDto(
                    step_number=3,
                    teacher_activities=f"Teacher moderates student team presentations on '{topic_clean}', facilitates constructive peer critique, and synthesizes key insights from {act_title}.",
                    student_activities=f"Team spokespersons present findings on '{topic_clean}'; peer teams evaluate presentations against criteria and record constructive feedback.",
                    learning_teaching_method=f"Spokesperson Presentation & Peer Review: {act_title}",
                    learning_teaching_aids=f"Student presentation charts and whiteboard for {act_title}",
                    assessment_and_feedback="",
                    time_minutes=10,
                    other="Presentation synthesis"
                )
            ]

        # 3. Round all individual step durations to the nearest multiple of 5 (minimum 5 mins)
        for step in self.lesson_development_steps:
            step.assessment_and_feedback = ""
            raw_val = step.time_minutes
            rounded = round(raw_val / 5.0) * 5
            step.time_minutes = max(5, int(rounded))

        # 4. Calculate drift relative to the strict 30-minute development ceiling
        current_sum = sum(s.time_minutes for s in self.lesson_development_steps)
        drift = TARGET_DEV_MINUTES - current_sum

        # 5. Deterministically balance drift strictly in 5-minute increments
        if drift != 0:
            units = drift // 5
            direction = 5 if units > 0 else -5
            step_count = len(self.lesson_development_steps)

            for _ in range(abs(units)):
                if direction < 0:
                    # Negative drift: trim the longest step that is greater than 5 minutes
                    candidates = [i for i, s in enumerate(self.lesson_development_steps) if s.time_minutes > 5]
                    if candidates:
                        idx = max(candidates, key=lambda k: self.lesson_development_steps[k].time_minutes)
                        self.lesson_development_steps[idx].time_minutes += direction
                    else:
                        break
                else:
                    # Positive drift: expand the shortest step
                    idx = min(range(step_count), key=lambda k: self.lesson_development_steps[k].time_minutes)
                    self.lesson_development_steps[idx].time_minutes += direction

        # 6. Sequentially renumber step indices (1, 2, 3...)
        for idx, step in enumerate(self.lesson_development_steps, start=1):
            step.step_number = idx

        # 7. Strip forbidden URLs from competence_level and competence
        URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)
        if self.competence_level and URL_PATTERN.search(self.competence_level):
            code_match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", self.competence_level)
            self.competence_level = code_match.group(1) if code_match else "8.1.1"

        if self.competence and URL_PATTERN.search(self.competence):
            slug = re.sub(r"^https?://[^\s/]+/(?:competence/?)?", "", self.competence)
            cleaned_slug = slug.replace("-", " ").strip().title()
            self.competence = cleaned_slug if len(cleaned_slug) > 3 else "Curriculum Competency Standard"

        return self


# Backward-compatibility alias
LearnLessonPlanDto = LessonPlanSchemaDto
PeradeniyaLessonPlanDto = LessonPlanSchemaDto