'use client';

import React, { useState } from 'react';
import {
  LessonPlanSchema,
  LearningOutcome,
  MaterialItem,
  ProcedureStep,
} from '@/types/lessonPlan';

interface StructuralEditorProps {
  initialPlan: LessonPlanSchema;
  userId?: string;
  onSave?: (updatedPlan: LessonPlanSchema) => void;
}

export default function StructuralEditor({
  initialPlan,
  userId,
  onSave,
}: StructuralEditorProps) {
  const [plan, setPlan] = useState<LessonPlanSchema>(initialPlan);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // --- Header Field Handlers ---
  const handleFieldChange = (field: keyof LessonPlanSchema, value: any) => {
    setPlan((prev) => ({ ...prev, [field]: value }));
  };

  // --- 1. Learning Outcomes Handlers ---
  const updateOutcome = (id: number, description: string) => {
    setPlan((prev) => ({
      ...prev,
      learning_outcomes: prev.learning_outcomes.map((o) =>
        o.id === id ? { ...o, description } : o
      ),
    }));
  };

  const addOutcome = () => {
    const newId = plan.learning_outcomes.length + 1;
    setPlan((prev) => ({
      ...prev,
      learning_outcomes: [
        ...prev.learning_outcomes,
        { id: newId, description: '', blooms_taxonomy_level: 'Understand' },
      ],
    }));
  };

  const removeOutcome = (id: number) => {
    setPlan((prev) => ({
      ...prev,
      learning_outcomes: prev.learning_outcomes.filter((o) => o.id !== id),
    }));
  };

  // --- 2. Materials Handlers ---
  const updateMaterial = (
    index: number,
    field: keyof MaterialItem,
    value: any
  ) => {
    setPlan((prev) => {
      const updated = [...prev.materials];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, materials: updated };
    });
  };

  const addMaterial = () => {
    setPlan((prev) => ({
      ...prev,
      materials: [
        ...prev.materials,
        { item_name: '', quantity: '1', is_digital: false },
      ],
    }));
  };

  const removeMaterial = (index: number) => {
    setPlan((prev) => ({
      ...prev,
      materials: prev.materials.filter((_, i) => i !== index),
    }));
  };

  // --- 3. Procedure Step Handlers ---
  const updateProcedure = (
    index: number,
    field: keyof ProcedureStep,
    value: any
  ) => {
    setPlan((prev) => {
      const updated = [...prev.procedures];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, procedures: updated };
    });
  };

  const addProcedureStep = () => {
    const nextStepNum = plan.procedures.length + 1;
    setPlan((prev) => ({
      ...prev,
      procedures: [
        ...prev.procedures,
        {
          step_number: nextStepNum,
          phase_title: 'Guided Activity',
          duration_minutes: 10,
          teacher_action: '',
          student_action: '',
        },
      ],
    }));
  };

  const removeProcedureStep = (index: number) => {
    setPlan((prev) => ({
      ...prev,
      procedures: prev.procedures
        .filter((_, i) => i !== index)
        .map((step, i) => ({ ...step, step_number: i + 1 })),
    }));
  };

  // --- Save Plan to ASP.NET Core / MySQL Database ---
  const handleSaveToDatabase = async () => {
    setIsSaving(true);
    setSaveStatus(null);

    try {
      const response = await fetch('http://localhost:5161/api/v1/lessonplan/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: userId || null,
          title: plan.title,
          gradeLevel: plan.grade_level,
          topic: plan.topic,
          planJsonData: JSON.stringify(plan),
        }),
      });

      if (!response.ok) throw new Error('Failed to persist lesson plan.');

      setSaveStatus('✅ Lesson plan saved successfully to MySQL!');
      if (onSave) onSave(plan);
    } catch (err: any) {
      setSaveStatus(`❌ Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 space-y-8">
      {/* Top Controls & Status Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b pb-4 gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-gray-900 flex items-center gap-2">
            <span>📝</span> Structural Lesson Plan Editor
          </h2>
          <p className="text-xs text-gray-500">
            Modify objectives, materials, and step-by-step procedures in real-time.
          </p>
        </div>

        <button
          onClick={handleSaveToDatabase}
          disabled={isSaving}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-5 rounded-lg shadow transition flex items-center gap-2"
        >
          {isSaving ? 'Saving...' : '💾 Save Changes'}
        </button>
      </div>

      {saveStatus && (
        <div
          className={`p-3 text-sm rounded-lg border ${
            saveStatus.includes('✅')
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {saveStatus}
        </div>
      )}

      {/* Basic Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-3">
          <label className="block text-xs font-bold text-gray-600 uppercase mb-1">
            Lesson Title
          </label>
          <input
            type="text"
            value={plan.title}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            className="w-full p-2.5 border border-gray-300 rounded-lg text-lg font-bold text-gray-800 focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-gray-600 uppercase mb-1">
            Subject
          </label>
          <input
            type="text"
            value={plan.subject}
            onChange={(e) => handleFieldChange('subject', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg text-sm text-gray-800"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-gray-600 uppercase mb-1">
            Grade Level
          </label>
          <input
            type="text"
            value={plan.grade_level}
            onChange={(e) => handleFieldChange('grade_level', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg text-sm text-gray-800"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-gray-600 uppercase mb-1">
            Duration (Minutes)
          </label>
          <input
            type="number"
            value={plan.estimated_duration_minutes}
            onChange={(e) =>
              handleFieldChange(
                'estimated_duration_minutes',
                parseInt(e.target.value) || 0
              )
            }
            className="w-full p-2 border border-gray-300 rounded-lg text-sm text-gray-800"
          />
        </div>
      </div>

      {/* --- SECTION 1: LEARNING OBJECTIVES --- */}
      <section className="bg-gray-50 p-5 rounded-xl border border-gray-200">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-md font-bold text-gray-800 uppercase tracking-wide">
            1. Learning Outcomes & Objectives
          </h3>
          <button
            onClick={addOutcome}
            className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            + Add Objective
          </button>
        </div>

        <div className="space-y-3">
          {plan.learning_outcomes.map((outcome) => (
            <div
              key={outcome.id}
              className="flex gap-3 items-center bg-white p-3 rounded-lg border border-gray-200"
            >
              <span className="font-bold text-sm text-blue-600">
                #{outcome.id}
              </span>
              <input
                type="text"
                value={outcome.description}
                onChange={(e) => updateOutcome(outcome.id, e.target.value)}
                placeholder="Enter learning objective description..."
                className="flex-1 p-2 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 text-gray-800"
              />
              <button
                onClick={() => removeOutcome(outcome.id)}
                className="text-red-500 hover:text-red-700 text-sm px-2"
                title="Remove Objective"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* --- SECTION 2: MATERIALS & RESOURCES --- */}
      <section className="bg-gray-50 p-5 rounded-xl border border-gray-200">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-md font-bold text-gray-800 uppercase tracking-wide">
            2. Required Materials
          </h3>
          <button
            onClick={addMaterial}
            className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            + Add Material
          </button>
        </div>

        <div className="space-y-3">
          {plan.materials.map((material, idx) => (
            <div
              key={idx}
              className="grid grid-cols-12 gap-3 items-center bg-white p-3 rounded-lg border border-gray-200"
            >
              <input
                type="text"
                value={material.item_name}
                onChange={(e) =>
                  updateMaterial(idx, 'item_name', e.target.value)
                }
                placeholder="Item Name (e.g. Whiteboard, Worksheets)"
                className="col-span-6 p-2 text-sm border border-gray-300 rounded text-gray-800"
              />
              <input
                type="text"
                value={material.quantity}
                onChange={(e) =>
                  updateMaterial(idx, 'quantity', e.target.value)
                }
                placeholder="Qty"
                className="col-span-3 p-2 text-sm border border-gray-300 rounded text-gray-800"
              />
              <label className="col-span-2 flex items-center gap-1.5 text-xs font-semibold text-gray-600">
                <input
                  type="checkbox"
                  checked={material.is_digital}
                  onChange={(e) =>
                    updateMaterial(idx, 'is_digital', e.target.checked)
                  }
                  className="rounded text-blue-600"
                />
                Digital
              </label>
              <button
                onClick={() => removeMaterial(idx)}
                className="col-span-1 text-red-500 hover:text-red-700 text-sm text-right"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* --- SECTION 3: STEP-BY-STEP PROCEDURES --- */}
      <section className="bg-gray-50 p-5 rounded-xl border border-gray-200">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-md font-bold text-gray-800 uppercase tracking-wide">
            3. Instructional Procedures
          </h3>
          <button
            onClick={addProcedureStep}
            className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            + Add Step
          </button>
        </div>

        <div className="space-y-4">
          {plan.procedures.map((step, idx) => (
            <div
              key={idx}
              className="bg-white p-4 rounded-xl border border-gray-300 shadow-sm space-y-3"
            >
              <div className="flex justify-between items-center border-b pb-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-blue-700 text-sm">
                    Step {step.step_number}
                  </span>
                  <input
                    type="text"
                    value={step.phase_title}
                    onChange={(e) =>
                      updateProcedure(idx, 'phase_title', e.target.value)
                    }
                    placeholder="Phase Title (e.g. Introduction, Group Discussion)"
                    className="font-semibold text-sm text-gray-800 border-b border-gray-200 focus:border-blue-500 focus:outline-none p-1"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 font-semibold">
                      ⏱️ Mins:
                    </span>
                    <input
                      type="number"
                      value={step.duration_minutes}
                      onChange={(e) =>
                        updateProcedure(
                          idx,
                          'duration_minutes',
                          parseInt(e.target.value) || 0
                        )
                      }
                      className="w-16 p-1 text-xs border border-gray-300 rounded text-gray-800"
                    />
                  </div>
                  <button
                    onClick={() => removeProcedureStep(idx)}
                    className="text-red-500 hover:text-red-700 text-sm font-bold"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-bold text-blue-900 mb-1">
                    Teacher Action
                  </label>
                  <textarea
                    rows={3}
                    value={step.teacher_action}
                    onChange={(e) =>
                      updateProcedure(idx, 'teacher_action', e.target.value)
                    }
                    className="w-full p-2 border border-gray-300 rounded text-gray-800 focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block font-bold text-emerald-900 mb-1">
                    Student Action
                  </label>
                  <textarea
                    rows={3}
                    value={step.student_action}
                    onChange={(e) =>
                      updateProcedure(idx, 'student_action', e.target.value)
                    }
                    className="w-full p-2 border border-gray-300 rounded text-gray-800 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}