// =====================================================================
// DYNAMIC CONFIGURATION (LAN / LOCALHOST RESOLUTION)
// =====================================================================
export const API_BASE_URL =
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
  post_activity?: string;
  information_sources?: string[];
  attachments?: string[];
}

// Type aliases for seamless compatibility across UI components
export type LearnLessonPlanDto = LessonPlanDto;
export type LessonPlanSchemaDto = LessonPlanDto;

export interface PedagogicalActivityOption {
  id: string;
  title: string;
  pedagogy_type: string;
  description: string;
  student_action_summary?: string;
  teacher_facilitation_summary?: string;
  student_grouping: string;
  required_materials: string[];
  approximate_duration_minutes?: number;
  expected_student_output?: string;
  creative_assessment_preview: string;
  low_resource_alternative?: string;
  learning_outcomes_addressed?: string[];
}

export interface PedagogicalOptionsResponse {
  competency_level: string;
  lesson_topic: string;
  student_count: number;
  periods: number;
  requested_period: number;
  teacher_mode: string;
  options: PedagogicalActivityOption[];
}

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
  periods?: number;
  requested_period?: number;
  student_count?: number;
  teacher_mode?: string;
  lesson_plan: LessonPlanDto;
  lesson_plans?: LessonPlanDto[];
  fact_check_report: FactCheckReport | any;
  alignment_report: AlignmentReport | any;
}

// Backend-facing Snake Case DTO
export interface LessonPlanPayload {
  competency_level: string;
  topic_query?: string;
  grade_level?: string;
  subject?: string;
  periods?: number;
  requested_period?: number;
  student_count?: number;
  teacher_mode?: 'suggested' | 'own_approach';
  selected_activity_option?: string;
  custom_teacher_activity?: string;
  classroom_environment?: string;
  accessible_resources?: string[];
  previous_period_activities?: string[];
  time_slot?: string;
  duration_minutes?: number;
}

// Frontend-facing Camel Case DTO
export interface GeneratePlanPayload {
  competencyLevel: string;
  topicQuery?: string;
  gradeLevel?: string;
  subject?: string;
  periods?: number;
  requestedPeriod?: number;
  studentCount?: number;
  teacherMode?: 'suggested' | 'own_approach';
  selectedActivityOption?: string;
  customTeacherActivity?: string;
  classroomEnvironment?: string;
  accessibleResources?: string[];
  previousPeriodActivities?: string[];
  timeSlot?: string;
  durationMinutes?: number;
}

export interface FetchOptionsPayload {
  competencyLevel: string;
  studentCount?: number;
  periods?: number;
  requestedPeriod?: number;
  gradeLevel?: string;
  subject?: string;
  classroomEnvironment?: string;
  accessibleResources?: string[];
  previousPeriodActivities?: string[];
}

export interface UnitGeneratePayload {
  unitQuery: string;
  gradeLevel?: string;
  subject?: string;
  periods?: number;
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

// Storage Management DTOs
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

// =====================================================================
// HELPER UTILITIES
// =====================================================================

/**
 * Calculates total duration and builds the canonical time allocation label.
 * Standard NIE Sri Lanka curriculum rule: 1 Period = 40 Minutes.
 */
export function resolvePeriodTime(
  periodsCount: number = 1,
  requestedPeriod: number = 1,
  explicitMinutes?: number
) {
  const periods = Math.min(Math.max(periodsCount || 1, 1), 4); // Clamped between 1 and 4
  const currentPeriod = Math.min(Math.max(requestedPeriod || 1, 1), periods);
  const duration = explicitMinutes || periods * 40;
  const timeSlot = `40 Minutes (Period ${currentPeriod} of ${periods})`;
  return { periods, currentPeriod, duration, timeSlot };
}

// =====================================================================
// STEP 4 & 5: PERIOD-AWARE PEDAGOGICAL OPTIONS API
// =====================================================================

/**
 * Discovers 3 distinct, period-aware activity options tailored to class size
 * and enforces anti-repetition against previous_period_activities.
 */
export async function fetchPedagogicalOptions(
  params: FetchOptionsPayload
): Promise<PedagogicalActivityOption[]> {
  const periods = Math.min(Math.max(params.periods || 1, 1), 4);
  const requestedPeriod = Math.min(Math.max(params.requestedPeriod || 1, 1), periods);

  const payload = {
    competency_level: params.competencyLevel.trim(),
    student_count: params.studentCount || 35,
    periods: periods,
    requested_period: requestedPeriod,
    grade_level: params.gradeLevel || 'Grade 8',
    subject: params.subject || 'Civic Education',
    classroom_environment: params.classroomEnvironment || 'Standard Classroom',
    accessible_resources: params.accessibleResources || [],
    previous_period_activities: params.previousPeriodActivities || [],
  };

  const response = await fetch(`${API_BASE_URL}/api/v1/suggest-pedagogical-options`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch pedagogical options (Status ${response.status})`
    );
  }

  const data: PedagogicalOptionsResponse = await response.json();
  return data.options;
}

// =====================================================================
// STEP 6, 7 & 8: SINGLE-PERIOD 40-MINUTE PLAN GENERATION API
// =====================================================================

/**
 * Generates an individual 40-minute plan for the specified period.
 * Direct bridge matching the Step 9 frontend state machine.
 */
export async function generateSinglePeriodPlan(
  params: GeneratePlanPayload
): Promise<LessonPlanDto> {
  const result = await generateLessonPlan(params);
  return result.lesson_plan;
}

/**
 * Idiomatic camelCase client with full support for Mode A, Mode B,
 * grouping logistics, and deterministic timing repair.
 */
export async function generateLessonPlan({
  competencyLevel,
  topicQuery = '',
  gradeLevel = 'Grade 8',
  subject = 'Civic Education',
  periods = 1,
  requestedPeriod = 1,
  studentCount = 35,
  teacherMode = 'suggested',
  selectedActivityOption,
  customTeacherActivity,
  classroomEnvironment = 'Standard Classroom',
  accessibleResources = [],
  previousPeriodActivities = [],
  timeSlot,
  durationMinutes,
}: GeneratePlanPayload): Promise<LessonPlanResponse> {
  const resolved = resolvePeriodTime(periods, requestedPeriod, durationMinutes);

  const payload: LessonPlanPayload = {
    competency_level: competencyLevel.trim(),
    topic_query: topicQuery,
    grade_level: gradeLevel,
    subject: subject,
    periods: resolved.periods,
    requested_period: resolved.currentPeriod,
    student_count: studentCount,
    teacher_mode: teacherMode,
    selected_activity_option: selectedActivityOption,
    custom_teacher_activity: customTeacherActivity,
    classroom_environment: classroomEnvironment,
    accessible_resources: accessibleResources,
    previous_period_activities: previousPeriodActivities,
    time_slot: timeSlot || resolved.timeSlot,
    duration_minutes: resolved.duration,
  };

  const response = await fetch(`${API_BASE_URL}/api/v1/generate-by-competency-level`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
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
 * Direct snake_case fetch client matching the raw FastAPI request model.
 */
export async function fetchLessonPlan(
  payload: LessonPlanPayload
): Promise<LessonPlanResponse> {
  const resolved = resolvePeriodTime(
    payload.periods,
    payload.requested_period,
    payload.duration_minutes
  );

  const response = await fetch(`${API_BASE_URL}/api/v1/generate-by-competency-level`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      periods: resolved.periods,
      requested_period: resolved.currentPeriod,
      time_slot: payload.time_slot || resolved.timeSlot,
      duration_minutes: resolved.duration,
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
 * Batch generate plans across all competencies discovered in a syllabus unit.
 */
export async function generateUnitPlans({
  unitQuery,
  gradeLevel = 'Grade 8',
  subject = 'Civic Education',
  periods = 1,
  timeSlot,
  durationMinutes,
}: UnitGeneratePayload): Promise<UnitGenerateResponse> {
  const resolved = resolvePeriodTime(periods, 1, durationMinutes);

  const response = await fetch(`${API_BASE_URL}/api/v1/generate-by-unit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json();
}

// =====================================================================
// GENERATED PLANS STORAGE MANAGEMENT (LIST, GET, SAVE, DELETE)
// =====================================================================

export async function fetchGeneratedPlans(filters?: {
  search?: string;
  grade?: string;
  subject?: string;
}): Promise<GeneratedPlanSummary[]> {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.grade && filters.grade !== 'All') params.append('grade', filters.grade);
  if (filters?.subject && filters.subject !== 'All') params.append('subject', filters.subject);
  params.append('_t', String(Date.now()));

  const queryString = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/v1/generated-plans${queryString}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
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
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
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
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
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
  if (grade) params.append('grade', grade);
  if (subject) params.append('subject', subject);
  params.append('_t', String(Date.now()));

  const queryString = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(
    `${API_BASE_URL}/api/v1/generated-plans/by-competency/${encodeURIComponent(
      competencyLevel.trim()
    )}${queryString}`,
    {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
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

export async function saveGeneratedPlan(
  plan: any,
  filename?: string
): Promise<{ success: boolean; message: string; filename: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/generated-plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan, filename }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to save lesson plan (Status ${response.status})`
    );
  }

  return response.json();
}