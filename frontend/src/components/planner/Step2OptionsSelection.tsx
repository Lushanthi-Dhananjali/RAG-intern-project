'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { generateSinglePeriodPlan } from '@/services/lessonPlanApi';

export default function Step2OptionsSelection() {
  const store = useLessonPlanStore();
  const [loading, setLoading] = useState(false);
  const [customMode, setCustomMode] = useState(false);
  const [customText, setCustomText] = useState('');
  const [generationError, setGenerationError] = useState<string | null>(null);

  const handleGenerate = async (selectedDesc?: string, isCustom = false, activityTitle?: string) => {
    setLoading(true);
    const chosenTitle = isCustom
      ? `Teacher approach: ${customText.trim()}`
      : (activityTitle || 'Selected Strategy');
    setGenerationError(null);
    try {
      const plan = await generateSinglePeriodPlan({
        competencyLevel: store.competencyLevel,
        topicQuery: store.topicQuery,
        periods: store.totalPeriods,
        requestedPeriod: store.currentPeriod,
        studentCount: store.studentCount,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        teacherMode: isCustom ? 'own_approach' : 'suggested',
        selectedActivityOption: selectedDesc,
        selectedActivityTitle: isCustom
          ? `Teacher approach: ${customText.trim()}`
          : activityTitle,
        customTeacherActivity: isCustom ? customText : undefined,
        activityOptions: store.currentOptions,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(store.currentPeriod),
      });

      store.setGeneratedPlan(store.currentPeriod, plan, chosenTitle);
    } catch (err: any) {
      setGenerationError(err.message || 'Generation failed. Your activity selection has been kept.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 rounded-xl border border-indigo-100 bg-indigo-50/60 p-4 sm:flex-row sm:items-center">
        <div>
          <span className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-indigo-700">
            Period {store.currentPeriod} Activity Selection
          </span>
          <h2 className="mt-0.5 text-lg font-extrabold text-slate-900">
            Choose an activity for Period {store.currentPeriod} of {store.totalPeriods}
          </h2>
          <p className="mt-1 text-xs text-slate-600">Choose an approach for this 40-minute lesson.</p>
          {store.priorActivityTitles(store.currentPeriod).length > 0 && (
            <p className="mt-2 text-xs text-slate-600">
              <strong>Activities used in earlier periods:</strong> {store.priorActivityTitles(store.currentPeriod).join(', ')}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => setCustomMode(!customMode)}
          className="shrink-0 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-sm transition hover:border-indigo-300 hover:bg-indigo-50 sm:text-sm"
        >
          {customMode ? '← View activity options' : 'Use my own activity'}
        </button>
      </div>

      {generationError && (
        <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {generationError}
        </div>
      )}
      {loading && (
        <div role="status" className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm font-semibold text-blue-900">
          Generating the Period {store.currentPeriod} plan from your selected activity. Your selections remain available.
        </div>
      )}

      {!customMode ? (
        <div>
          <div className="mb-3 flex items-center justify-between gap-2">
            <h3 className="text-sm font-extrabold text-slate-800">Activity options</h3>
            <span className="text-[11px] font-semibold text-slate-500">{store.currentOptions.length} choices</span>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {store.currentOptions.map((opt, index) => (
              <article
                key={opt.id}
                onClick={() => store.selectOption(opt)}
                className={`flex h-full flex-col rounded-xl border bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
                  store.selectedOption?.id === opt.id
                    ? 'border-indigo-400 ring-2 ring-indigo-100'
                    : 'border-slate-200 hover:border-indigo-200'
                }`}
              >
                <div className="mb-3 flex items-start justify-between gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-[11px] font-extrabold text-indigo-700">
                    {index + 1}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-slate-600">
                    {opt.pedagogy_type}
                  </span>
                </div>
                <h4 className="text-sm font-extrabold leading-snug text-slate-900">{opt.title}</h4>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{opt.description}</p>
                {opt.learning_outcomes_addressed && opt.learning_outcomes_addressed.length > 0 && (
                  <div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50/50 p-3 text-xs text-slate-700">
                    <strong className="text-indigo-900">Period {store.currentPeriod} learning outcomes</strong>
                    <ul className="mt-2 list-disc space-y-1 pl-4">
                      {opt.learning_outcomes_addressed.map((outcome, outcomeIndex) => (
                        <li key={outcomeIndex}>{outcome}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600">
                  <strong className="text-slate-800">Student grouping</strong>
                  <p className="mt-1">{opt.student_grouping}</p>
                </div>
                <button
                  type="button"
                  disabled={loading}
                  onClick={(e) => {
                    e.stopPropagation();
                    store.selectOption(opt);
                    handleGenerate(
                      [
                        `Activity: ${opt.title}`,
                        `Approach: ${opt.description}`,
                        `Student task: ${opt.student_action_summary || opt.description}`,
                        `Teacher facilitation: ${opt.teacher_facilitation_summary || 'Facilitate student participation and outcome-focused discussion.'}`,
                        `Expected output: ${opt.expected_student_output || 'A student-created response demonstrating the allocated learning outcomes.'}`,
                        `Grouping: ${opt.student_grouping}`,
                      ].join('\n'),
                      false,
                      opt.title
                    );
                  }}
                  className="mt-auto w-full rounded-lg bg-indigo-600 px-3 py-2.5 text-xs font-extrabold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60 sm:mt-4"
                >
                  {loading && store.selectedOption?.id === opt.id ? 'Generating plan...' : 'Choose & Generate Plan'}
                </button>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
          <h3 className="font-extrabold text-slate-900">Your own activity</h3>
          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            Enter your custom idea or video simulation below. The generated lesson plan will build
            its introduction and closing assessment around this activity and the allocated learning outcomes.
          </p>
          <textarea
            rows={4}
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="e.g. Play a 3-minute clip of a municipal council debate, then ask student groups to draft two formal citizen complaints regarding road drainage..."
            className="mt-4 w-full rounded-lg border border-slate-300 bg-slate-50 p-3 text-sm outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-100"
          />
          <button
            type="button"
            disabled={loading || !customText.trim()}
            onClick={() => handleGenerate(customText, true)}
            className="mt-3 w-full rounded-lg bg-indigo-600 py-3 text-sm font-extrabold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Generating plan...' : 'Generate Plan From My Activity'}
          </button>
        </div>
      )}
    </div>
  );
}