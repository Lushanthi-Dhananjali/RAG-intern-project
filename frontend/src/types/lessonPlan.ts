// =====================================================================
// 1. PEDAGOGICAL ACTIVITY DISCOVERY TYPES (STEP 1 & STEP 2)
// =====================================================================

export interface PedagogicalActivityOption {
  id: string;
  title: string;
  pedagogy_type: string;
  description: string;
  student_action_summary?: string;
  teacher_facilitation_summary?: string;
  student_grouping: string;
  required_materials: string[];
  expected_student_output?: string;
  creative_assessment_preview: string;
  low_resource_alternative?: string;
  learning_outcomes_addressed?: string[];
}

export interface PedagogicalOptionsRequest {
  competency_level: string;
  topic_query?: string;
  grade_level?: string;
  subject?: string;
  student_count?: number;
  periods?: number;
}

export interface PedagogicalOptionsResponse {
  competency_level: string;
  lesson_topic: string;
  student_count: number;
  periods: number;
  options: PedagogicalActivityOption[];
}

// =====================================================================
// 2. LEARN KANDY PRACTICE TEACHING FORMAT (PRIMARY SCHEMA)
// =====================================================================

export interface LessonDevelopmentStep {
  step_number: number;
  teacher_activities: string;
  student_activities: string;
  learning_teaching_method: string;
  learning_teaching_aids: string;
  assessment_and_feedback: string;
  time_minutes: number;
  other?: string;
}

export interface LessonPlanSchemaDto {
  grade: string;
  subject: string;
  time_allocation: string;
  competence: string;
  competence_level: string;
  lesson: string;
  unique_learning_outcome: string[];
  the_entrance: string;
  lesson_development_steps: LessonDevelopmentStep[];
  summary: string;
  assessment_and_feedback_whole_lesson: string;
  post_activity: string;
  information_sources: string[];
  attachments: string[];
  period_number?: number;
  total_periods?: number;
  selected_activity?: string | null;
  selected_activity_title?: string | null;
  custom_teacher_activity?: string | null;
  activity_options?: PedagogicalActivityOption[];
  outcome_allocation?: Record<string, string[]>;
  entrance_duration_minutes?: number;
  assignment_duration_minutes?: number;
  filename?: string;
}

// Aliases for compatibility
export type LearnLessonPlanDto = LessonPlanSchemaDto;
export type PeradeniyaLessonPlanDto = LessonPlanSchemaDto;

// =====================================================================
// 3. GENERATION REQUEST & RESPONSE TYPES
// =====================================================================

export interface GenerateLessonPlanRequest {
  competency_level: string;
  topic_query?: string;
  grade_level?: string;
  subject?: string;
  periods?: number;
  requested_period?: number;
  single_period_only?: boolean;
  student_count?: number;
  selected_activity_option?: string;
  custom_teacher_activity?: string;
  duration_minutes?: number;
  time_slot?: string;
}

export type CompetencyLevelGenerateRequest = GenerateLessonPlanRequest;

export interface FactCheckReport {
  grounding_score?: number;
  passed?: boolean;
  unsupported_claims?: string[];
  explanation?: string;
}

export interface AlignmentReport {
  overall_alignment_score?: number;
  passed_alignment_guardrail?: boolean;
  details?: Record<string, unknown>;
}

export interface CompetencyLevelGenerateResponse {
  competency_level: string;
  grade_level: string;
  subject: string;
  periods: number;
  student_count: number;
  lesson_plan: LessonPlanSchemaDto;
  lesson_plans: LessonPlanSchemaDto[];
  fact_check_report?: FactCheckReport;
  alignment_report?: AlignmentReport;
}

// =====================================================================
// 4. LEGACY / GENERIC PIPELINE COMPATIBILITY TYPES
// =====================================================================

export interface LessonPlanRequest {
  query: string;
  gradeLevel: string;
  subject: string;
  useRAG: boolean;
}

export interface LearningOutcome {
  id: number;
  description: string;
  blooms_taxonomy_level?: string;
}

export interface MaterialItem {
  item_name: string;
  quantity: string;
  is_digital: boolean;
}

export interface ProcedureStep {
  step_number: number;
  phase_title: string;
  duration_minutes: number;
  teacher_action: string;
  student_action: string;
}

export interface AssessmentAndVerification {
  formative_assessment: string;
  summative_assessment?: string;
  alignment_check: string;
}

export interface LessonPlanSchema {
  title: string;
  subject: string;
  grade_level: string;
  topic: string;
  educational_goal_or_standard: string;
  estimated_duration_minutes: number;
  learning_outcomes: LearningOutcome[];
  materials: MaterialItem[];
  procedures: ProcedureStep[];
  verification: AssessmentAndVerification;
}

export interface LessonPlanGenerateResponse {
  lesson_plan: LessonPlanSchemaDto | LessonPlanSchema;
  lesson_plans?: LessonPlanSchemaDto[];
  fact_check_report?: FactCheckReport;
  alignment_report?: AlignmentReport;
}