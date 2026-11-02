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

export const sanitizePlanUrls = (p: LessonPlanSchemaDto): LessonPlanSchemaDto => {
  if (!p) return p;
  let competence_level = p.competence_level;
  if (competence_level && (competence_level.includes('http://') || competence_level.includes('https://'))) {
    const match = competence_level.match(/\b(\d+\.\d+(?:\.\d+)?)\b/);
    competence_level = match ? match[1] : competence_level.split('/').filter(Boolean).pop() || '8.1.1';
  }
  let competence = p.competence;
  if (competence && (competence.includes('http://') || competence.includes('https://'))) {
    const slug = competence.replace(/^https?:\/\/[^/]+\/(?:competence\/?)?/, '');
    const cleanSlug = slug.replace(/-/g, ' ').trim();
    competence = cleanSlug ? cleanSlug.charAt(0).toUpperCase() + cleanSlug.slice(1) : 'Curriculum Competence Standard';
  }
  return {
    ...p,
    competence_level,
    competence,
  };
};

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
  optionsByPeriod: Record<number, PedagogicalActivityOption[]>;
  selectedOption: PedagogicalActivityOption | null;
  selectedOptionByPeriod: Record<number, PedagogicalActivityOption | null>;
  customTeacherActivity: string;
  customActivityByPeriod: Record<number, string>;
  
  // API Key & Provider settings
  apiKey: string;
  llmProvider: 'auto' | 'openai' | 'gemini' | 'ollama';

  // History & storage
  previousPeriodActivities: string[];
  generatedPlans: Record<number, LessonPlanSchemaDto>;
  activityByPeriod: Record<number, string>;
  isLoading: boolean;
  error: string | null;

  // Actions
  setInputs: (inputs: Partial<MultiPeriodState>) => void;
  setCurrentPeriod: (period: number) => void;
  startPlanningPeriod: (period: number, options: PedagogicalActivityOption[]) => void;
  viewPeriodPlan: (period: number) => void;
  goToChooseActivity: (period?: number) => void;
  setOptions: (options: PedagogicalActivityOption[]) => void;
  selectOption: (option: PedagogicalActivityOption) => void;
  setCustomTeacherActivity: (activity: string) => void;
  setApiKey: (key: string) => void;
  setLlmProvider: (provider: 'auto' | 'openai' | 'gemini' | 'ollama') => void;
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
  optionsByPeriod: {},
  selectedOption: null,
  selectedOptionByPeriod: {},
  customTeacherActivity: '',
  customActivityByPeriod: {},
  apiKey: '',
  llmProvider: 'auto',
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

    const targetTotal = inputs.totalPeriods !== undefined ? inputs.totalPeriods : state.totalPeriods;
    const targetPeriod = inputs.currentPeriod !== undefined
      ? Math.max(1, Math.min(inputs.currentPeriod, targetTotal))
      : (sequenceChanged ? 1 : Math.max(1, Math.min(state.currentPeriod, targetTotal)));

    return sequenceChanged
      ? {
          ...state,
          ...inputs,
          step: 1,
          totalPeriods: targetTotal,
          currentPeriod: targetPeriod,
          currentOptions: [],
          optionsByPeriod: {},
          selectedOption: null,
          selectedOptionByPeriod: {},
          customTeacherActivity: '',
          customActivityByPeriod: {},
          generatedPlans: {},
          activityByPeriod: {},
          previousPeriodActivities: [],
        }
      : { ...state, ...inputs, currentPeriod: targetPeriod };
  }),

  setCurrentPeriod: (period) => set((state) => {
    const targetPeriod = Math.max(1, Math.min(period, state.totalPeriods));
    const cachedOptions = state.optionsByPeriod[targetPeriod] || [];
    return {
      currentPeriod: targetPeriod,
      currentOptions: cachedOptions.length > 0 ? cachedOptions : state.currentOptions,
      selectedOption: state.selectedOptionByPeriod[targetPeriod] || null,
      customTeacherActivity: state.customActivityByPeriod[targetPeriod] || '',
    };
  }),

  startPlanningPeriod: (period, options) => set((state) => {
    const targetPeriod = Math.max(1, Math.min(period, state.totalPeriods));
    const updatedOptionsByPeriod = { ...state.optionsByPeriod, [targetPeriod]: options };
    return {
      currentPeriod: targetPeriod,
      currentOptions: options,
      optionsByPeriod: updatedOptionsByPeriod,
      selectedOption: state.selectedOptionByPeriod[targetPeriod] || options[0] || null,
      customTeacherActivity: state.customActivityByPeriod[targetPeriod] || '',
      step: 2,
    };
  }),

  viewPeriodPlan: (period) => set((state) => ({
    currentPeriod: Math.max(1, Math.min(period, state.totalPeriods)),
    step: 3,
  })),

  goToChooseActivity: (period) => set((state) => {
    const targetPeriod = period !== undefined ? Math.max(1, Math.min(period, state.totalPeriods)) : state.currentPeriod;
    const cachedOptions = state.optionsByPeriod[targetPeriod] || state.currentOptions;
    return {
      currentPeriod: targetPeriod,
      currentOptions: cachedOptions,
      selectedOption: state.selectedOptionByPeriod[targetPeriod] || state.selectedOption || (cachedOptions.length > 0 ? cachedOptions[0] : null),
      customTeacherActivity: state.customActivityByPeriod[targetPeriod] || state.customTeacherActivity,
      teacherMode: state.customActivityByPeriod[targetPeriod] ? 'own_approach' : 'suggested',
      step: 2,
    };
  }),

  setOptions: (options) => set((state) => ({
    currentOptions: options,
    optionsByPeriod: { ...state.optionsByPeriod, [state.currentPeriod]: options },
    selectedOption: options.length > 0 ? options[0] : null,
    step: 2
  })),

  selectOption: (option) => set((state) => ({
    selectedOption: option,
    selectedOptionByPeriod: { ...state.selectedOptionByPeriod, [state.currentPeriod]: option },
    teacherMode: 'suggested'
  })),

  setCustomTeacherActivity: (act) => set((state) => ({
    customTeacherActivity: act,
    customActivityByPeriod: { ...state.customActivityByPeriod, [state.currentPeriod]: act },
    teacherMode: 'own_approach'
  })),

  setApiKey: (key) => set({ apiKey: key }),
  setLlmProvider: (prov) => set({ llmProvider: prov }),
  
  setGeneratedPlan: (period, plan, activityTitle) =>
    set((state) => {
      const activityByPeriod = { ...state.activityByPeriod, [period]: activityTitle };
      return {
        generatedPlans: { ...state.generatedPlans, [period]: sanitizePlanUrls(plan) },
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
    const { currentPeriod, totalPeriods, generatedPlans } = get();
    let nextP = currentPeriod + 1;
    if (nextP > totalPeriods) {
      nextP = 1;
    }
    const cachedOptions = get().optionsByPeriod[nextP] || [];
    set({
      currentPeriod: nextP,
      currentOptions: cachedOptions,
      selectedOption: get().selectedOptionByPeriod[nextP] || (cachedOptions[0] || null),
      customTeacherActivity: get().customActivityByPeriod[nextP] || '',
      step: 2,
    });
  },

  previousPeriod: (p) => set({ currentPeriod: p, step: 3 }),
  goToStep: (step) => set((state) => {
    if (step === 2) {
      const cachedOptions = state.optionsByPeriod[state.currentPeriod] || state.currentOptions;
      return {
        step: 2,
        currentOptions: cachedOptions,
        selectedOption: state.selectedOptionByPeriod[state.currentPeriod] || state.selectedOption || (cachedOptions[0] || null),
        customTeacherActivity: state.customActivityByPeriod[state.currentPeriod] || state.customTeacherActivity,
      };
    }
    return { step };
  }),
  resetAll: () =>
    set({
      step: 1,
      currentPeriod: 1,
      generatedPlans: {},
      activityByPeriod: {},
      previousPeriodActivities: [],
      selectedOption: null,
      selectedOptionByPeriod: {},
      currentOptions: [],
      optionsByPeriod: {},
      customTeacherActivity: '',
      customActivityByPeriod: {},
    }),
}), { name: 'civic-multi-period-planner' }));