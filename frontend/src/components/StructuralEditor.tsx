'use client';

import React, { useState, useEffect } from 'react';
import {
  LessonPlanDto,
  LessonDevelopmentStepDto,
  saveGeneratedPlan,
} from '@/services/lessonPlanApi';

interface StructuralEditorProps {
  initialPlan: any;
  filename?: string;
  userId?: string;
  onSave?: (updatedPlan: any, savedFilename?: string) => void;
  activeViewTab?: 'viewer' | 'editor';
  onViewTabChange?: (tab: 'viewer' | 'editor') => void;
}

/**
 * Normalizes input plan data from either the Sri Lankan NIE & LEARN DTO
 * or legacy schemas into a structured LessonPlanDto format.
 */
function normalizeInitialPlan(p: any, fallbackFilename?: string): LessonPlanDto {
  if (!p) {
    return {
      grade: 'Grade 8',
      subject: 'Civic Education',
      time_allocation: '40 Minutes (1 Period)',
      competence: '',
      competence_level: '8.1.1',
      lesson: '',
      unique_learning_outcome: ['Explain key concepts accurately.'],
      the_entrance: '',
      lesson_development_steps: [
        {
          step_number: 1,
          time_minutes: 10,
          learning_teaching_method: 'Inquiry-based discussion',
          teacher_activities: '',
          student_activities: '',
          learning_teaching_aids: 'Textbook / Whiteboard',
          assessment_and_feedback: 'Teacher observation',
        },
      ],
      summary: '',
      assessment_and_feedback_whole_lesson: '',
      post_activity: '',
      information_sources: ['Civic Education Grade 8 Teacher Guide, NIE'],
    };
  }

  // 1. Unique Learning Outcomes normalization
  let outcomes: string[] = [];
  if (Array.isArray(p.unique_learning_outcome) && p.unique_learning_outcome.length > 0) {
    outcomes = p.unique_learning_outcome.map((o: any) =>
      typeof o === 'string' ? o : o.description || String(o)
    );
  } else if (Array.isArray(p.learning_outcomes) && p.learning_outcomes.length > 0) {
    outcomes = p.learning_outcomes.map((o: any) =>
      typeof o === 'string' ? o : o.description || String(o)
    );
  } else {
    outcomes = ['Explain key concepts accurately.'];
  }

  // 2. Lesson Development Steps normalization
  let steps: LessonDevelopmentStepDto[] = [];
  if (Array.isArray(p.lesson_development_steps) && p.lesson_development_steps.length > 0) {
    steps = p.lesson_development_steps.map((s: any, idx: number) => ({
      step_number: s.step_number || idx + 1,
      time_minutes: Number(s.time_minutes) || 10,
      learning_teaching_method: s.learning_teaching_method || 'Interactive Teaching',
      teacher_activities: s.teacher_activities || '',
      student_activities: s.student_activities || '',
      learning_teaching_aids: s.learning_teaching_aids || 'Textbook / Whiteboard',
      assessment_and_feedback: s.assessment_and_feedback || 'Teacher observation',
      other: s.other || '',
    }));
  } else if (Array.isArray(p.procedures) && p.procedures.length > 0) {
    steps = p.procedures.map((proc: any, idx: number) => ({
      step_number: proc.step_number || idx + 1,
      time_minutes: Number(proc.duration_minutes) || 10,
      learning_teaching_method: proc.phase_title || 'Guided Activity',
      teacher_activities: proc.teacher_action || '',
      student_activities: proc.student_action || '',
      learning_teaching_aids: 'Textbook / Board',
      assessment_and_feedback: 'Formative observation',
      other: '',
    }));
  } else {
    steps = [
      {
        step_number: 1,
        time_minutes: 10,
        learning_teaching_method: 'Inquiry-based discussion',
        teacher_activities: '',
        student_activities: '',
        learning_teaching_aids: 'Textbook / Whiteboard',
        assessment_and_feedback: 'Teacher observation',
      },
    ];
  }

  // 3. Information Sources normalization
  let sources: string[] = [];
  if (Array.isArray(p.information_sources) && p.information_sources.length > 0) {
    sources = p.information_sources.map((s: any) => String(s));
  } else if (Array.isArray(p.materials) && p.materials.length > 0) {
    sources = p.materials.map((m: any) => m.item_name || String(m));
  } else {
    sources = ['Civic Education Grade 8 Teacher Guide, NIE'];
  }

  return {
    grade: p.grade || p.grade_level || 'Grade 8',
    subject: p.subject || 'Civic Education',
    time_allocation:
      p.time_allocation ||
      (p.estimated_duration_minutes
        ? `${p.estimated_duration_minutes} Minutes`
        : '40 Minutes (1 Period)'),
    competence: p.competence || p.educational_goal_or_standard || p.topic || '',
    competence_level: p.competence_level || '8.1.1',
    lesson: p.lesson || p.title || p.topic || '',
    unique_learning_outcome: outcomes,
    the_entrance: p.the_entrance || (p.procedures?.[0]?.teacher_action) || '',
    lesson_development_steps: steps,
    summary: p.summary || p.verification?.summative_assessment || '',
    assessment_and_feedback_whole_lesson:
      p.assessment_and_feedback_whole_lesson ||
      p.verification?.formative_assessment ||
      '',
    post_activity: p.post_activity || 'Students complete assigned textbook activities.',
    information_sources: sources,
    attachments: p.attachments || [],
    period_number: p.period_number,
    total_periods: p.total_periods,
    selected_activity: p.selected_activity,
    selected_activity_title: p.selected_activity_title,
    custom_teacher_activity: p.custom_teacher_activity,
    activity_options: p.activity_options,
    outcome_allocation: p.outcome_allocation,
    entrance_duration_minutes: p.entrance_duration_minutes,
    assignment_duration_minutes: p.assignment_duration_minutes,
    filename: p?.filename || fallbackFilename,
  };
}

export default function StructuralEditor({
  initialPlan,
  filename,
  userId,
  onSave,
  activeViewTab = 'editor',
  onViewTabChange,
}: StructuralEditorProps) {
  const [plan, setPlan] = useState<LessonPlanDto>(() => normalizeInitialPlan(initialPlan, filename));
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Sync state whenever external initialPlan prop updates
  useEffect(() => {
    if (initialPlan) {
      setPlan(normalizeInitialPlan(initialPlan, filename));
    }
  }, [initialPlan]);

  // Direct field modifier
  const handleFieldChange = (field: keyof LessonPlanDto, value: any) => {
    setPlan((prev) => ({ ...prev, [field]: value }));
  };

  // --- 1. Unique Learning Outcomes Handlers ---
  const handleOutcomeChange = (index: number, text: string) => {
    setPlan((prev) => {
      const updated = [...prev.unique_learning_outcome];
      updated[index] = text;
      return { ...prev, unique_learning_outcome: updated };
    });
  };

  const handleAddOutcome = () => {
    setPlan((prev) => ({
      ...prev,
      unique_learning_outcome: [
        ...prev.unique_learning_outcome,
        'Demonstrates understanding of key concepts through practical examples.',
      ],
    }));
  };

  const handleRemoveOutcome = (index: number) => {
    setPlan((prev) => {
      if (prev.unique_learning_outcome.length <= 1) return prev;
      return {
        ...prev,
        unique_learning_outcome: prev.unique_learning_outcome.filter((_, i) => i !== index),
      };
    });
  };

  // --- 2. Development Steps Handlers ---
  const handleStepChange = (
    index: number,
    field: keyof LessonDevelopmentStepDto,
    value: any
  ) => {
    setPlan((prev) => {
      const updated = [...prev.lesson_development_steps];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, lesson_development_steps: updated };
    });
  };

  const handleAddStep = () => {
    setPlan((prev) => {
      const nextStepNum = prev.lesson_development_steps.length + 1;
      return {
        ...prev,
        lesson_development_steps: [
          ...prev.lesson_development_steps,
          {
            step_number: nextStepNum,
            time_minutes: 10,
            learning_teaching_method: 'Guided Activity & Discussion',
            teacher_activities: 'Teacher guides students through the learning activity.',
            student_activities: 'Students engage actively in group discussion and record findings.',
            learning_teaching_aids: 'Worksheets / Textbook',
            assessment_and_feedback: 'Teacher checks student understanding through targeted questions.',
          },
        ],
      };
    });
  };

  const handleRemoveStep = (index: number) => {
    setPlan((prev) => {
      if (prev.lesson_development_steps.length <= 1) return prev;
      const filtered = prev.lesson_development_steps.filter((_, i) => i !== index);
      // Renumber steps sequentially
      const renumbered = filtered.map((step, idx) => ({
        ...step,
        step_number: idx + 1,
      }));
      return { ...prev, lesson_development_steps: renumbered };
    });
  };

  // --- 3. Information Sources Handlers ---
  const handleSourceChange = (index: number, text: string) => {
    setPlan((prev) => {
      const updated = [...(prev.information_sources || [])];
      updated[index] = text;
      return { ...prev, information_sources: updated };
    });
  };

  const handleAddSource = () => {
    setPlan((prev) => ({
      ...prev,
      information_sources: [...(prev.information_sources || []), 'Teacher Guide & Resource Book, NIE'],
    }));
  };

  const handleRemoveSource = (index: number) => {
    setPlan((prev) => {
      const current = prev.information_sources || [];
      if (current.length <= 1) return prev;
      return {
        ...prev,
        information_sources: current.filter((_, i) => i !== index),
      };
    });
  };

  // --- Save Plan to FastAPI Backend Storage & Notify Parent ---
  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus(null);

    // Create a dual-compatible plan object with both NIE/LEARN DTO fields and legacy schema aliases
    const comprehensivePlan: any = {
      ...plan,
      // Legacy schema aliases for backwards compatibility
      title: plan.lesson || plan.competence,
      topic: plan.lesson || plan.competence,
      grade_level: plan.grade,
      educational_goal_or_standard: plan.competence,
      estimated_duration_minutes:
        plan.lesson_development_steps.reduce((acc, s) => acc + (s.time_minutes || 0), 0) || 40,
      learning_outcomes: plan.unique_learning_outcome.map((uo, idx) => ({
        id: idx + 1,
        description: uo,
        blooms_taxonomy_level: 'Apply',
      })),
      procedures: plan.lesson_development_steps.map((s) => ({
        step_number: s.step_number,
        phase_title: s.learning_teaching_method,
        duration_minutes: s.time_minutes,
        teacher_action: s.teacher_activities,
        student_action: s.student_activities,
      })),
      materials: (plan.information_sources || []).map((src) => ({
        item_name: src,
        quantity: '1',
        is_digital: false,
      })),
      verification: {
        formative_assessment: plan.assessment_and_feedback_whole_lesson,
        summative_assessment: plan.summary,
        alignment_check: 'Aligned with Sri Lankan NIE & LEARN standards',
      },
    };

    const targetFilename =
      filename ||
      plan.filename ||
      initialPlan?.filename ||
      (plan.period_number != null
        ? `${(plan.grade || 'Grade 8').replace(/\s+/g, '_')}_comp_${(plan.competence_level || 'custom').replace(/\./g, '_')}_p${plan.period_number}.json`
        : `${(plan.grade || 'Grade 8').replace(/\s+/g, '_')}_comp_${(plan.competence_level || 'custom').replace(/\./g, '_')}.json`);

    try {
      const res = await saveGeneratedPlan(comprehensivePlan, targetFilename);
      const savedName = res.filename || targetFilename;
      setSaveStatus({
        type: 'success',
        message: `✅ Lesson plan saved successfully as "${savedName}"!`,
      });
      if (onSave) {
        onSave(comprehensivePlan, savedName);
      }
    } catch (err: any) {
      setSaveStatus({
        type: 'error',
        message: `❌ Failed to save: ${err.message || 'Unknown error occurred'}`,
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        maxWidth: '860px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      {/* Panel Header matching LessonPlanForm */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f1f5f9',
          paddingBottom: '14px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h3
            style={{
              fontSize: '16px',
              fontWeight: '800',
              color: '#0f172a',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              margin: 0,
            }}
          >
            <span>✏️</span>
            <span>Structural Lesson Plan Editor</span>
          </h3>
          <p style={{ fontSize: '12px', color: '#64748b', margin: '3px 0 0 0' }}>
            Directly customize NIE & LEARN curriculum parameters, development steps, and assessment in real-time
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {onViewTabChange && (
            <div
              style={{
                display: 'inline-flex',
                padding: '3px',
                backgroundColor: '#f1f5f9',
                borderRadius: '10px',
                border: '1px solid #e2e8f0',
              }}
            >
              <button
                type="button"
                onClick={() => onViewTabChange('viewer')}
                style={{
                  padding: '6px 14px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  border: 'none',
                  backgroundColor: activeViewTab === 'viewer' ? '#4f46e5' : 'transparent',
                  color: activeViewTab === 'viewer' ? '#ffffff' : '#475569',
                  boxShadow: activeViewTab === 'viewer' ? '0 2px 4px rgba(79, 70, 229, 0.25)' : 'none',
                  transition: 'all 0.15s ease',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>📄</span>
                <span>Table Viewer</span>
              </button>
              <button
                type="button"
                onClick={() => onViewTabChange('editor')}
                style={{
                  padding: '6px 14px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  border: 'none',
                  backgroundColor: activeViewTab === 'editor' ? '#4f46e5' : 'transparent',
                  color: activeViewTab === 'editor' ? '#ffffff' : '#475569',
                  boxShadow: activeViewTab === 'editor' ? '0 2px 4px rgba(79, 70, 229, 0.25)' : 'none',
                  transition: 'all 0.15s ease',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>✏️</span>
                <span>Structural Editor</span>
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            style={{
              padding: '9px 18px',
              borderRadius: '10px',
              backgroundColor: isSaving ? '#94a3b8' : '#059669',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '13px',
              border: 'none',
              cursor: isSaving ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 2px 4px rgba(5, 150, 105, 0.2)',
              transition: 'all 0.2s ease',
            }}
          >
            {isSaving ? (
              <>
                <span>⏳</span>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <span>💾</span>
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Save Notification Feedback Banner */}
      {saveStatus && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '10px',
            fontSize: '13px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: saveStatus.type === 'success' ? '#ecfdf5' : '#fef2f2',
            color: saveStatus.type === 'success' ? '#065f46' : '#991b1b',
            border: `1px solid ${saveStatus.type === 'success' ? '#a7f3d0' : '#fecaca'}`,
          }}
        >
          <span>{saveStatus.message}</span>
          <button
            type="button"
            onClick={() => setSaveStatus(null)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'inherit',
              fontWeight: 'bold',
              fontSize: '14px',
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* =================================================================== */}
      {/* 1. CURRICULUM PARAMETERS & LESSON IDENTITY                          */}
      {/* =================================================================== */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px' }}>🏛️</span>
          <span style={{ fontSize: '13px', fontWeight: '800', color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            1. Curriculum & Lesson Parameters
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
          {/* Subject */}
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: '700',
                textTransform: 'uppercase',
                color: '#334155',
                marginBottom: '6px',
                letterSpacing: '0.05em',
              }}
            >
              Subject
            </label>
            <select
              value={plan.subject}
              onChange={(e) => handleFieldChange('subject', e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#1e293b',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            >
              <option value="Civic Education">🏛️ Civic Education</option>
              <option value="Science">🧪 Science</option>
            </select>
          </div>

          {/* Grade Level */}
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: '700',
                textTransform: 'uppercase',
                color: '#334155',
                marginBottom: '6px',
                letterSpacing: '0.05em',
              }}
            >
              Grade Level
            </label>
            <select
              value={plan.grade}
              onChange={(e) => handleFieldChange('grade', e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#1e293b',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            >
              <option value="Grade 6">Grade 6</option>
              <option value="Grade 7">Grade 7</option>
              <option value="Grade 8">Grade 8</option>
              <option value="Grade 9">Grade 9</option>
            </select>
          </div>

          {/* Competence Level Code */}
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: '700',
                textTransform: 'uppercase',
                color: '#334155',
                marginBottom: '6px',
                letterSpacing: '0.05em',
              }}
            >
              Competence Level
            </label>
            <input
              type="text"
              value={plan.competence_level}
              onChange={(e) => handleFieldChange('competence_level', e.target.value)}
              placeholder="e.g. 8.1.1"
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#ffffff',
                border: '1.5px solid #6366f1',
                borderRadius: '10px',
                fontSize: '14px',
                fontWeight: '600',
                fontFamily: 'monospace',
                color: '#4338ca',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Time Allocation */}
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: '700',
                textTransform: 'uppercase',
                color: '#334155',
                marginBottom: '6px',
                letterSpacing: '0.05em',
              }}
            >
              Time Allocation
            </label>
            <input
              type="text"
              value={plan.time_allocation}
              onChange={(e) => handleFieldChange('time_allocation', e.target.value)}
              placeholder="e.g. 40 Minutes (1 Period)"
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                fontSize: '14px',
                fontWeight: '500',
                color: '#1e293b',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>
        </div>

        {/* Lesson Topic Title */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: '#334155',
              marginBottom: '6px',
              letterSpacing: '0.05em',
            }}
          >
            Lesson Topic (Title)
          </label>
          <input
            type="text"
            value={plan.lesson}
            onChange={(e) => handleFieldChange('lesson', e.target.value)}
            placeholder="Enter the lesson topic title..."
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '700',
              color: '#0f172a',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Competence Statement */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: '#334155',
              marginBottom: '6px',
              letterSpacing: '0.05em',
            }}
          >
            Competence Statement
          </label>
          <textarea
            rows={2}
            value={plan.competence}
            onChange={(e) => handleFieldChange('competence', e.target.value)}
            placeholder="Overall curriculum competence goal..."
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: '500',
              color: '#1e293b',
              outline: 'none',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
          />
        </div>
      </div>

      {/* =================================================================== */}
      {/* 2. THE ENTRANCE (ENGAGEMENT HOOK & PRIOR KNOWLEDGE)                 */}
      {/* =================================================================== */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px' }}>🚪</span>
          <span style={{ fontSize: '13px', fontWeight: '800', color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            2. The Entrance (Hook & Prior Knowledge Recall)
          </span>
        </div>
        <textarea
          rows={3}
          value={plan.the_entrance}
          onChange={(e) => handleFieldChange('the_entrance', e.target.value)}
          placeholder="Describe how the teacher opens the lesson, engages student interest, and connects to prior knowledge..."
          style={{
            width: '100%',
            padding: '10px 14px',
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            fontSize: '13px',
            fontWeight: '500',
            color: '#1e293b',
            outline: 'none',
            boxSizing: 'border-box',
            resize: 'vertical',
          }}
        />
      </div>

      {/* =================================================================== */}
      {/* 3. UNIQUE LEARNING OUTCOMES (BLOOM'S TAXONOMY)                     */}
      {/* =================================================================== */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '14px' }}>🎯</span>
            <span style={{ fontSize: '13px', fontWeight: '800', color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              3. Unique Learning Outcomes (Bloom&apos;s Taxonomy)
            </span>
          </div>
          <button
            type="button"
            onClick={handleAddOutcome}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              backgroundColor: '#eef2ff',
              color: '#4338ca',
              fontWeight: '700',
              fontSize: '12px',
              border: '1px solid #c7d2fe',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>+</span>
            <span>Add Outcome</span>
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {plan.unique_learning_outcome.map((outcome, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: '800',
                  color: '#4338ca',
                  backgroundColor: '#e0e7ff',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  minWidth: '32px',
                  textAlign: 'center',
                }}
              >
                #{idx + 1}
              </span>
              <input
                type="text"
                value={outcome}
                onChange={(e) => handleOutcomeChange(idx, e.target.value)}
                placeholder="Specific measurable learning outcome..."
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '10px',
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#1e293b',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
              <button
                type="button"
                onClick={() => handleRemoveOutcome(idx)}
                title="Remove Outcome"
                disabled={plan.unique_learning_outcome.length <= 1}
                style={{
                  padding: '8px 12px',
                  borderRadius: '8px',
                  backgroundColor: plan.unique_learning_outcome.length <= 1 ? '#f1f5f9' : '#fee2e2',
                  color: plan.unique_learning_outcome.length <= 1 ? '#94a3b8' : '#dc2626',
                  fontWeight: '700',
                  fontSize: '13px',
                  border: `1px solid ${plan.unique_learning_outcome.length <= 1 ? '#e2e8f0' : '#fecaca'}`,
                  cursor: plan.unique_learning_outcome.length <= 1 ? 'not-allowed' : 'pointer',
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* =================================================================== */}
      {/* 4. LESSON DEVELOPMENT STEPS (MULTI-PERIOD INSTRUCTIONAL TABLE)      */}
      {/* =================================================================== */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px' }}>⏱️</span>
              <span style={{ fontSize: '13px', fontWeight: '800', color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                4. Lesson Development Steps (Instructional Procedures)
              </span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '2px 0 0 0' }}>
              Detailed teacher/student actions, methods, aids, and continuous assessment per step
            </p>
          </div>
          <button
            type="button"
            onClick={handleAddStep}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              backgroundColor: '#eef2ff',
              color: '#4338ca',
              fontWeight: '700',
              fontSize: '12px',
              border: '1px solid #c7d2fe',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>+</span>
            <span>Add Step</span>
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {plan.lesson_development_steps.map((step, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#ffffff',
                padding: '16px',
                borderRadius: '12px',
                border: '1px solid #cbd5e1',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              {/* Step Header Row */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid #f1f5f9',
                  paddingBottom: '10px',
                  flexWrap: 'wrap',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      fontSize: '12px',
                      fontWeight: '800',
                      color: '#ffffff',
                      backgroundColor: '#4338ca',
                      borderRadius: '8px',
                      padding: '4px 10px',
                    }}
                  >
                    Step {step.step_number}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: '#64748b' }}>
                      Duration:
                    </span>
                    <input
                      type="number"
                      min={1}
                      max={180}
                      value={step.time_minutes}
                      onChange={(e) =>
                        handleStepChange(idx, 'time_minutes', parseInt(e.target.value) || 0)
                      }
                      style={{
                        width: '64px',
                        padding: '4px 8px',
                        backgroundColor: '#f8fafc',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '700',
                        color: '#1e293b',
                        textAlign: 'center',
                      }}
                    />
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Mins</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleRemoveStep(idx)}
                  disabled={plan.lesson_development_steps.length <= 1}
                  title="Remove Step"
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    backgroundColor:
                      plan.lesson_development_steps.length <= 1 ? '#f1f5f9' : '#fee2e2',
                    color: plan.lesson_development_steps.length <= 1 ? '#94a3b8' : '#dc2626',
                    fontWeight: '700',
                    fontSize: '12px',
                    border: `1px solid ${
                      plan.lesson_development_steps.length <= 1 ? '#e2e8f0' : '#fecaca'
                    }`,
                    cursor:
                      plan.lesson_development_steps.length <= 1 ? 'not-allowed' : 'pointer',
                  }}
                >
                  ✕ Remove
                </button>
              </div>

              {/* Teaching Method */}
              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '11px',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    color: '#475569',
                    marginBottom: '4px',
                    letterSpacing: '0.05em',
                  }}
                >
                  Learning / Teaching Method
                </label>
                <input
                  type="text"
                  value={step.learning_teaching_method}
                  onChange={(e) =>
                    handleStepChange(idx, 'learning_teaching_method', e.target.value)
                  }
                  placeholder="e.g. Inquiry-based discussion, Group activity, Brainstorming"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: '#f8fafc',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: '#0f172a',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              {/* 2-Column: Teacher Activities vs Student Activities */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
                <div>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '11px',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      color: '#1d4ed8',
                      marginBottom: '4px',
                      letterSpacing: '0.05em',
                    }}
                  >
                    Teacher Activities
                  </label>
                  <textarea
                    rows={3}
                    value={step.teacher_activities}
                    onChange={(e) =>
                      handleStepChange(idx, 'teacher_activities', e.target.value)
                    }
                    placeholder="Specific actions and explanations provided by the teacher..."
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '500',
                      color: '#1e293b',
                      outline: 'none',
                      boxSizing: 'border-box',
                      resize: 'vertical',
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '11px',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      color: '#047857',
                      marginBottom: '4px',
                      letterSpacing: '0.05em',
                    }}
                  >
                    Student Activities
                  </label>
                  <textarea
                    rows={3}
                    value={step.student_activities}
                    onChange={(e) =>
                      handleStepChange(idx, 'student_activities', e.target.value)
                    }
                    placeholder="Active tasks, discussions, and responses by students..."
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '500',
                      color: '#1e293b',
                      outline: 'none',
                      boxSizing: 'border-box',
                      resize: 'vertical',
                    }}
                  />
                </div>
              </div>

              {/* 2-Column: Aids/Resources vs Continuous Assessment */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
                <div>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '11px',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      color: '#475569',
                      marginBottom: '4px',
                      letterSpacing: '0.05em',
                    }}
                  >
                    Learning / Teaching Aids
                  </label>
                  <input
                    type="text"
                    value={step.learning_teaching_aids}
                    onChange={(e) =>
                      handleStepChange(idx, 'learning_teaching_aids', e.target.value)
                    }
                    placeholder="e.g. Textbook page 42, Charts, Board"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '500',
                      color: '#1e293b',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '11px',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      color: '#475569',
                      marginBottom: '4px',
                      letterSpacing: '0.05em',
                    }}
                  >
                    Continuous Assessment & Feedback
                  </label>
                  <input
                    type="text"
                    value={step.assessment_and_feedback}
                    onChange={(e) =>
                      handleStepChange(idx, 'assessment_and_feedback', e.target.value)
                    }
                    placeholder="e.g. Teacher observes student group responses and guides"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '500',
                      color: '#1e293b',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* =================================================================== */}
      {/* 5. SUMMARY, ASSESSMENT & POST-ACTIVITY                              */}
      {/* =================================================================== */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px' }}>📝</span>
          <span style={{ fontSize: '13px', fontWeight: '800', color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            5. Summary & Lesson Evaluation
          </span>
        </div>

        {/* Lesson Summary */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: '#334155',
              marginBottom: '6px',
              letterSpacing: '0.05em',
            }}
          >
            Summary of Key Concepts
          </label>
          <textarea
            rows={3}
            value={plan.summary}
            onChange={(e) => handleFieldChange('summary', e.target.value)}
            placeholder="Recap of major learning points covered in the lesson..."
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: '500',
              color: '#1e293b',
              outline: 'none',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
          />
        </div>

        {/* Whole Lesson Assessment & Feedback */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: '#334155',
              marginBottom: '6px',
              letterSpacing: '0.05em',
            }}
          >
            Assessment and Feedback (Whole Lesson)
          </label>
          <textarea
            rows={3}
            value={plan.assessment_and_feedback_whole_lesson}
            onChange={(e) =>
              handleFieldChange('assessment_and_feedback_whole_lesson', e.target.value)
            }
            placeholder="Summative evaluation criteria, question set, or rubric used to verify outcome mastery..."
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: '500',
              color: '#1e293b',
              outline: 'none',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
          />
        </div>

        {/* Post Activity / Homework */}
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: '#334155',
              marginBottom: '6px',
              letterSpacing: '0.05em',
            }}
          >
            Post Activity / Extended Assignment
          </label>
          <textarea
            rows={2}
            value={plan.post_activity}
            onChange={(e) => handleFieldChange('post_activity', e.target.value)}
            placeholder="Homework, field observation, or follow-up activity..."
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: '500',
              color: '#1e293b',
              outline: 'none',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
          />
        </div>
      </div>

      {/* =================================================================== */}
      {/* 6. INFORMATION SOURCES & CURRICULUM REFERENCES                      */}
      {/* =================================================================== */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '14px' }}>📚</span>
            <span style={{ fontSize: '13px', fontWeight: '800', color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              6. Information Sources & References
            </span>
          </div>
          <button
            type="button"
            onClick={handleAddSource}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              backgroundColor: '#eef2ff',
              color: '#4338ca',
              fontWeight: '700',
              fontSize: '12px',
              border: '1px solid #c7d2fe',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>+</span>
            <span>Add Source</span>
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {(plan.information_sources || []).map((source, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="text"
                value={source}
                onChange={(e) => handleSourceChange(idx, e.target.value)}
                placeholder="e.g. Civic Education Grade 8 Teacher's Guide, NIE"
                style={{
                  flex: 1,
                  padding: '9px 12px',
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#1e293b',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
              <button
                type="button"
                onClick={() => handleRemoveSource(idx)}
                disabled={(plan.information_sources || []).length <= 1}
                style={{
                  padding: '8px 12px',
                  borderRadius: '8px',
                  backgroundColor:
                    (plan.information_sources || []).length <= 1 ? '#f1f5f9' : '#fee2e2',
                  color:
                    (plan.information_sources || []).length <= 1 ? '#94a3b8' : '#dc2626',
                  fontWeight: '700',
                  fontSize: '13px',
                  border: `1px solid ${
                    (plan.information_sources || []).length <= 1 ? '#e2e8f0' : '#fecaca'
                  }`,
                  cursor:
                    (plan.information_sources || []).length <= 1 ? 'not-allowed' : 'pointer',
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Save Action Button */}
      <button
        type="button"
        onClick={handleSave}
        disabled={isSaving}
        style={{
          width: '100%',
          marginTop: '6px',
          padding: '12px 16px',
          borderRadius: '10px',
          backgroundColor: isSaving ? '#94a3b8' : '#059669',
          color: '#ffffff',
          fontWeight: '700',
          fontSize: '14px',
          border: 'none',
          cursor: isSaving ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          boxShadow: '0 2px 4px rgba(5, 150, 105, 0.2)',
        }}
      >
        {isSaving ? (
          <>
            <span className="animate-spin inline-block">⏳</span>
            <span>Saving Lesson Plan...</span>
          </>
        ) : (
          <>
            <span>💾</span>
            <span>Save Changes &amp; Update Lesson Plan</span>
          </>
        )}
      </button>
    </div>
  );
}