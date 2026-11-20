# Comprehensive Developer Expansion Guidelines: Scaling to Civic Education (Grades 6, 7, 9) and Science (Grades 6–9)

## Executive Summary & Architectural Overview

This document serves as an exhaustive, step-by-step engineering roadmap for incoming developers looking to scale the **LEARN Practice Teaching Lesson Plan Engine** from its current reference implementation (**Civic Education - Grade 8**) to:
1. **Civic Education:** Grades 6, 7, and 9.
2. **Science:** Grades 6, 7, 8, and 9.

### Current Architectural Baseline
The system is built on a modular, guardrail-driven, student-centered RAG architecture:
* **Retrieval-Augmented Generation (RAG):** Hybrid vector search using ChromaDB, splitting Teacher Instructional Guides (TIG) and Student Textbooks.
* **Deterministic Outcome Allocation (`outcome_allocator.py`):** Extracts verbatim outcomes from TIG and maps them across sequential 40-minute periods using Bloom's cognitive weighting (Introduce → Develop → Practice → Assess).
* **Pedagogical Options Engine (`activity_options_engine.py`):** Suggests 3 distinct active-learning activity tracks with anti-repetition tracking across periods.
* **Grouping & Logistics Engine (`grouping_logistics_engine.py`):** Assigns structured small-group roles (Leader, Scribe, Timekeeper, Investigator, Spokesperson) to eliminate passive bystanders.
* **Subject & Grade Isolation (`subject_guard.py`):** Safeguards the pipeline so that only supported subjects and grades enter the creative multi-period pipeline.
* **Export Engine (`export_service.py`):** Generates publication-ready Microsoft Word (`.docx`) and Adobe PDF (`.pdf`) documents following the official Sri Lankan National Institute of Education (NIE) standard.

---

## PART 1: Expanding Civic Education to Grades 6, 7, and 9

Grade 8 Civic Education is fully functional. Expanding to Grades 6, 7, and 9 requires completing curriculum ingestion, age-appropriate pedagogical calibration, and regression validation.

### Step 1.1: Curriculum Assets Audit & Ingestion
Navigate to `backend pycharm/curriculum_data/` and verify the PDF assets:

| Grade | Required Documents | Current Status | Action Required |
| :--- | :--- | :--- | :--- |
| **Grade 6** | `grade_6_civic_teacher_guide.pdf`<br>`grade_6_civic_textbook.pdf` | Present in `curriculum_data/grade_6/` | Ingest into ChromaDB with metadata verification. |
| **Grade 7** | `grade_7_civic_teacher_guide.pdf`<br>`grade_7_civic_textbook.pdf` | Present in `curriculum_data/grade_7/` | Ingest into ChromaDB with metadata verification. |
| **Grade 9** | `grade_9_civic_teacher_guide.pdf`<br>`grade_9_civic_textbook.pdf` | `grade_9_civic_textbook.pdf` present.<br>**`grade_9_civic_teacher_guide.pdf` is MISSING.** | **Critical:** Obtain NIE Grade 9 Civic TIG PDF, place in `curriculum_data/grade_9/`, then ingest. |

#### Ingestion Execution Procedure:
1. Ensure all PDF files follow standard naming.
2. Execute the document chunking and ingestion pipeline:
   ```bash
   cd "backend pycharm"
   .\venv\Scripts\activate
   python app/ingestion/chunking_pipeline.py
   python app/ingestion/ingest_chroma.py
   ```
3. Verify metadata tagging in ChromaDB:
   Each chunk must contain:
   * `subject`: `"Civic Education"`
   * `grade`: `"Grade 6"` / `"Grade 7"` / `"Grade 9"`
   * `doc_type`: `"tig"` or `"textbook"`
   * `competency_level`: e.g. `"6.1.1"`, `"7.2.1"`, `"9.3.2"`

---

### Step 1.2: Age-Appropriate Pedagogy Tuning (`activity_options_engine.py`)

Civic Education in Grade 6 (ages 11–12) requires very different cognitive strategies than Grade 9 (ages 14–15). Modify `activity_options_engine.py` to support grade-tiered activity templates:

```
Grade 6 (Concrete & Experiential):
  ├── Track 1: Simple Roleplay & Daily Life Simulations (Home duties, classroom rules, road safety)
  ├── Track 2: Visual Scavenger Hunts & School Environment Audits
  └── Track 3: Picture Matching, Collage Making, Wall Charts

Grade 7 (Community & Local Systems):
  ├── Track 1: Village Touchpoints (Grama Niladhari desk, Post Office, Community Health Clinic)
  ├── Track 2: Cooperative Societies, Local Markets & Welfare Groups
  └── Track 3: Mini Case Dilemmas, Dual-Sector Matrices

Grade 8 (Current Reference):
  ├── Track 1: Pradeshiya Sabha / Municipal Council Simulations
  ├── Track 2: Public Service Audits & Progress Comparisons
  └── Track 3: Jigsaw Matrices, Citizen Charters, Cause-Effect Trees

Grade 9 (Abstract Governance & Constitutional Principles):
  ├── Track 1: Parliamentary Debates, Mock Supreme Court, Fundamental Rights Tribunals
  ├── Track 2: Constitutional Case Law Audits, Election Commission Simulations
  └── Track 3: Policy Drafting, Human Rights Advocacy Campaigns
```

**Developer Task in `activity_options_engine.py`:**
* Inspect `generate_pedagogical_activity_options(...)`.
* Add a `grade_level` parameter dispatch that selects age-tuned seed activity definitions rather than applying Grade 8 council simulations to Grade 6 students.

---

### Step 1.3: TIG Outcome Extraction Regex Validation (`outcome_allocator.py`)

Check whether NIE Grade 6, 7, and 9 Teacher Instructional Guides use the exact tabular formatting parsed by `extract_verbatim_tig_outcomes`:
1. Check competency headers in TIGs (e.g., "Competency 6.1:", "Competency Level 6.1.1:").
2. Ensure regex patterns in `outcome_allocator.py` match the outcome bullet syntax across all three grades.
3. Test extraction without running generation by writing a unit test:
   ```python
   # tests/test_civic_outcomes_all_grades.py
   from app.services.outcome_allocator import extract_verbatim_tig_outcomes
   # Verify that Grade 6, 7, and 9 sample TIG texts return clean string lists.
   ```

---

### Step 1.4: Period Clamping and Guardrails (`timing_guardrail_engine.py` & `subject_guard.py`)

1. In `backend pycharm/app/services/subject_guard.py`:
   * `ALLOWED_GRADES` already includes `{"grade 6", "grade 7", "grade 8", "grade 9"}`.
   * Verify `resolve_civic_grade(...)` correctly parses single digits (`"6"`, `"7"`, `"9"`) and prefix formats (`"6.1.1"` → `"Grade 6"`).
2. In `backend pycharm/app/services/timing_guardrail_engine.py`:
   * Verify that the allocated period counts match NIE syllabus guidelines for each grade (typically 1 to 4 periods per competency level in Civic Education).

---

## PART 2: Expanding the Engine to Science (Grades 6 to 9)

Expanding to Science is a major architectural milestone. Science pedagogy differs fundamentally from Civic Education: it requires **Inquiry-Based Learning**, the **5E Instructional Model**, **Predict-Observe-Explain (POE)**, and **Laboratory Safety Guardrails**.

### Step 2.1: Pedagogical Model Comparison

| Feature | Civic Education (Social Science) | Science (Natural & Physical Science) |
| :--- | :--- | :--- |
| **Dominant Model** | Roleplay, Simulation, Field Inquiry, Jigsaw | **5E Model:** Engage, Explore, Explain, Elaborate, Evaluate |
| **Core Classroom Tasks** | Discussion, Debate, Case Audit, Citizen Chart | **Experimentation, Apparatus Handling, Observation, Data Recording** |
| **Safety Dimension** | Minimal (psychosocial/respectful debate) | **Critical:** Chemical handling, heat, glassware, electrical hazards |
| **Group Roles** | Leader, Scribe, Timekeeper, Investigator, Spokesperson | **Material Handler, Chief Experimenter, Observation Recorder, Safety Officer, Presenter** |
| **Period Structures** | Typically single 40-minute periods | Single 40-minute periods or **80-minute double practical laboratory blocks** |

---

### Step 2.2: Curriculum Data Inventory for Science

Verify files in `backend pycharm/curriculum_data/`:
* `curriculum_data/grade_6/grade_6_science_teacher_guide.pdf` & `textbook.pdf`
* `curriculum_data/grade_7/grade_7_science_teacher_guide.pdf` & `textbook_1.pdf` & `textbook_2.pdf`
* `curriculum_data/grade_8/grade_8_science_teacher_guide.pdf` & `textbook_1.pdf` & `textbook_2.pdf`
* `curriculum_data/grade_9/grade_9_science_teacher_guide.pdf` & `textbook_1.pdf` & `textbook_2.pdf`

*(All required Science PDFs are already physically present in the repository).*

#### Handling Dual-Volume Textbooks (`textbook_1.pdf` & `textbook_2.pdf`):
In Sri Lanka, Science textbooks for Grades 7, 8, and 9 are split into Part 1 (Term 1 & 2) and Part 2 (Term 3).
* When chunking, ensure the metadata includes `volume: 1` or `volume: 2` and the specific Science `unit_number` (e.g., Unit 1: Plant Diversity, Unit 12: Electric Circuits).

---

### Step 2.3: Updating Subject Guard (`subject_guard.py`)

Currently, `subject_guard.py` enforces:
```python
ALLOWED_SUBJECT = "civic education"
```
To enable Science without breaking existing Civic Education flows, refactor to a multi-subject registry:

```python
# Refactored subject_guard.py architecture
SUPPORTED_SUBJECTS = {
    "civic education": {
        "allowed_grades": {"grade 6", "grade 7", "grade 8", "grade 9"},
        "max_periods": 4,
        "pedagogy_pipeline": "civic_student_centered",
    },
    "science": {
        "allowed_grades": {"grade 6", "grade 7", "grade 8", "grade 9"},
        "max_periods": 6, # Permits practical double periods
        "pedagogy_pipeline": "science_inquiry_5e",
    }
}

def is_creative_pipeline_enabled(subject: str, grade: str) -> bool:
    sub = (subject or "").strip().lower()
    grd = normalize_grade(grade or "")
    if sub in SUPPORTED_SUBJECTS:
        return grd.lower() in SUPPORTED_SUBJECTS[sub]["allowed_grades"]
    return False
```

---

### Step 2.4: Implementing Science Pedagogical Options Engine

Create or branch `science_activity_options_engine.py` (or extend `activity_options_engine.py` with subject dispatch) supporting three foundational Science tracks:

```
Science Pedagogical Tracks:
  ├── Track 1: Hands-on Laboratory Experiment (POE: Predict-Observe-Explain)
  │     ├── Apparatus setup, variable identification (control, independent, dependent)
  │     ├── Guided scientific observation and measurement tables
  │     └── Drawing causal conclusions from empirical data
  │
  ├── Track 2: Phenomenon Simulation & Scientific Model Building
  │     ├── 3D ball-and-stick molecular models / Cell organelle crafting
  │     ├── Mechanical pulley/circuit mockups using everyday low-cost materials
  │     └── Microscopic slide preparation or biological classification keys
  │
  └── Track 3: Concept Dissection & Scientific Problem-Solving
        ├── Data analysis graphs (rate of reaction, speed-time, temperature curves)
        ├── Flowcharts of biological systems (respiration, digestive paths)
        └── Environmental audit / Field specimen sampling
```

#### Dedicated Science Grouping Roles:
Replace generic roles with science laboratory roles:
1. **Apparatus & Material Handler:** Responsible for safely collecting and returning glassware, reagents, and measuring tools.
2. **Safety Officer / Monitor:** Verifies lab rules (wearing safety goggles, handling burners/acids with tongs, managing disposal).
3. **Chief Experimenter:** Directly manipulates the experiment apparatus under teacher guidance.
4. **Observation Scribe:** Records quantitative data (temperatures, times, measurements) and qualitative changes (color shifts, gas bubbles).
5. **Data Analyst / Presenter:** Interprets findings against textbook theories and presents results to the class.

---

### Step 2.5: Science Cognitive Verbs & Outcome Allocation

Science learning outcomes use distinct action verbs:
* **Level 1 (Recall):** `names`, `lists`, `identifies`, `defines`
* **Level 2 (Comprehend):** `describes`, `explains`, `classifies`, `illustrates`
* **Level 3 (Apply/Investigate):** `conducts an experiment`, `measures`, `assembles apparatus`, `records observations`, `constructs circuits`
* **Level 4 (Analyze/Evaluate):** `hypothesizes`, `draws conclusions`, `deduces`, `analyzes errors`, `formulates scientific models`

Update `outcome_allocator.py` or create a specialized `science_outcome_allocator.py` that maps:
* Period 1: Theoretical engagement + Apparatus orientation (Introduce).
* Period 2: Hands-on experimentation + Data collection (Explore & Explain).
* Period 3: Analysis of findings + Real-world application (Elaborate & Evaluate).

---

### Step 2.6: Science Prompt Templates (`prompt_templates.py`)

Add dedicated prompt templates for Science lesson planning:
1. **Safety Precautions Section:** A mandatory field in every science plan listing potential hazards and prevention steps.
2. **Apparatus & Reagents Checklist:** Formatted checklist of standard school lab materials vs. low-cost alternatives (e.g., using lime juice if dilute acid is unavailable).
3. **Observation Table Template:** Explicit tabular schema for students to record measurements and visual phenomena during Step 2.

Example prompt template addition in `prompt_templates.py`:
```python
SCIENCE_LESSON_PLAN_DEVELOPMENT_PROMPT = """
You are an expert Sri Lankan Science Teacher educator adhering strictly to the NIE Science Curriculum.
Generate the 30-minute Lesson Development Steps using the 5E Instructional Model (Engage, Explore, Explain, Elaborate, Evaluate).

MANDATORY SCIENCE REQUIREMENTS:
1. Teacher Activities MUST include:
   - Specific laboratory safety warnings and reagent handling tips.
   - Demonstration steps with exact apparatus instructions.
   - Formative scaffolding questions prompting students to explain 'WHY' a phenomenon occurs.
2. Student Activities MUST include:
   - Active manipulation of apparatus in 5 designated roles (Apparatus Handler, Safety Officer, Chief Experimenter, Observation Scribe, Presenter).
   - Recording observations in a structured 2-column or 3-column data table.
3. Teaching Aids MUST explicitly name scientific apparatus (beakers, test tubes, Bunsen burner, multimeter, prism).
"""
```

---

### Step 2.7: Fact-Checking & Grounding for Science (`evaluator.py`)

Science lesson plans have high risk of AI hallucinations regarding units and chemical equations.
Ensure the fact-checking agent audits:
1. **SI Units & Formulations:** Verifies that units (e.g., $ms^{-1}$, $g/cm^3$, $N$, $J$) match secondary school conventions.
2. **Safety Realism:** Flags any dangerous chemical combinations inappropriate for Grade 6–9 students.
3. **Textbook Grounding:** Confirms that experimental procedures match the official NIE textbook experiments.

---

## PART 3: Frontend Adjustments (`frontend/src/`)

To expose the newly supported grades and Science subject to the user interface:

### 1. Update Lesson Plan Store (`frontend/src/store/useLessonPlanStore.ts`)
* Add `'Science'` to available subjects.
* Add support for Science-specific state (e.g., `isLabDoublePeriod: boolean`, `safetyEquipmentRequired: string[]`).

### 2. Update Step 1 Inputs Component (`frontend/src/components/planner/Step1Inputs.tsx`)
* Replace hardcoded single-subject display with a dropdown:
  ```tsx
  <select
    value={store.subject}
    onChange={(e) => store.setInputs({ subject: e.target.value })}
  >
    <option value="Civic Education">Civic Education</option>
    <option value="Science">Science</option>
  </select>
  ```
* Allow dynamic period selection (1 to 4 for Civic, 1 to 6 for Science).

### 3. Update Visual Badges in Viewer Components
* In `LessonPlanViewer.tsx` and `MultiPeriodPlanViewer.tsx`:
  * Add subject-specific styling (e.g., Emerald green badges for Science, Blue/Indigo badges for Civic Education).
  * Render an interactive "Laboratory Safety & Materials" callout box when `subject === 'Science'`.

---

## PART 4: Developer Verification Checklist & Testing Strategy

Before committing any expansion code, follow this verification pipeline:

```
[1. Curriculum Assets Ready]
      └── Verify PDFs in curriculum_data/
[2. Vector DB Ingestion]
      └── Ingest into ChromaDB & test retrieval filters
[3. Unit & Pipeline Tests]
      └── Run automated test scripts for the target grade/subject
[4. LLM Response Validation]
      └── Ensure valid JSON output matching LessonPlanSchemaDto
[5. Export Fidelity Verification]
      └── Export to Word (.docx) & PDF (.pdf) and check visual tables
```

### Automated Test Matrix to Create:
* `backend pycharm/tests/test_civic_grade6_pipeline.py`: Tests Grade 6 Civic generation.
* `backend pycharm/tests/test_civic_grade7_pipeline.py`: Tests Grade 7 Civic generation.
* `backend pycharm/tests/test_civic_grade9_pipeline.py`: Tests Grade 9 Civic generation (once TIG is ingested).
* `backend pycharm/tests/test_science_grade8_pipeline.py`: First Science pilot test.
* `backend pycharm/tests/test_export_science.py`: Tests PDF/Word table layout for lab steps.

---

## PART 5: Summary of File Changes Required

| Component | Target File | Nature of Change |
| :--- | :--- | :--- |
| **Curriculum Data** | `curriculum_data/grade_9/` | Add missing `grade_9_civic_teacher_guide.pdf`. |
| **Ingestion** | `app/ingestion/chunking_pipeline.py` | Add Science textbook Part 1 & 2 parsing. |
| **Routing & Guardrails** | `app/services/subject_guard.py` | Add Science to `SUPPORTED_SUBJECTS` registry. |
| **Pedagogical Options** | `app/services/activity_options_engine.py` | Add age-tiered Civic seeds and 5E Science tracks. |
| **Group Roles** | `app/services/grouping_logistics_engine.py`| Add Science laboratory roles (Safety Officer, etc.). |
| **Outcome Allocator** | `app/services/outcome_allocator.py` | Add Science action verb cognitive weights. |
| **Prompts** | `app/services/prompt_templates.py` | Add Science 5E lesson plan and safety prompts. |
| **Evaluator** | `app/evaluation/evaluator.py` | Add Science scientific unit and safety checks. |
| **Frontend UI** | `frontend/src/components/planner/Step1Inputs.tsx` | Add Subject selector (`Civic Education` vs `Science`). |

---
*Document Version: 1.0.0*  
*Target Environment: Python 3.13, FastAPI, ChromaDB, Next.js 16 (Turbopack), TailwindCSS*  
*Standard: National Institute of Education (NIE) Sri Lanka / LEARN Practice Teaching*
