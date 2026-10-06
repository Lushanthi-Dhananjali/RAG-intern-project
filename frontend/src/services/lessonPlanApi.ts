// =====================================================================
// DYNAMIC CONFIGURATION (LAN / LOCALHOST RESOLUTION)
// =====================================================================
const API_BASE_URL =
  typeof window !== 'undefined' && window.location.hostname
    ? `http://${window.location.hostname}:8000`
    : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000');

// =====================================================================
// TYPE DEFINITIONS (LEARN PRACTICE TEACHING FORMAT & NIE DTOs)
// =====================================================================
export interface LessonDevelopmentStepDto {
  step_number: number;
  teacher_activities: string;
  student_activities: string;
  learning_teaching_method: string;
  learning_teaching_aids: string;
  assessment_and_feedback: string;
  time_minutes: number;
  other?: string;
}

export interface LessonPlanDto {
  grade: string;
  subject: string;
  time_allocation: string;
  competence: string;
  competence_level: string;
  lesson: string;
  unique_learning_outcome: string[];
  the_entrance: string;
  lesson_development_steps: LessonDevelopmentStepDto[];
  summary: string;
  assessment_and_feedback_whole_lesson: string;
  post_activity: string;
  information_sources?: string[];
  attachments?: string[];
}

// Type alias for UI components
export type LearnLessonPlanDto = LessonPlanDto;

export interface FactCheckReport {
  grounding_score: number;
  passed: boolean;
  unsupported_claims: string[];
}

export interface AlignmentReport {
  overall_alignment_score: number;
  passed_alignment_guardrail: boolean;
  unaddressed_outcomes?: string[];
}

export interface LessonPlanResponse {
  competency_level: string;
  grade_level: string;
  subject: string;
  lesson_plan: LessonPlanDto;
  fact_check_report: FactCheckReport | any;
  alignment_report: AlignmentReport | any;
}

// Snake-case request payload (Direct Backend Mapping with 1-4 Periods Support)
export interface LessonPlanPayload {
  competency_level: string;
  topic_query?: string;
  grade_level?: string;
  subject?: string;
  periods?: number; // 1, 2, 3, or 4 periods
  time_slot?: string;
  duration_minutes?: number;
}

// Camel-case request payload (Idiomatic React / TypeScript)
export interface GeneratePlanPayload {
  competencyLevel: string;
  topicQuery?: string;
  gradeLevel?: string;
  subject?: string;
  periods?: number; // 1, 2, 3, or 4 periods
  timeSlot?: string;
  durationMinutes?: number;
}

export interface UnitGeneratePayload {
  unitQuery: string;
  gradeLevel?: string;
  subject?: string;
  periods?: number; // 1, 2, 3, or 4 periods
  timeSlot?: string;
  durationMinutes?: number;
}

export interface UnitGenerateResponse {
  unit_query: string;
  grade_level: string;
  subject: string;
  total_plans: number;
  lesson_plans: LessonPlanDto[];
}

// =====================================================================
// HELPER UTILITIES
// =====================================================================

/**
 * Calculates total duration and builds the official time allocation label.
 * Standard NIE curriculum rule: 1 Period = 40 Minutes.
 */
function resolvePeriodTime(periodsCount: number = 1, explicitMinutes?: number) {
  const periods = Math.min(Math.max(periodsCount, 1), 4); // Clamped between 1 and 4
  const duration = explicitMinutes || periods * 40;
  const timeSlot = `${duration} Minutes (${periods} ${periods === 1 ? 'Period' : 'Periods'})`;
  return { periods, duration, timeSlot };
}

// =====================================================================
// API CLIENT FUNCTIONS
// =====================================================================

/**
 * Direct snake_case fetch client matching the raw FastAPI request model.
 * Automatically computes duration and time_slot (40 mins per period).
 */
export async function fetchLessonPlan(
  payload: LessonPlanPayload
): Promise<LessonPlanResponse> {
  const { periods, duration, timeSlot } = resolvePeriodTime(
    payload.periods,
    payload.duration_minutes
  );

  const response = await fetch(`${API_BASE_URL}/api/v1/generate-by-competency-level`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      competency_level: payload.competency_level,
      topic_query: payload.topic_query || "",
      grade_level: payload.grade_level || "Grade 8",
      subject: payload.subject || "Civic Education",
      periods: periods,
      time_slot: payload.time_slot || timeSlot,
      duration_minutes: duration,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch lesson plan (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Idiomatic camelCase client with dynamic 1-4 periods support for Next.js UI components.
 */
export async function generateLessonPlan({
  competencyLevel,
  topicQuery = "",
  gradeLevel = "Grade 8",
  subject = "Civic Education",
  periods = 1,
  timeSlot,
  durationMinutes,
}: GeneratePlanPayload): Promise<LessonPlanResponse> {
  const resolved = resolvePeriodTime(periods, durationMinutes);

  const response = await fetch(`${API_BASE_URL}/api/v1/generate-by-competency-level`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      competency_level: competencyLevel,
      topic_query: topicQuery,
      grade_level: gradeLevel,
      subject: subject,
      periods: resolved.periods,
      time_slot: timeSlot || resolved.timeSlot,
      duration_minutes: resolved.duration,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to generate lesson plan (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Batch generate plans across all competencies discovered in a syllabus unit
 * with period scaling (1 to 4 periods).
 */
export async function generateUnitPlans({
  unitQuery,
  gradeLevel = "Grade 8",
  subject = "Civic Education",
  periods = 1,
  timeSlot,
  durationMinutes,
}: UnitGeneratePayload): Promise<UnitGenerateResponse> {
  const resolved = resolvePeriodTime(periods, durationMinutes);

  const response = await fetch(`${API_BASE_URL}/api/v1/generate-by-unit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      unit_query: unitQuery,
      grade_level: gradeLevel,
      subject: subject,
      periods: resolved.periods,
      time_slot: timeSlot || resolved.timeSlot,
      duration_minutes: resolved.duration,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to generate unit lesson plans (Status ${response.status})`
    );
  }

  return response.json();
}

/**
 * Health check ping for testing backend connectivity.
 */
export async function checkBackendHealth(): Promise<{ status: string; engine: string }> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json();
}

// =====================================================================
// GENERATED PLANS STORAGE MANAGEMENT (LIST & DELETE)
// =====================================================================

export interface GeneratedPlanSummary {
  id: string;
  filename: string;
  grade: string;
  subject: string;
  competence_level: string;
  competence: string;
  lesson: string;
  time_allocation: string;
  the_entrance?: string;
  summary?: string;
  step_count: number;
  outcome_count: number;
  created_at: string;
  updated_at?: string;
  file_size_bytes?: number;
}

export interface GeneratedPlanDetailResponse {
  filename: string;
  id: string;
  created_at: string;
  file_size_bytes: number;
  plan: LessonPlanDto;
}

export interface DeletePlanResponse {
  success: boolean;
  message: string;
  deleted_filename: string;
}

export async function fetchGeneratedPlans(filters?: {
  search?: string;
  grade?: string;
  subject?: string;
}): Promise<GeneratedPlanSummary[]> {
  const params = new URLSearchParams();
  if (filters?.search) params.append("search", filters.search);
  if (filters?.grade && filters.grade !== "All") params.append("grade", filters.grade);
  if (filters?.subject && filters.subject !== "All") params.append("subject", filters.subject);
  params.append("_t", String(Date.now()));

  const queryString = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/api/v1/generated-plans${queryString}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to load generated lesson plans (Status ${response.status})`);
  }

  return response.json();
}

export async function fetchGeneratedPlanDetail(
  filename: string
): Promise<GeneratedPlanDetailResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/generated-plans/${encodeURIComponent(filename)}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to load lesson plan '${filename}' (Status ${response.status})`);
  }

  return response.json();
}

export async function deleteGeneratedPlan(
  filename: string
): Promise<DeletePlanResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/generated-plans/${encodeURIComponent(filename)}`,
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to delete lesson plan (Status ${response.status})`
    );
  }

  return response.json();
}

export async function fetchPlanByCompetency(
  competencyLevel: string,
  grade?: string,
  subject?: string
): Promise<GeneratedPlanDetailResponse> {
  const params = new URLSearchParams();
  if (grade) params.append("grade", grade);
  if (subject) params.append("subject", subject);
  params.append("_t", String(Date.now()));

  const queryString = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(
    `${API_BASE_URL}/api/v1/generated-plans/by-competency/${encodeURIComponent(competencyLevel.trim())}${queryString}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `No saved lesson plan found for Competency Level '${competencyLevel}'.`
    );
  }

  return response.json();
}
