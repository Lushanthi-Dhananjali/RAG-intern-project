'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { generateSinglePeriodPlan } from '@/services/lessonPlanApi';

export default function Step2OptionsSelection() {
  const store = useLessonPlanStore();
  const [loading, setLoading] = useState(false);
  const [customMode, setCustomMode] = useState(false);
  const [customText, setCustomText] = useState('');

  const handleGenerate = async (selectedDesc?: string, isCustom = false, activityTitle?: string) => {
    setLoading(true);
    const chosenTitle = isCustom
      ? `Teacher approach: ${customText.trim()}`
      : (activityTitle || 'Selected Strategy');
    try {
      const plan = await generateSinglePeriodPlan({
        competencyLevel: store.competencyLevel,
        periods: store.totalPeriods,
        requestedPeriod: store.currentPeriod,
        studentCount: store.studentCount,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        teacherMode: isCustom ? 'own_approach' : 'suggested',
        selectedActivityOption: selectedDesc,
        customTeacherActivity: isCustom ? customText : undefined,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(store.currentPeriod),
      });

      store.setGeneratedPlan(store.currentPeriod, plan, chosenTitle);
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center bg-blue-50 border border-blue-200 p-4 rounded-xl">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wide">
            Sequence Progress
          </span>
          <h2 className="text-lg font-bold text-gray-900">
            Planning Period {store.currentPeriod} of {store.totalPeriods} (40-Minute Block)
          </h2>
          {store.priorActivityTitles(store.currentPeriod).length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Previous activities avoided: {store.priorActivityTitles(store.currentPeriod).join(', ')}
            </p>
          )}
        </div>
        <button
          onClick={() => setCustomMode(!customMode)}
          className="text-sm font-semibold bg-white border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 shadow-sm"
        >
          {customMode ? '← Use AI Activity Cards' : 'Switch to Mode B (My Own Idea)'}
        </button>
      </div>

      {!customMode ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {store.currentOptions.map((opt) => (
            <div
              key={opt.id}
              onClick={() => store.selectOption(opt)}
              className={`p-6 rounded-xl border-2 transition cursor-pointer flex flex-col justify-between ${
                store.selectedOption?.id === opt.id
                  ? 'border-blue-600 bg-blue-50/40 shadow-md'
                  : 'border-gray-200 bg-white hover:border-blue-300'
              }`}
            >
              <div>
                <span className="inline-block text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-700 mb-2">
                  {opt.pedagogy_type}
                </span>
                <h3 className="font-bold text-gray-900 mb-2">{opt.title}</h3>
                <p className="text-xs text-gray-600 leading-relaxed mb-4">{opt.description}</p>
                {opt.learning_outcomes_addressed && opt.learning_outcomes_addressed.length > 0 && (
                  <div className="mb-4 text-xs text-gray-600">
                    <strong>Period {store.currentPeriod} learning outcomes:</strong>
                    <ul className="list-disc pl-4 mt-1">
                      {opt.learning_outcomes_addressed.map((outcome, index) => (
                        <li key={index}>{outcome}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="border-t pt-3 space-y-1 text-xs text-gray-500">
                  <p><strong>Grouping:</strong> {opt.student_grouping}</p>
                </div>
              </div>
              <button
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
                className="mt-6 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold shadow"
              >
                {loading && store.selectedOption?.id === opt.id ? 'Assembling...' : 'Assemble 40m Plan →'}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white p-6 rounded-xl border space-y-4">
          <h3 className="font-bold text-gray-900">Mode B: Teacher's Own Approach</h3>
          <p className="text-xs text-gray-500">
            Enter your custom idea or video simulation below. The generated lesson plan will build
            its introduction and closing assessment around this activity and the allocated learning outcomes.
          </p>
          <textarea
            rows={4}
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="e.g. Play a 3-minute clip of a municipal council debate, then ask student groups to draft two formal citizen complaints regarding road drainage..."
            className="w-full p-3 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <button
            disabled={loading || !customText.trim()}
            onClick={() => handleGenerate(customText, true)}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold text-sm shadow transition"
          >
            {loading ? 'Scaffolding Plan...' : 'Scaffold My Custom Idea into LEARN Plan →'}
          </button>
        </div>
      )}
    </div>
  );
}