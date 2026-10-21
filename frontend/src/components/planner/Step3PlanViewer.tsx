'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { fetchPedagogicalOptions } from '@/services/lessonPlanApi';

export default function Step3PlanViewer() {
  const store = useLessonPlanStore();
  const [loadingNext, setLoadingNext] = useState(false);
  const currentPlan = store.generatedPlans[store.currentPeriod];

  if (!currentPlan) {
    return <div>No plan found for Period {store.currentPeriod}.</div>;
  }

  const handleNextPeriodClick = async () => {
    setLoadingNext(true);
    const nextP = store.currentPeriod + 1;
    try {
      const options = await fetchPedagogicalOptions({
        competencyLevel: store.competencyLevel,
        studentCount: store.studentCount,
        periods: store.totalPeriods,
        requestedPeriod: nextP,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(nextP),
      });

      store.setOptions(options);
      store.nextPeriod();
    } catch (err: any) {
      alert(`Could not fetch options for Period ${nextP}: ${err.message}`);
    } finally {
      setLoadingNext(false);
    }
  };

  const handleChangeActivity = async () => {
    setLoadingNext(true);
    try {
      const options = await fetchPedagogicalOptions({
        competencyLevel: store.competencyLevel,
        studentCount: store.studentCount,
        periods: store.totalPeriods,
        requestedPeriod: store.currentPeriod,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.otherActivityTitles(store.currentPeriod),
      });
      store.setOptions(options);
    } catch (err: any) {
      alert(`Could not fetch new options for Period ${store.currentPeriod}: ${err.message}`);
    } finally {
      setLoadingNext(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Sequence Tabs */}
      <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2">
        {Array.from({ length: store.totalPeriods }).map((_, idx) => {
          const pNum = idx + 1;
          const isDone = !!store.generatedPlans[pNum];
          return (
            <button
              key={pNum}
              onClick={() => store.previousPeriod(pNum)}
              disabled={!isDone}
              className={`rounded-lg border px-3 py-2 text-xs font-extrabold transition sm:text-sm ${
                store.currentPeriod === pNum
                  ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                  : isDone
                  ? 'border-slate-200 bg-white text-slate-700 hover:border-indigo-200 hover:bg-indigo-50'
                  : 'cursor-not-allowed border-slate-100 bg-slate-100 text-slate-400'
              }`}
            >
              Period {pNum} {isDone ? '✓' : ''}
            </button>
          );
        })}
      </div>

      {/* Plan Document Container */}
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-2 rounded-lg border border-indigo-100 bg-indigo-50/50 p-3 sm:flex-row sm:items-center">
          <div>
            <p className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-indigo-700">Generated lesson plan</p>
            <p className="mt-0.5 text-xs text-slate-600">This period is saved automatically in the Generated Plans Library.</p>
          </div>
          <span className="w-fit rounded-full border border-indigo-200 bg-white px-3 py-1 text-[11px] font-extrabold text-indigo-800">
            Period {store.currentPeriod} of {store.totalPeriods}
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Subject</span>
            <p className="mt-1 font-bold text-slate-900">{currentPlan.subject}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Competency Level</span>
            <p className="mt-1 font-bold text-slate-900">{currentPlan.competence_level}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Time</span>
            <p className="mt-1 font-bold text-slate-900">{currentPlan.time_allocation}</p>
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-[10px] font-extrabold uppercase tracking-wide text-slate-500">Lesson focus</p>
          <h1 className="mt-1 text-xl font-extrabold text-slate-900">{currentPlan.lesson}</h1>
          {store.activityByPeriod[store.currentPeriod] && (
            <p className="mt-2 text-sm text-indigo-800">
              <strong>Selected activity:</strong> {store.activityByPeriod[store.currentPeriod]}
            </p>
          )}
        </div>

        <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-4">
          <h4 className="text-xs font-extrabold uppercase tracking-wide text-indigo-900">Teacher Guide Learning Outcomes</h4>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed text-slate-800">
            {currentPlan.unique_learning_outcome.map((o, idx) => (
              <li key={idx}>{o}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-sm font-extrabold text-amber-950">The Entrance — Introduction</h4>
            <span className="rounded-full border border-amber-200 bg-white px-2.5 py-1 text-[10px] font-bold text-amber-900">5 Minutes</span>
          </div>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-700">{currentPlan.the_entrance}</p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-sm font-extrabold uppercase tracking-wide text-slate-900">Lesson Development</h4>
            <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold text-slate-700">30 Minutes</span>
          </div>
          <div className="space-y-4 mt-3">
            {currentPlan.lesson_development_steps.map((st) => (
              <div key={st.step_number} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
                <h5 className="mb-3 flex items-center gap-2 font-extrabold text-sm text-slate-800">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-xs text-indigo-800">{st.step_number}</span>
                  Development Step
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-[10px] uppercase tracking-wide text-slate-500">Teacher Activities</strong>
                    <p className="mt-1 text-xs leading-relaxed text-slate-800">{st.teacher_activities}</p>
                  </div>
                  <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-3">
                    <strong className="block text-[10px] uppercase tracking-wide text-indigo-700">Student Activities</strong>
                    <p className="mt-1 text-xs leading-relaxed text-slate-800">{st.student_activities}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-[10px] uppercase tracking-wide text-slate-500">Learning and Teaching Method</strong>
                    <p className="mt-1 text-xs leading-relaxed text-slate-800">{st.learning_teaching_method}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-[10px] uppercase tracking-wide text-slate-500">Learning and Teaching Aids</strong>
                    <p className="mt-1 text-xs leading-relaxed text-slate-800">{st.learning_teaching_aids}</p>
                  </div>
                  <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-3">
                    <strong className="block text-[10px] uppercase tracking-wide text-indigo-700">Time</strong>
                    <p className="mt-1 text-xs font-bold text-slate-800">{st.time_minutes} Minutes</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={handleChangeActivity}
          disabled={loadingNext}
          className="w-full rounded-lg border border-indigo-300 bg-white py-3 text-sm font-bold text-indigo-700 transition hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loadingNext ? 'Loading period-specific options...' : `Choose a different activity for Period ${store.currentPeriod}`}
        </button>

        <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-sm font-extrabold text-indigo-950">Assessment & Closure</h4>
            <span className="rounded-full border border-indigo-200 bg-white px-2.5 py-1 text-[10px] font-bold text-indigo-900">5 Minutes</span>
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="rounded-lg border border-indigo-100 bg-white/80 p-3">
              <strong className="text-xs uppercase tracking-wide text-indigo-700">Closure Summary</strong>
              <p className="mt-1 text-sm text-gray-700 whitespace-pre-line">{currentPlan.summary}</p>
            </div>
            <div className="rounded-lg border border-indigo-100 bg-white/80 p-3">
              <strong className="text-xs uppercase tracking-wide text-indigo-700">Generated Assessment</strong>
              <p className="mt-1 text-sm text-gray-700 whitespace-pre-line">
                {currentPlan.assessment_and_feedback_whole_lesson}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Sequential Progression Action Button */}
      {store.currentPeriod < store.totalPeriods ? (
        <button
          onClick={handleNextPeriodClick}
          disabled={loadingNext}
          className="w-full rounded-lg bg-indigo-600 py-3.5 text-sm font-extrabold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loadingNext
            ? `Querying Fresh Options for Period ${store.currentPeriod + 1}...`
            : `Plan Next Period (Period ${store.currentPeriod + 1} of ${store.totalPeriods}) →`}
        </button>
      ) : (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-center font-extrabold text-emerald-800">
          🎉 All {store.totalPeriods} Periods for Competency {store.competencyLevel} Successfully Completed!
        </div>
      )}
    </div>
  );
}