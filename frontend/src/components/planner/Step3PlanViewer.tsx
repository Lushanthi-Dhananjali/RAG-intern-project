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
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Sequence Tabs */}
      <div className="flex gap-2 border-b pb-2">
        {Array.from({ length: store.totalPeriods }).map((_, idx) => {
          const pNum = idx + 1;
          const isDone = !!store.generatedPlans[pNum];
          return (
            <button
              key={pNum}
              onClick={() => store.previousPeriod(pNum)}
              disabled={!isDone}
              className={`px-4 py-2 rounded-lg text-sm font-bold ${
                store.currentPeriod === pNum
                  ? 'bg-blue-600 text-white'
                  : isDone
                  ? 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  : 'bg-gray-50 text-gray-400 cursor-not-allowed'
              }`}
            >
              Period {pNum} {isDone ? '✓' : ''}
            </button>
          );
        })}
      </div>

      {/* Plan Document Container */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-8 shadow-sm space-y-6">
        <p className="text-sm text-emerald-700 font-medium">
          This period plan is saved automatically in the Generated Plans Library.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Subject</span>
            <p className="mt-1 font-bold text-slate-900">{currentPlan.subject}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Competency Level</span>
            <p className="mt-1 font-bold text-slate-900">{currentPlan.competence_level}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Time</span>
            <p className="mt-1 font-bold text-slate-900">{currentPlan.time_allocation}</p>
          </div>
        </div>
        <div className="border-b border-slate-200 pb-4">
          <h1 className="text-2xl font-extrabold text-gray-900">{currentPlan.lesson}</h1>
          {store.activityByPeriod[store.currentPeriod] && (
            <p className="text-sm text-blue-800 mt-2">
              <strong>Selected activity:</strong> {store.activityByPeriod[store.currentPeriod]}
            </p>
          )}
        </div>

        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
          <h4 className="text-sm font-bold text-emerald-900 uppercase">Teacher Guide Learning Outcomes</h4>
          <ul className="list-disc pl-5 mt-2 space-y-1 text-sm text-gray-800">
            {currentPlan.unique_learning_outcome.map((o, idx) => (
              <li key={idx}>{o}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4">
          <h4 className="text-sm font-bold text-amber-900">The Entrance — Introduction (5 Minutes)</h4>
          <p className="text-sm text-gray-700 mt-2 whitespace-pre-line">{currentPlan.the_entrance}</p>
        </div>

        <div>
          <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">
            Lesson Development (30 Minutes)
          </h4>
          <div className="space-y-4 mt-3">
            {currentPlan.lesson_development_steps.map((st) => (
              <div key={st.step_number} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h5 className="mb-3 font-bold text-sm text-gray-800">Step {st.step_number}</h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-xs uppercase tracking-wide text-slate-500">Teacher Activities</strong>
                    <p className="mt-1 text-slate-800">{st.teacher_activities}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-xs uppercase tracking-wide text-slate-500">Student Activities</strong>
                    <p className="mt-1 text-slate-800">{st.student_activities}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-xs uppercase tracking-wide text-slate-500">Learning and Teaching Method</strong>
                    <p className="mt-1 text-slate-800">{st.learning_teaching_method}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <strong className="block text-xs uppercase tracking-wide text-slate-500">Learning and Teaching Aids</strong>
                    <p className="mt-1 text-slate-800">{st.learning_teaching_aids}</p>
                  </div>
                  <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-3">
                    <strong className="block text-xs uppercase tracking-wide text-blue-700">Time</strong>
                    <p className="mt-1 font-bold text-slate-800">{st.time_minutes} Minutes</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={handleChangeActivity}
          disabled={loadingNext}
          className="w-full bg-white border border-blue-300 text-blue-700 font-semibold py-3 rounded-xl hover:bg-blue-50 disabled:opacity-50"
        >
          {loadingNext ? 'Loading period-specific options...' : `Choose a different activity for Period ${store.currentPeriod}`}
        </button>

        <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-4">
          <h4 className="text-sm font-bold text-indigo-900">Assessment & Closure (5 Minutes)</h4>
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
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 rounded-xl shadow-lg transition"
        >
          {loadingNext
            ? `Querying Fresh Options for Period ${store.currentPeriod + 1}...`
            : `Plan Next Period (Period ${store.currentPeriod + 1} of ${store.totalPeriods}) →`}
        </button>
      ) : (
        <div className="p-4 bg-green-100 text-green-800 rounded-xl font-bold text-center">
          🎉 All {store.totalPeriods} Periods for Competency {store.competencyLevel} Successfully Completed!
        </div>
      )}
    </div>
  );
}