'use client';

import React, { useState } from 'react';
import { FactCheckReport, AlignmentReport } from '@/services/lessonPlanApi';

export interface LessonDevelopmentStep {
  step_number: number;
  teacher_activities: string;
  student_activities: string;
  learning_teaching_method: string;
  learning_teaching_aids: string;
  assessment_and_feedback?: string;
  time_minutes: number;
  other?: string;
}

export interface LearnLessonPlan {
  lesson_plan_number?: string;
  page_no?: string;
  date?: string;
  grade: string;
  subject: string;
  time_allocation: string;
  competence: string;
  competence_level: string;
  lesson: string;
  unique_learning_outcome: string[];
  the_entrance: string;
  lesson_development_steps: LessonDevelopmentStep[];
  summary: string;
  assessment_and_feedback_whole_lesson: string;
  post_activity: string;
  information_sources?: string[];
  attachments?: string[];
  reflection?: string;
  supervisors_notes?: string;
}


interface Props {
  plan: LearnLessonPlan | any;
  factCheck?: FactCheckReport;
  alignment?: AlignmentReport;
  filename?: string;
  onEditInGenerator?: (plan: any) => void;
  onDeletePlan?: (filename: string) => void;
  allPlans?: (LearnLessonPlan | any)[];
  activePeriodIndex?: number;
  onPeriodChange?: (index: number) => void;
  activeViewTab?: 'viewer' | 'editor';
  onViewTabChange?: (tab: 'viewer' | 'editor') => void;
}

export default function LessonPlanViewer({
  plan,
  factCheck,
  alignment,
  filename,
  onEditInGenerator,
  onDeletePlan,
  allPlans,
  activePeriodIndex,
  onPeriodChange,
  activeViewTab = 'viewer',
  onViewTabChange,
}: Props) {
  const [copied, setCopied] = useState<boolean>(false);

  if (!plan) return null;

  const summaryText = plan.summary || (plan as any).Summary || '—';
  const isCivicPlan = String(plan.subject || '').trim().toLocaleLowerCase() === 'civic education';
  const wholeLessonAssessment =
    plan.assessment_and_feedback_whole_lesson ||
    (plan as any).assessmentAndFeedbackWholeLesson ||
    (plan as any).assessment_and_feedback ||
    '—';
  const postActivity = plan.post_activity || (plan as any).postActivity || '—';
  const rawInformationSources = plan.information_sources || (plan as any).informationSources;
  const informationSources = Array.isArray(rawInformationSources)
    ? rawInformationSources
        .filter((source: unknown): source is string => typeof source === 'string' && source.trim().length > 0)
        .map((source: string) => {
          const match = source.match(/^(.*?)(\s+\((?:page|pages)\s+[^)]+\))$/i);
          const sourceName = match ? match[1] : source;
          const sourcePath = sourceName.split(/[\\/]/).pop() || sourceName;
          return `${sourcePath}${match ? match[2] : ''}`;
        })
    : rawInformationSources;
  const attachmentsList = plan.attachments || (plan as any).Attachments;

  // Calculate total development minutes
  const totalDevMinutes =
    plan.lesson_development_steps?.reduce(
      (acc: number, step: LessonDevelopmentStep) => acc + (step.time_minutes || 0),
      0
    ) || 0;

  const handleCopyJson = () => {
    try {
      const jsonStr = JSON.stringify(plan, null, 2);
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(jsonStr);
      } else {
        const textArea = document.createElement('textarea');
        textArea.value = jsonStr;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy JSON:', e);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <article
      style={{
        backgroundColor: '#ffffff',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        maxWidth: '860px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      {/* Box Header (Matches View Saved Lesson Plan Box Header Style) */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f1f5f9',
          paddingBottom: '14px',
          gap: '12px',
        }}
      >
        <div>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '3px 10px',
              backgroundColor: '#eef2ff',
              borderRadius: '9999px',
              border: '1px solid #e0e7ff',
              color: '#4338ca',
              fontSize: '11px',
              fontWeight: '800',
              textTransform: 'uppercase',
              marginBottom: '4px',
            }}
          >
            <span>🏛️</span>
            <span>Education Science Division • LEARN Kandy</span>
          </div>
          <h3
            style={{
              fontSize: '16px',
              fontWeight: '800',
              color: '#0f172a',
              margin: '2px 0 0 0',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>📄</span>
            <span>
              View Lesson Plan — Level {plan.competence_level}
              {plan.period_number != null && ` • Period ${plan.period_number}${plan.total_periods ? ` of ${plan.total_periods}` : ''}`}
            </span>
          </h3>
          <p style={{ fontSize: '12px', color: '#64748b', margin: '3px 0 0 0', fontWeight: '500' }}>
            {plan.grade} • {plan.subject} • {plan.time_allocation}
            {filename && (
              <span
                style={{
                  marginLeft: '8px',
                  fontFamily: 'monospace',
                  backgroundColor: '#f1f5f9',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#475569',
                  border: '1px solid #e2e8f0',
                }}
              >
                {filename}
              </span>
            )}
          </p>
        </div>

        {/* Selected Activity for this Period (Only selected activity displayed) */}
        {(plan.selected_activity || plan.selected_activity_title || (Array.isArray(plan.activity_options) && plan.activity_options.length > 0)) && (
          <div
            style={{
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: '10px',
              padding: '12px 16px',
              fontSize: '12px',
              color: '#1e3a8a',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <strong style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#1e40af' }}>
                Selected Period Activity {plan.period_number ? `(Period ${plan.period_number})` : ''}
              </strong>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 800,
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  textTransform: 'uppercase',
                }}
              >
                Chosen Strategy
              </span>
            </div>

            <p style={{ margin: '4px 0 0 0', fontWeight: 800, fontSize: '14px', color: '#0f172a' }}>
              {plan.selected_activity_title || (Array.isArray(plan.activity_options) && plan.activity_options[0]?.title) || 'Selected Activity'}
            </p>

            {((Array.isArray(plan.activity_options) && plan.activity_options[0]?.description) || plan.selected_activity) && (
              <p style={{ margin: '6px 0 0 0', color: '#334155', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
                {(Array.isArray(plan.activity_options) && plan.activity_options[0]?.description) || plan.selected_activity}
              </p>
            )}

            {Array.isArray(plan.activity_options) && plan.activity_options[0]?.student_action_summary && (
              <p style={{ margin: '8px 0 0 0', color: '#475569', fontSize: '11px' }}>
                <strong>Student Participation: </strong>
                {plan.activity_options[0].student_action_summary}
              </p>
            )}

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
              {Array.isArray(plan.activity_options) && plan.activity_options[0]?.student_grouping && (
                <span style={{ backgroundColor: '#ffffff', border: '1px solid #cbd5e1', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', color: '#475569' }}>
                  <strong>Grouping:</strong> {plan.activity_options[0].student_grouping}
                </span>
              )}
              {Array.isArray(plan.activity_options) && plan.activity_options[0]?.pedagogy_type && (
                <span style={{ backgroundColor: '#ffffff', border: '1px solid #cbd5e1', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', color: '#475569' }}>
                  <strong>Pedagogy:</strong> {plan.activity_options[0].pedagogy_type}
                </span>
              )}
            </div>

            {plan.custom_teacher_activity && (
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed #bfdbfe', color: '#1e3a8a' }}>
                <strong>Teacher-provided notes: </strong>
                <span style={{ whiteSpace: 'pre-wrap' }}>{plan.custom_teacher_activity}</span>
              </div>
            )}
          </div>
        )}


        {/* Action Buttons in Header */}
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
            onClick={handlePrint}
            style={{
              padding: '7px 12px',
              fontSize: '12px',
              fontWeight: '700',
              color: '#334155',
              backgroundColor: '#f1f5f9',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background-color 0.2s',
            }}
            title="Print this lesson plan"
          >
            <span>🖨️</span>
            <span>Print</span>
          </button>
          <button
            type="button"
            onClick={handleCopyJson}
            style={{
              padding: '7px 12px',
              fontSize: '12px',
              fontWeight: '700',
              color: '#334155',
              backgroundColor: '#f1f5f9',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background-color 0.2s',
            }}
            title="Copy lesson plan data as JSON"
          >
            <span>{copied ? '✅' : '📋'}</span>
            <span>{copied ? 'Copied' : 'Copy JSON'}</span>
          </button>
          {onEditInGenerator && !onViewTabChange && (
            <button
              type="button"
              onClick={() => onEditInGenerator(plan)}
              style={{
                padding: '7px 12px',
                fontSize: '12px',
                fontWeight: '700',
                color: '#4338ca',
                backgroundColor: '#eef2ff',
                border: '1px solid #c7d2fe',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'background-color 0.2s',
              }}
              title="Load into Main Viewer and Structural Editor"
            >
              <span>✏️</span>
              <span>Edit in Generator</span>
            </button>
          )}
          {onDeletePlan && filename && (
            <button
              type="button"
              onClick={() => onDeletePlan(filename)}
              style={{
                padding: '7px 12px',
                fontSize: '12px',
                fontWeight: '700',
                color: '#dc2626',
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'background-color 0.2s',
              }}
              title="Delete this generated lesson plan permanently from storage"
            >
              <span>🗑️</span>
              <span>Delete Plan</span>
            </button>
          )}
        </div>
      </div>

      {/* Multi-Period Selector Bar if multiple periods exist */}
      {allPlans && allPlans.length > 1 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '10px',
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '8px 14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: '800',
                color: '#475569',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              📚 Sequential Periods:
            </span>
            {allPlans.map((p, idx) => {
              const pNum = p.period_number ?? (idx + 1);
              const isSelected = (activePeriodIndex ?? 0) === idx;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onPeriodChange?.(idx)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    border: isSelected ? '1px solid #4f46e5' : '1px solid #cbd5e1',
                    backgroundColor: isSelected ? '#4f46e5' : '#ffffff',
                    color: isSelected ? '#ffffff' : '#334155',
                    boxShadow: isSelected ? '0 2px 4px rgba(79, 70, 229, 0.25)' : 'none',
                    transition: 'all 0.15s ease',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <span>Period {pNum}</span>
                  <span
                    style={{
                      fontSize: '10px',
                      padding: '1px 6px',
                      borderRadius: '9999px',
                      backgroundColor: isSelected ? 'rgba(255,255,255,0.25)' : '#f1f5f9',
                      color: isSelected ? '#ffffff' : '#475569',
                      fontFamily: 'monospace',
                      fontWeight: 700,
                    }}
                  >
                    40m
                  </span>
                </button>
              );
            })}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>
            Viewing Period {(activePeriodIndex ?? 0) + 1} of {allPlans.length} (40 Min Lesson)
          </span>
        </div>
      )}

      {/* Optional Guardrails Summary Boxes */}
      {(factCheck || alignment) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          {factCheck && (
            <div
              style={{
                backgroundColor: factCheck.passed ? '#f0fdf4' : '#fffbeb',
                border: `1px solid ${factCheck.passed ? '#bbf7d0' : '#fde68a'}`,
                borderRadius: '10px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '12px', fontWeight: '700', color: factCheck.passed ? '#166534' : '#854d0e' }}>
                Grounding Score: {(factCheck.grounding_score * 100).toFixed(0)}% ({factCheck.passed ? 'Passed' : 'Review Needed'})
              </span>
            </div>
          )}
          {alignment && (
            <div
              style={{
                backgroundColor: alignment.passed_alignment_guardrail ? '#eff6ff' : '#fef2f2',
                border: `1px solid ${alignment.passed_alignment_guardrail ? '#bfdbfe' : '#fecaca'}`,
                borderRadius: '10px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '12px', fontWeight: '700', color: alignment.passed_alignment_guardrail ? '#1e40af' : '#991b1b' }}>
                Goal Alignment: {(alignment.overall_alignment_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* 1. Metadata Grid Boxes (Identical to Form Field Boxes) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '12px' }}>
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '10px 12px' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', letterSpacing: '0.05em' }}>Date</label>
          <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{plan.date || '—'}</span>
        </div>
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '10px 12px' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', letterSpacing: '0.05em' }}>Grade</label>
          <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', display: 'block' }}>{plan.grade || '—'}</span>
        </div>
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '10px 12px' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', letterSpacing: '0.05em' }}>Subject</label>
          <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{plan.subject || '—'}</span>
        </div>
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '10px 12px' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', letterSpacing: '0.05em' }}>Time</label>
          <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', display: 'block' }}>{plan.time_allocation || '—'}</span>
        </div>
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '10px 12px' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', letterSpacing: '0.05em' }}>Plan No</label>
          <span style={{ fontSize: '13px', fontWeight: '700', fontFamily: 'monospace', color: '#0f172a', display: 'block' }}>{plan.lesson_plan_number || '01'}</span>
        </div>
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '10px 12px' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#64748b', marginBottom: '4px', letterSpacing: '0.05em' }}>Page No</label>
          <span style={{ fontSize: '13px', fontWeight: '700', fontFamily: 'monospace', color: '#0f172a', display: 'block' }}>{plan.page_no || '01'}</span>
        </div>
      </div>

      {/* 2. Competence Box */}
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
          Competence
        </label>
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            padding: '12px 14px',
            fontSize: '14px',
            fontWeight: '600',
            color: '#1e293b',
            lineHeight: '1.6',
          }}
        >
          {plan.competence}
        </div>
      </div>

      {/* 3. Competency Level & Lesson Topic Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
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
            NIE Competence Level
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1.5px solid #6366f1',
              borderRadius: '10px',
              padding: '10px 14px',
              fontSize: '15px',
              fontWeight: '700',
              fontFamily: 'monospace',
              color: '#4338ca',
            }}
          >
            Level {plan.competence_level}
          </div>
        </div>

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
            Lesson
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '10px 14px',
              fontSize: '14px',
              fontWeight: '700',
              color: '#1e293b',
            }}
          >
            {plan.lesson}
          </div>
        </div>
      </div>

      {/* 4. Unique Learning Outcomes Box */}
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
          Unique Learning Outcomes ({plan.unique_learning_outcome?.length || 0})
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {plan.unique_learning_outcome?.map((outcome: string, idx: number) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                padding: '10px 14px',
              }}
            >
              <span
                style={{
                  flexShrink: 0,
                  width: '22px',
                  height: '22px',
                  borderRadius: '6px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  fontSize: '12px',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginTop: '1px',
                }}
              >
                {idx + 1}
              </span>
              <span style={{ fontSize: '13px', fontWeight: '500', color: '#1e293b', lineHeight: '1.5' }}>
                {outcome}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 5. The Entrance (Introduction) Box */}
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
          {isCivicPlan ? 'The Entrance (Introduction) — 5 Minutes' : 'The Entrance (Introduction)'}
        </label>
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            padding: '12px 14px',
            fontSize: '13px',
            fontWeight: '500',
            color: '#1e293b',
            lineHeight: '1.6',
            whiteSpace: 'pre-line',
          }}
        >
          {plan.the_entrance}
        </div>
      </div>

      {/* 6. Lesson Development (7-Column Schedule) Table Box */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: '#334155',
              letterSpacing: '0.05em',
            }}
          >
            Lesson Development Schedule ({plan.lesson_development_steps?.length || 0} Steps)
          </label>
          <span
            style={{
              fontSize: '11px',
              fontWeight: '700',
              color: '#4f46e5',
              backgroundColor: '#eef2ff',
              padding: '3px 8px',
              borderRadius: '6px',
            }}
          >
            ⏱️ {totalDevMinutes} Minutes Total
          </span>
        </div>

        <div style={{ border: '1px solid #cbd5e1', borderRadius: '10px', overflowX: 'auto', backgroundColor: '#ffffff' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
            <thead style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
              <tr>
                <th style={{ padding: '10px 8px', width: '48px', textAlign: 'center', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Step</th>
                <th style={{ padding: '10px 12px', minWidth: '160px', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Teacher Activities</th>
                <th style={{ padding: '10px 12px', minWidth: '160px', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Student Activities</th>
                <th style={{ padding: '10px 10px', minWidth: '110px', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Method</th>
                <th style={{ padding: '10px 10px', minWidth: '110px', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Aids</th>
                {!isCivicPlan && <th style={{ padding: '10px 10px', minWidth: '120px', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Assessment & Feedback</th>}
                <th style={{ padding: '10px 8px', width: '56px', textAlign: 'center', borderRight: '1px solid #e2e8f0', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Time</th>
                <th style={{ padding: '10px 8px', width: '60px', fontWeight: '700', color: '#334155', textTransform: 'uppercase', fontSize: '11px' }}>Other</th>
              </tr>
            </thead>
            <tbody>
              {plan.lesson_development_steps?.map((step: LessonDevelopmentStep, idx: number) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', verticalAlign: 'top', backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                  <td style={{ padding: '10px 8px', textAlign: 'center', borderRight: '1px solid #e2e8f0', fontWeight: '800', fontFamily: 'monospace', color: '#4f46e5' }}>
                    {step.step_number || idx + 1}
                  </td>
                  <td style={{ padding: '10px 12px', borderRight: '1px solid #e2e8f0', color: '#1e293b', lineHeight: '1.5', whiteSpace: 'pre-line' }}>
                    {step.teacher_activities}
                  </td>
                  <td style={{ padding: '10px 12px', borderRight: '1px solid #e2e8f0', color: '#1e293b', lineHeight: '1.5', whiteSpace: 'pre-line' }}>
                    {step.student_activities}
                  </td>
                  <td style={{ padding: '10px 10px', borderRight: '1px solid #e2e8f0', color: '#334155' }}>
                    <span style={{ display: 'inline-block', padding: '2px 8px', backgroundColor: '#e2e8f0', borderRadius: '6px', fontSize: '11px', fontWeight: '600' }}>
                      {step.learning_teaching_method}
                    </span>
                  </td>
                  <td style={{ padding: '10px 10px', borderRight: '1px solid #e2e8f0', color: '#475569', fontSize: '11px' }}>
                    {step.learning_teaching_aids}
                  </td>
                  {!isCivicPlan && <td style={{ padding: '10px 10px', borderRight: '1px solid #e2e8f0', color: '#475569', fontSize: '11px' }}>
                    {step.assessment_and_feedback}
                  </td>}
                  <td style={{ padding: '10px 8px', textAlign: 'center', borderRight: '1px solid #e2e8f0', fontWeight: '700', fontFamily: 'monospace', color: '#0f172a' }}>
                    {step.time_minutes}m
                  </td>
                  <td style={{ padding: '10px 8px', color: '#64748b', fontSize: '11px' }}>
                    {step.other || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 7. Summary & Whole Lesson Assessment Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
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
            Summary
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '13px',
              color: '#1e293b',
              lineHeight: '1.6',
            }}
          >
            {summaryText}
          </div>
        </div>

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
            {isCivicPlan ? 'Assessment & Closure (5 Minutes)' : 'Assessment & Feedback (Whole Lesson)'}
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '13px',
              color: '#1e293b',
              lineHeight: '1.6',
            }}
          >
            {wholeLessonAssessment}
          </div>
        </div>
      </div>

      {/* 8. Post Activity Box */}
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
          Post Activity (Relevant to the Lesson)
        </label>
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            padding: '12px 14px',
            fontSize: '13px',
            fontWeight: '500',
            color: '#1e293b',
            lineHeight: '1.6',
          }}
        >
          {postActivity}
        </div>
      </div>

      {/* 9. Retrieved curriculum document names and attachments */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
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
            Information Sources
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '12px',
              color: '#334155',
            }}
          >
            {Array.isArray(informationSources) && informationSources.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: '18px', lineHeight: '1.6' }}>
                {informationSources.map((source: string, idx: number) => (
                  <li key={idx}>{source}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0 }}>
                {typeof informationSources === 'string' && informationSources.trim()
                  ? informationSources
                  : 'No source metadata was returned for this generated plan.'}
              </p>
            )}
          </div>
        </div>

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
            Attachments
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '12px',
              color: '#334155',
            }}
          >
            {Array.isArray(attachmentsList) && attachmentsList.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: '18px', lineHeight: '1.6' }}>
                {attachmentsList.map((item: string, idx: number) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0, color: '#64748b' }}>None</p>
            )}
          </div>
        </div>
      </div>

      {/* Optional Reflection */}
      {plan.reflection && (
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
            Teacher Reflection
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '13px',
              color: '#1e293b',
            }}
          >
            {plan.reflection}
          </div>
        </div>
      )}

      {/* Optional Supervisor's Notes */}
      {plan.supervisors_notes && (
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
            Supervisor's Notes
          </label>
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '13px',
              color: '#1e293b',
            }}
          >
            {plan.supervisors_notes}
          </div>
        </div>
      )}
    </article>
  );
}