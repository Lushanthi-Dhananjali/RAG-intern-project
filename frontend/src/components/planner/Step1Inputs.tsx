'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { fetchPedagogicalOptions } from '@/services/lessonPlanApi';

export default function Step1Inputs() {
  const store = useLessonPlanStore();
  const [loading, setLoading] = useState(false);
  const supportedGrades = ['Grade 6', 'Grade 7', 'Grade 8', 'Grade 9'];
  const selectedGrade = supportedGrades.includes(store.gradeLevel)
    ? store.gradeLevel
    : 'Grade 8';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const options = await fetchPedagogicalOptions({
        competencyLevel: store.competencyLevel,
        studentCount: store.studentCount,
        periods: store.totalPeriods,
        requestedPeriod: store.currentPeriod,
        gradeLevel: selectedGrade,
        subject: store.subject,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(store.currentPeriod),
      });
      if (store.gradeLevel !== selectedGrade) {
        store.setInputs({ gradeLevel: selectedGrade });
      }
      store.setOptions(options);
    } catch (err: any) {
      alert(`Discovery failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mx-auto w-full max-w-4xl space-y-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-lg sm:p-8">
      <div className="flex items-start gap-4 border-b border-slate-100 pb-5">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50 text-2xl">
          🏛️
        </span>
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-emerald-700">Multi-Period Lesson Planner</p>
          <h2 className="mt-1 text-xl font-extrabold text-slate-900 sm:text-2xl">Curriculum & Class Configuration</h2>
          <p className="mt-1 text-sm text-slate-500">Set the competency, class size, and period sequence for Civic Education (Grades 6–9).</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-600">Competency Level</label>
          <input
            type="text"
            value={store.competencyLevel}
            onChange={(e) => store.setInputs({ competencyLevel: e.target.value })}
            placeholder="e.g. 8.1.1"
            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-mono font-semibold text-slate-800 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            required
          />
          <p className="mt-2 text-xs text-slate-500">Use the competency code from the Teacher Guide.</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-600">Grade Level</label>
          <select
            value={selectedGrade}
            onChange={(e) => store.setInputs({ gradeLevel: e.target.value })}
            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-semibold text-slate-800 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          >
            <option value="Grade 6">Grade 6</option>
            <option value="Grade 7">Grade 7</option>
            <option value="Grade 8">Grade 8</option>
            <option value="Grade 9">Grade 9</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-600">Periods for this Competency Level <span className="text-emerald-700">(Max 4)</span></label>
          <input
            type="number"
            min={1}
            max={4}
            value={store.totalPeriods}
            onChange={(e) => store.setInputs({ totalPeriods: Number(e.target.value) })}
            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-semibold text-slate-800 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            required
          />
          <p className="mt-2 text-xs text-slate-500">Each period is planned separately in a sequence.</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-600">Student Count</label>
          <input
            type="number"
            min={5}
            max={80}
            value={store.studentCount}
            onChange={(e) => store.setInputs({ studentCount: Number(e.target.value) })}
            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-semibold text-slate-800 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            required
          />
          <p className="mt-2 text-xs text-slate-500">Activity options are tailored to your class size.</p>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-700 py-3.5 font-bold text-white shadow-md transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? 'Retrieving curriculum and activities...' : `Get Period ${store.currentPeriod} Activity Options →`}
      </button>
    </form>
  );
}