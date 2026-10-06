'use client';

import React, { useState } from 'react';

interface LessonPlanFormProps {
  onSubmit: (formData: {
    competencyLevel: string;
    gradeLevel: string;
    subject: string;
    periods: number;
    durationMinutes: number;
    timeSlot: string;
  }) => void;
  isLoading: boolean;
}

export default function LessonPlanForm({
  onSubmit,
  isLoading,
}: LessonPlanFormProps) {
  const [subject, setSubject] = useState<string>('Civic Education');
  const [gradeLevel, setGradeLevel] = useState<string>('Grade 8');
  const [competencyLevel, setCompetencyLevel] = useState<string>('8.1.1');
  const [periods, setPeriods] = useState<number>(1);

  // Derived calculation: 1 period = 40 minutes (NIE standard)
  const durationMinutes = periods * 40;
  const timeSlotString = `${durationMinutes} Minutes (${periods} ${periods === 1 ? 'Period' : 'Periods'})`;

  // Provide helpful example placeholders based on the chosen subject
  const placeholderText = subject === 'Science' ? 'e.g. 1.6, 1.7, 2.1' : 'e.g. 8.1.1, 8.4.2, 8.6.8';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!competencyLevel.trim()) return;

    onSubmit({
      competencyLevel: competencyLevel.trim(),
      gradeLevel,
      subject,
      periods: Number(periods),
      durationMinutes,
      timeSlot: timeSlotString,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
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
      {/* Panel Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f1f5f9',
          paddingBottom: '12px',
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
            <span>✨</span>
            <span>Lesson Plan Generator</span>
          </h3>
          <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
            Configure curriculum parameters to generate an NIE & LEARN aligned lesson plan
          </p>
        </div>
      </div>

      {/* 1. Subject and Grade Level */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#334155', marginBottom: '6px', letterSpacing: '0.05em' }}>
            Subject
          </label>
          <select
            value={subject}
            onChange={(e) => {
              const newSub = e.target.value;
              setSubject(newSub);
              // Set default competency hint on subject change
              setCompetencyLevel(newSub === 'Science' ? '1.6' : '8.1.1');
            }}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#f8fafc',
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

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#334155', marginBottom: '6px', letterSpacing: '0.05em' }}>
            Grade Level
          </label>
          <select
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: '#f8fafc',
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
      </div>

      {/* 2. Direct Competency Level Input */}
      <div>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#334155', marginBottom: '6px', letterSpacing: '0.05em' }}>
          NIE Competency Level
        </label>
        <input
          type="text"
          required
          list="competency-suggestions"
          value={competencyLevel}
          onChange={(e) => setCompetencyLevel(e.target.value)}
          placeholder={placeholderText}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '10px 14px',
            backgroundColor: '#f8fafc',
            border: '1.5px solid #6366f1',
            borderRadius: '10px',
            fontSize: '15px',
            fontWeight: '600',
            fontFamily: 'monospace',
            color: '#4338ca',
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
        <datalist id="competency-suggestions">
          <option value="8.1.1">8.1.1 — Public Services</option>
          <option value="8.1.2">8.1.2 — Public Services Need</option>
          <option value="8.1.3">8.1.3 — Public Services Features</option>
          <option value="8.1.4">8.1.4 — Public Services Role</option>
          <option value="8.2.1">8.2.1 — Democratic Governance</option>
          <option value="8.2.2">8.2.2 — Rule of Law</option>
          <option value="8.3.1">8.3.1 — Civic Responsibilities</option>
          <option value="8.4.1">8.4.1 — Multicultural Society</option>
          <option value="8.4.2">8.4.2 — Social Harmony</option>
          <option value="8.5.1">8.5.1 — Environmental Protection</option>
          <option value="8.6.1">8.6.1 — Global Community</option>
          <option value="1.6">1.6 — Science Competency</option>
          <option value="1.7">1.7 — Science Competency</option>
        </datalist>
        <span style={{ display: 'block', fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
          {subject === 'Science' ? 'Enter Science Competency Level (e.g. 1.6)' : 'Enter Civic Education Competency Code (e.g. 8.1.1, 8.4.2, 8.6.8)'}
        </span>
      </div>

      {/* 3. Lesson Allocation (Periods & Duration) */}
      <div>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#334155', marginBottom: '6px', letterSpacing: '0.05em' }}>
          Lesson Allocation (Periods & Duration)
        </label>
        <select
          value={periods}
          onChange={(e) => setPeriods(Number(e.target.value))}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '10px 14px',
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            fontSize: '14px',
            fontWeight: '500',
            color: '#1e293b',
            outline: 'none',
            boxSizing: 'border-box',
          }}
        >
          <option value={1}>1 Period — 40 Minutes (Min. 2 Development Steps)</option>
          <option value={2}>2 Periods — 80 Minutes (Min. 3 Development Steps)</option>
          <option value={3}>3 Periods — 120 Minutes (Min. 4 Development Steps)</option>
          <option value={4}>4 Periods — 160 Minutes (Min. 5 Development Steps)</option>
        </select>
        <span style={{ display: 'block', fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
          NIE Standard: 40 minutes per period ({durationMinutes} minutes total)
        </span>
      </div>

      {/* 4. Generate Submit Button (Only Generate Option) */}
      <button
        type="submit"
        disabled={isLoading || !competencyLevel.trim()}
        style={{
          width: '100%',
          marginTop: '6px',
          padding: '12px 16px',
          borderRadius: '10px',
          backgroundColor: isLoading || !competencyLevel.trim() ? '#94a3b8' : '#4f46e5',
          color: '#ffffff',
          fontWeight: '700',
          fontSize: '14px',
          border: 'none',
          cursor: isLoading || !competencyLevel.trim() ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
        }}
      >
        {isLoading ? (
          <>
            <span className="animate-spin inline-block">⏳</span>
            <span>Generating Lesson Plan...</span>
          </>
        ) : (
          <>
            <span>✨</span>
            <span>Generate {subject} Lesson Plan ({competencyLevel || '...'})</span>
          </>
        )}
      </button>
    </form>
  );
}