import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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

export interface LessonDevelopmentStep {
  step_number: number;
  time_minutes: number;
  learning_teaching_method: string;
  learning_teaching_aids: string;
  teacher_activities: string;
  student_activities: string;
  assessment_and_feedback: string;
  other?: string;
}

export interface LessonPlanSchemaDto {
  lesson: string;
  subject: string;
  grade: string;
  competence: string;
  competence_level: string;
  time_allocation: string;
  unique_learning_outcome: string[];
  the_entrance: string;
  lesson_development_steps: LessonDevelopmentStep[];
  summary: string;
  assessment_and_feedback_whole_lesson: string;
  post_activity?: string;
  information_sources?: string[];
  attachments?: string[];
  period_number?: number;
  total_periods?: number;
  selected_activity?: string | null;
  selected_activity_title?: string | null;
  outcome_allocation?: Record<string, string[]>;
  custom_teacher_activity?: string | null;
  activity_options?: PedagogicalActivityOption[];
  entrance_duration_minutes?: number;
  assignment_duration_minutes?: number;
}

export interface MultiPeriodState {
  // Step indicator (1 = Inputs, 2 = Option Selection, 3 = Viewer)
  step: 1 | 2 | 3;
  
  // Curriculum configuration
  competencyLevel: string;
  gradeLevel: string;
  subject: string;
  topicQuery: string;
  totalPeriods: number;
  currentPeriod: number;
  studentCount: number;
  classroomEnvironment: string;
  accessibleResources: string[];
  
  // Teacher mode & options
  teacherMode: 'suggested' | 'own_approach';
  currentOptions: PedagogicalActivityOption[];
  selectedOption: PedagogicalActivityOption | null;
  customTeacherActivity: string;
  
  // History & storage
  previousPeriodActivities: string[];
  generatedPlans: Record<number, LessonPlanSchemaDto>;
  activityByPeriod: Record<number, string>;
  isLoading: boolean;
  error: string | null;

  // Actions
  setInputs: (inputs: Partial<MultiPeriodState>) => void;
  setOptions: (options: PedagogicalActivityOption[]) => void;
  selectOption: (option: PedagogicalActivityOption) => void;
  setCustomTeacherActivity: (activity: string) => void;
  setGeneratedPlan: (period: number, plan: LessonPlanSchemaDto, activityTitle: string) => void;
  priorActivityTitles: (period: number) => string[];
  otherActivityTitles: (period: number) => string[];
  nextPeriod: () => void;
  previousPeriod: (period: number) => void;
  goToStep: (step: 1 | 2 | 3) => void;
  resetAll: () => void;
}

export const useLessonPlanStore = create<MultiPeriodState>()(persist((set, get) => ({
  step: 1,
  competencyLevel: '8.1.1',
  gradeLevel: 'Grade 8',
  subject: 'Civic Education',
  topicQuery: '',
  totalPeriods: 2,
  currentPeriod: 1,
  studentCount: 35,
  classroomEnvironment: 'Standard Classroom',
  accessibleResources: ['Chalkboard', 'Student Notebooks', 'Chart Paper'],
  teacherMode: 'suggested',
  currentOptions: [],
  selectedOption: null,
  customTeacherActivity: '',
  previousPeriodActivities: [],
  generatedPlans: {},
  activityByPeriod: {},
  isLoading: false,
  error: null,

  setInputs: (inputs) => set((state) => {
    const sequenceChanged =
      (inputs.competencyLevel !== undefined && inputs.competencyLevel !== state.competencyLevel) ||
      (inputs.gradeLevel !== undefined && inputs.gradeLevel !== state.gradeLevel) ||
      (inputs.subject !== undefined && inputs.subject !== state.subject) ||
      (inputs.topicQuery !== undefined && inputs.topicQuery !== state.topicQuery) ||
      (inputs.totalPeriods !== undefined && inputs.totalPeriods !== state.totalPeriods);
    return sequenceChanged
      ? {
          ...state,
          ...inputs,
          step: 1,
          currentPeriod: 1,
          currentOptions: [],
          selectedOption: null,
          generatedPlans: {},
          activityByPeriod: {},
          previousPeriodActivities: [],
        }
      : { ...state, ...inputs };
  }),
  setOptions: (options) => set({ currentOptions: options, selectedOption: null, step: 2 }),
  selectOption: (option) => set({ selectedOption: option, teacherMode: 'suggested' }),
  setCustomTeacherActivity: (act) => set({ customTeacherActivity: act, teacherMode: 'own_approach' }),
  
  setGeneratedPlan: (period, plan, activityTitle) =>
    set((state) => {
      const activityByPeriod = { ...state.activityByPeriod, [period]: activityTitle };
      return {
        generatedPlans: { ...state.generatedPlans, [period]: plan },
        activityByPeriod,
        previousPeriodActivities: Object.keys(activityByPeriod)
          .map(Number)
          .sort((a, b) => a - b)
          .map((periodNumber) => activityByPeriod[periodNumber]),
        step: 3,
        isLoading: false,
      };
    }),

  priorActivityTitles: (period) => {
    const activityByPeriod = get().activityByPeriod;
    return Object.entries(activityByPeriod)
      .filter(([periodNumber]) => Number(periodNumber) < period)
      .sort(([periodA], [periodB]) => Number(periodA) - Number(periodB))
      .map(([, title]) => title);
  },
  otherActivityTitles: (period) =>
    Object.entries(get().activityByPeriod)
      .filter(([periodNumber]) => Number(periodNumber) !== period)
      .sort(([periodA], [periodB]) => Number(periodA) - Number(periodB))
      .map(([, title]) => title),

  nextPeriod: () => {
    const { currentPeriod, totalPeriods } = get();
    if (currentPeriod < totalPeriods) {
      set({
        currentPeriod: currentPeriod + 1,
        selectedOption: null,
        customTeacherActivity: '',
        step: 2,
      });
    }
  },

  previousPeriod: (p) => set({ currentPeriod: p, step: 3 }),
  goToStep: (step) => set({ step }),
  resetAll: () =>
    set({
      step: 1,
      currentPeriod: 1,
      generatedPlans: {},
      activityByPeriod: {},
      previousPeriodActivities: [],
      selectedOption: null,
      currentOptions: [],
      customTeacherActivity: '',
    }),
}), { name: 'civic-multi-period-planner' }));