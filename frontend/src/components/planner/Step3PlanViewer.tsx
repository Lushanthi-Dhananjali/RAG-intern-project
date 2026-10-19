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
        previousPeriodActivities: store.previousPeriodActivities,
      });

      store.setOptions(options);
      store.nextPeriod();
    } catch (err: any) {
      alert(`Could not fetch options for Period ${nextP}: ${err.message}`);
    } finally {
      setLoadingNext(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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
      <div className="bg-white border rounded-xl p-8 shadow-sm space-y-6">
        <div className="border-b pb-4">
          <span className="text-xs font-bold text-blue-600 tracking-wider uppercase">
            {currentPlan.time_allocation}
          </span>
          <h1 className="text-2xl font-extrabold text-gray-900 mt-1">{currentPlan.lesson}</h1>
          <p className="text-sm text-gray-500">
            {currentPlan.subject} | {currentPlan.grade} | Competency: {currentPlan.competence_level}
          </p>
        </div>

        <div>
          <h4 className="text-sm font-bold text-gray-700 uppercase">Verbatim NIE Learning Outcomes:</h4>
          <ul className="list-disc pl-5 mt-2 space-y-1 text-sm text-gray-800">
            {currentPlan.unique_learning_outcome.map((o, idx) => (
              <li key={idx}>{o}</li>
            ))}
          </ul>
        </div>

        <div className="bg-amber-50/60 border border-amber-200 p-4 rounded-lg">
          <h4 className="text-sm font-bold text-amber-900">Phase 1: The Entrance (5 Minutes)</h4>
          <p className="text-sm text-gray-700 mt-1">{currentPlan.the_entrance}</p>
        </div>

        <div>
          <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">
            Phase 2: Lesson Development (Strict 30 Minutes)
          </h4>
          <div className="space-y-4 mt-3">
            {currentPlan.lesson_development_steps.map((st) => (
              <div key={st.step_number} className="border p-4 rounded-lg bg-gray-50">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-sm text-gray-800">
                    Step {st.step_number}: {st.learning_teaching_method}
                  </span>
                  <span className="text-xs bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded">
                    {st.time_minutes} Mins
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                  <div><strong>Teacher:</strong> {st.teacher_activities}</div>
                  <div><strong>Student:</strong> {st.student_activities}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-emerald-50/60 border border-emerald-200 p-4 rounded-lg">
          <h4 className="text-sm font-bold text-emerald-900">
            Phase 3: Assessment & Closure (5 Minutes)
          </h4>
          <p className="text-sm text-gray-700 mt-1">
            {currentPlan.assessment_and_feedback_whole_lesson}
          </p>
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