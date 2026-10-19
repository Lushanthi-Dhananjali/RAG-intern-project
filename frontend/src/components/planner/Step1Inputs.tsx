'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { fetchPedagogicalOptions } from '@/services/lessonPlanApi';

export default function Step1Inputs() {
  const store = useLessonPlanStore();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
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
        previousPeriodActivities: store.previousPeriodActivities,
      });
      store.setOptions(options);
    } catch (err: any) {
      alert(`Discovery failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-md border space-y-6">
      <div className="border-b pb-4">
        <h2 className="text-xl font-bold text-gray-900">Step 1: Curriculum & Class Configuration</h2>
        <p className="text-sm text-gray-500">Sri Lankan NIE Civic Education (Grades 6–9)</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700">Competency Level</label>
          <input
            type="text"
            value={store.competencyLevel}
            onChange={(e) => store.setInputs({ competencyLevel: e.target.value })}
            placeholder="e.g. 8.1.1"
            className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700">Grade Level</label>
          <select
            value={store.gradeLevel}
            onChange={(e) => store.setInputs({ gradeLevel: e.target.value })}
            className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="Grade 6">Grade 6</option>
            <option value="Grade 7">Grade 7</option>
            <option value="Grade 8">Grade 8</option>
            <option value="Grade 9">Grade 9</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700">Total Periods for Level (Max 4)</label>
          <input
            type="number"
            min={1}
            max={4}
            value={store.totalPeriods}
            onChange={(e) => store.setInputs({ totalPeriods: Number(e.target.value) })}
            className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700">Student Count ($N$)</label>
          <input
            type="number"
            min={5}
            max={80}
            value={store.studentCount}
            onChange={(e) => store.setInputs({ studentCount: Number(e.target.value) })}
            className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            required
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg shadow transition"
      >
        {loading ? 'Discovering Curriculum Boundaries...' : `Proceed to Period ${store.currentPeriod} Activity Options →`}
      </button>
    </form>
  );
}