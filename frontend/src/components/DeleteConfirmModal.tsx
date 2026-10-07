'use client';

import React, { useEffect, useMemo, useRef } from 'react';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  filename: string;
  planTitle?: string;
  grade?: string;
  subject?: string;
  competenceLevel?: string;
  timeAllocation?: string;
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function DeleteConfirmModal({
  isOpen,
  filename,
  planTitle = '',
  grade,
  subject,
  competenceLevel,
  timeAllocation,
  isDeleting,
  onConfirm,
  onCancel,
}: DeleteConfirmModalProps) {
  const boxRef = useRef<HTMLElement>(null);

  // Smooth scroll into view when opened directly below View Lesson Plan box
  useEffect(() => {
    if (isOpen && boxRef.current) {
      boxRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isOpen]);

  // Derive display values with smart fallbacks from filename
  const displayGrade = useMemo(() => {
    if (grade && grade.trim()) return grade;
    const match = filename.match(/Grade[_\s]*([0-9]+)/i);
    return match ? `Grade ${match[1]}` : 'Grade 8';
  }, [grade, filename]);

  const displayCompetency = useMemo(() => {
    if (competenceLevel && competenceLevel.trim()) return competenceLevel;
    const match = filename.match(/comp[_\s]*([0-9_]+)/i);
    if (match) return match[1].replace(/_/g, '.');
    return '8.1.1';
  }, [competenceLevel, filename]);

  const displaySubject = useMemo(() => {
    if (subject && subject.trim() && subject !== 'All') return subject;
    if (/science/i.test(filename)) return 'Science';
    if (/civic/i.test(filename)) return 'Civic Education';
    return 'Civic Education';
  }, [subject, filename]);

  const displayTime = useMemo(() => {
    if (timeAllocation && timeAllocation.trim()) return timeAllocation;
    return '40 Minutes';
  }, [timeAllocation]);

  const displayTitle = useMemo(() => {
    if (planTitle && planTitle.trim()) return planTitle;
    return `Competency ${displayCompetency}`;
  }, [planTitle, displayCompetency]);

  if (!isOpen) return null;

  return (
    <section
      ref={boxRef}
      id="delete-lesson-plan-box"
      aria-labelledby="delete-box-title"
      style={{
        maxWidth: '860px',
        margin: '20px auto 0 auto', // 20px gap between View Lesson Plan box and Delete Lesson Plan box, middle center aligned in page
        width: '100%',
        boxSizing: 'border-box',
      }}
      className="animate-in fade-in slide-in-from-top-3 duration-200"
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1.5px solid #fecaca',
          boxShadow: '0 4px 12px -2px rgba(220, 38, 38, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04)',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '18px',
          width: '100%',
          boxSizing: 'border-box',
          position: 'relative',
        }}
      >
        {/* Top Header Row with Icon, Title and Close Button */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #fee2e2',
            paddingBottom: '14px',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '12px',
                backgroundColor: '#fef2f2',
                border: '1px solid #fee2e2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px',
                boxShadow: '0 2px 6px rgba(239, 68, 68, 0.12)',
                flexShrink: 0,
              }}
            >
              🗑️
            </div>
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '2px 9px',
                  backgroundColor: '#fef2f2',
                  borderRadius: '9999px',
                  border: '1px solid #fecaca',
                  color: '#dc2626',
                  fontSize: '10.5px',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '2px',
                }}
              >
                <span>⚠️</span>
                <span>Permanent Removal</span>
              </div>
              <h3
                id="delete-box-title"
                style={{
                  fontSize: '17px',
                  fontWeight: '800',
                  color: '#0f172a',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                Delete Lesson Plan
              </h3>
              <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0', fontWeight: '500' }}>
                This action cannot be undone. Please confirm the plan details below before permanently removing.
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={isDeleting}
            onClick={onCancel}
            aria-label="Close delete box"
            style={{
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#64748b',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '700',
              transition: 'all 0.15s',
              flexShrink: 0,
            }}
            title="Cancel and close delete box"
            onMouseEnter={(e) => {
              if (!isDeleting) {
                e.currentTarget.style.backgroundColor = '#f1f5f9';
                e.currentTarget.style.color = '#0f172a';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#f8fafc';
              e.currentTarget.style.color = '#64748b';
            }}
          >
            ✕
          </button>
        </div>

        {/* =========================================================================
            CREATIVE "TARGET LESSON PLAN BOX" PREVIEW SECTION
            Matches the authentic design language of LessonPlanViewer & GeneratedPlansLibrary
           ========================================================================= */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '14px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 2px 8px -1px rgba(15, 23, 42, 0.04)',
            padding: '16px 18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          {/* Box Header Badge: Matches View Saved Lesson Plan Box Header */}
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
              }}
            >
              <span>🏛️</span>
              <span>Education Science Division • Target Record</span>
            </div>

            <span
              style={{
                fontSize: '11px',
                fontWeight: '700',
                color: '#dc2626',
                backgroundColor: '#fef2f2',
                padding: '2px 8px',
                borderRadius: '6px',
                border: '1px solid #fecaca',
              }}
            >
              Selected for Permanent Deletion
            </span>
          </div>

          {/* Target File Name Display Bar */}
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
              <span style={{ fontSize: '15px' }}>📄</span>
              <span
                style={{
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                  fontSize: '12px',
                  fontWeight: '700',
                  color: '#334155',
                  wordBreak: 'break-all',
                }}
              >
                {filename || 'Lesson_Plan.json'}
              </span>
            </div>
            <span
              style={{
                fontSize: '10px',
                fontWeight: '800',
                textTransform: 'uppercase',
                color: '#64748b',
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                padding: '2px 6px',
                borderRadius: '4px',
                flexShrink: 0,
              }}
            >
              JSON Plan
            </span>
          </div>

          {/* Metadata Grid Boxes (Identical to LessonPlanViewer metadata boxes) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
              gap: '10px',
            }}
          >
            {/* Grade Box */}
            <div
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                padding: '8px 10px',
              }}
            >
              <label
                style={{
                  display: 'block',
                  fontSize: '10px',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  color: '#64748b',
                  marginBottom: '2px',
                  letterSpacing: '0.05em',
                }}
              >
                Grade
              </label>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: '700',
                  color: '#0f172a',
                  display: 'block',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displayGrade}
              </span>
            </div>

            {/* Subject Box */}
            <div
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                padding: '8px 10px',
              }}
            >
              <label
                style={{
                  display: 'block',
                  fontSize: '10px',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  color: '#64748b',
                  marginBottom: '2px',
                  letterSpacing: '0.05em',
                }}
              >
                Subject
              </label>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: '700',
                  color: '#0f172a',
                  display: 'block',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displaySubject}
              </span>
            </div>

            {/* Competency Level Box */}
            <div
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                padding: '8px 10px',
              }}
            >
              <label
                style={{
                  display: 'block',
                  fontSize: '10px',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  color: '#64748b',
                  marginBottom: '2px',
                  letterSpacing: '0.05em',
                }}
              >
                Level
              </label>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: '800',
                  color: '#4338ca',
                  display: 'block',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displayCompetency}
              </span>
            </div>
          </div>

          {/* Competency / Lesson Topic Focus Card */}
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderLeft: '4px solid #4f46e5',
              borderRadius: '10px',
              padding: '10px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <label
                style={{
                  display: 'block',
                  fontSize: '10px',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  color: '#64748b',
                  letterSpacing: '0.05em',
                  margin: 0,
                }}
              >
                Competency / Lesson Focus
              </label>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: '600',
                  color: '#64748b',
                }}
              >
                ⏱️ {displayTime}
              </span>
            </div>
            <div
              style={{
                fontSize: '13px',
                fontWeight: '700',
                color: '#1e293b',
                lineHeight: 1.4,
              }}
            >
              &ldquo;{displayTitle}&rdquo;
            </div>
          </div>
        </div>

        {/* Warning Caution Notice */}
        <div
          style={{
            backgroundColor: '#fff1f2',
            border: '1px solid #fecdd3',
            borderRadius: '12px',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}
        >
          <span style={{ fontSize: '16px', lineHeight: 1.2, flexShrink: 0 }}>⚠️</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span
              style={{
                fontSize: '12px',
                fontWeight: '700',
                color: '#991b1b',
                lineHeight: 1.3,
              }}
            >
              Are you sure you want to permanently delete this plan?
            </span>
            <span
              style={{
                fontSize: '11px',
                color: '#b91c1c',
                lineHeight: 1.4,
              }}
            >
              This plan file will be permanently removed from disk storage and erased from vector database indices.
            </span>
          </div>
        </div>

        {/* Actions Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '10px',
            paddingTop: '2px',
          }}
        >
          <button
            type="button"
            disabled={isDeleting}
            onClick={onCancel}
            style={{
              padding: '9px 18px',
              fontSize: '13px',
              fontWeight: '700',
              color: '#475569',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease-in-out',
              boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
            }}
            onMouseEnter={(e) => {
              if (!isDeleting) {
                e.currentTarget.style.backgroundColor = '#f1f5f9';
                e.currentTarget.style.color = '#0f172a';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#ffffff';
              e.currentTarget.style.color = '#475569';
            }}
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={isDeleting}
            onClick={onConfirm}
            style={{
              padding: '9px 20px',
              fontSize: '13px',
              fontWeight: '700',
              color: '#ffffff',
              backgroundColor: '#dc2626',
              border: '1px solid #b91c1c',
              borderRadius: '10px',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              opacity: isDeleting ? 0.7 : 1,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.15s ease-in-out',
              boxShadow: '0 4px 12px rgba(220, 38, 38, 0.3)',
            }}
            onMouseEnter={(e) => {
              if (!isDeleting) {
                e.currentTarget.style.backgroundColor = '#b91c1c';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#dc2626';
            }}
          >
            {isDeleting ? (
              <>
                <span
                  style={{
                    width: '14px',
                    height: '14px',
                    border: '2px solid #ffffff',
                    borderTopColor: 'transparent',
                    borderRadius: '50%',
                    display: 'inline-block',
                    animation: 'spin 0.8s linear infinite',
                  }}
                />
                <span>Deleting Plan...</span>
              </>
            ) : (
              <>
                <span>🗑️</span>
                <span>Confirm Delete</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Inline Keyframe for Spinner Animation */}
      <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </section>
  );
}
