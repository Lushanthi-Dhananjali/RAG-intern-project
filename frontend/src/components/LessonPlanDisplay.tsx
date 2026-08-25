'use client';

import React, { useState } from 'react';
import { LessonPlanGenerateResponse, LessonPlanSchema } from '@/types/lessonPlan';

interface Props {
  data: LessonPlanGenerateResponse;
}

export default function LessonPlanDisplay({ data }: Props) {
  const [plan, setPlan] = useState<LessonPlanSchema>(data.lesson_plan);

  const handleTextChange = (field: keyof LessonPlanSchema, value: string) => {
    setPlan((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.fact_check_report && (
          <div className={`p-4 rounded-xl border ${data.fact_check_report.passed ? 'bg-green-50 border-green-200 text-green-800' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
            <h4 className="font-semibold text-sm">Grounding Score (Fact Check)</h4>
            <p className="text-2xl font-bold mt-1">
              {(data.fact_check_report.grounding_score * 100).toFixed(0)}%
            </p>
          </div>
        )}

        {data.alignment_report && (
          <div className={`p-4 rounded-xl border ${data.alignment_report.passed_alignment_guardrail ? 'bg-blue-50 border-blue-200 text-blue-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
            <h4 className="font-semibold text-sm">Pedagogical Alignment</h4>
            <p className="text-2xl font-bold mt-1">
              {(data.alignment_report.overall_alignment_score * 100).toFixed(0)}%
            </p>
          </div>
        )}
      </div>

      {/* Editable Lesson Card */}
      <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
        <div className="border-b pb-4 mb-4">
          <input
            type="text"
            value={plan.title}
            onChange={(e) => handleTextChange('title', e.target.value)}
            className="text-2xl font-extrabold text-gray-900 w-full border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none"
          />
          <div className="flex gap-4 mt-2 text-sm text-gray-500 font-medium">
            <span>Subject: {plan.subject}</span>
            <span>•</span>
            <span>Grade: {plan.grade_level}</span>
            <span>•</span>
            <span>Duration: {plan.estimated_duration_minutes} Mins</span>
          </div>
        </div>

        {/* Step 1: Goal */}
        <div className="mb-6">
          <h3 className="text-md font-bold text-gray-800 mb-2 uppercase tracking-wide">
            1. Educational Goal / Standard
          </h3>
          <p className="bg-gray-50 p-3 rounded-lg text-gray-700 border border-gray-100">
            {plan.educational_goal_or_standard}
          </p>
        </div>

        {/* Step 2: Learning Outcomes */}
        <div className="mb-6">
          <h3 className="text-md font-bold text-gray-800 mb-2 uppercase tracking-wide">
            2. Learning Outcomes
          </h3>
          <ul className="space-y-2">
            {plan.learning_outcomes.map((outcome) => (
              <li key={outcome.id} className="flex items-start gap-3 p-2 bg-blue-50/50 rounded-lg">
                <span className="font-bold text-blue-600">#{outcome.id}</span>
                <div className="flex-1">
                  <p className="text-gray-800 text-sm">{outcome.description}</p>
                  {outcome.blooms_taxonomy_level && (
                    <span className="text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-0.5 rounded mt-1 inline-block">
                      {outcome.blooms_taxonomy_level}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Step 3: Required Materials */}
        <div className="mb-6">
          <h3 className="text-md font-bold text-gray-800 mb-2 uppercase tracking-wide">
            3. Materials & Resources
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {plan.materials.map((mat, idx) => (
              <div key={idx} className="p-3 border rounded-lg flex justify-between items-center bg-gray-50">
                <div>
                  <p className="font-semibold text-sm text-gray-800">{mat.item_name}</p>
                  <p className="text-xs text-gray-500">Qty: {mat.quantity}</p>
                </div>
                {mat.is_digital && (
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">Digital</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step 4: Instructional Procedures */}
        <div className="mb-6">
          <h3 className="text-md font-bold text-gray-800 mb-2 uppercase tracking-wide">
            4. Sequential Procedures
          </h3>
          <div className="space-y-3">
            {plan.procedures.map((step) => (
              <div key={step.step_number} className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-blue-700 text-sm">
                    Step {step.step_number}: {step.phase_title}
                  </span>
                  <span className="text-xs text-gray-500 font-semibold bg-gray-100 px-2 py-1 rounded">
                    ⏱️ {step.duration_minutes} mins
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="bg-blue-50/30 p-2.5 rounded">
                    <strong className="block text-blue-900 mb-1">Teacher Action:</strong>
                    <p className="text-gray-700">{step.teacher_action}</p>
                  </div>
                  <div className="bg-emerald-50/30 p-2.5 rounded">
                    <strong className="block text-emerald-900 mb-1">Student Action:</strong>
                    <p className="text-gray-700">{step.student_action}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 5: Verification & Assessment */}
        <div>
          <h3 className="text-md font-bold text-gray-800 mb-2 uppercase tracking-wide">
            5. Assessment & Verification
          </h3>
          <div className="p-4 bg-amber-50/40 rounded-lg border border-amber-200 space-y-2 text-sm">
            <p><strong>Formative Assessment:</strong> {plan.verification.formative_assessment}</p>
            <p><strong>Alignment Verification:</strong> {plan.verification.alignment_check}</p>
          </div>
        </div>
      </div>
    </div>
  );
}