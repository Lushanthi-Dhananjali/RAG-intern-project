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

export interface FactCheckReport {
  grounding_score: number;
  passed: boolean;
  unsupported_claims?: string[];
  explanation?: string;
}

export interface AlignmentReport {
  overall_alignment_score: number;
  passed_alignment_guardrail: boolean;
}

export interface LessonPlanGenerateResponse {
  lesson_plan: LessonPlanSchema;
  fact_check_report?: FactCheckReport;
  alignment_report?: AlignmentReport;
}