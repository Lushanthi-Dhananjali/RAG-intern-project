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
  const durationMinutes = store.totalPeriods * 40;

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
        topicQuery: store.topicQuery,
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

  const fieldLabelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '12px',
    fontWeight: 700,
    textTransform: 'uppercase',
    color: '#334155',
    marginBottom: '6px',
    letterSpacing: '0.05em',
  };
  const fieldStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    backgroundColor: '#f8fafc',
    border: '1px solid #cbd5e1',
    borderRadius: '10px',
    fontSize: '14px',
    fontWeight: 600,
    color: '#1e293b',
    outline: 'none',
    boxSizing: 'border-box',
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
      <header style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '12px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0, color: '#0f172a', fontSize: '16px', fontWeight: 800 }}>
          <span aria-hidden="true">✨</span>
          <span>Lesson Plan Generator</span>
        </h2>
        <p style={{ margin: '2px 0 0', color: '#64748b', fontSize: '12px' }}>
          Configure curriculum parameters to generate an NIE &amp; LEARN aligned lesson plan
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div>
          <label htmlFor="planner-subject" style={fieldLabelStyle}>Subject</label>
          <select id="planner-subject" value={store.subject} disabled style={fieldStyle}>
            <option value={store.subject}>🏛️ {store.subject}</option>
          </select>
        </div>

        <div>
          <label htmlFor="planner-grade" style={fieldLabelStyle}>Grade Level</label>
          <select
            id="planner-grade"
            value={selectedGrade}
            onChange={(e) => store.setInputs({ gradeLevel: e.target.value })}
            style={fieldStyle}
          >
            <option value="Grade 6">Grade 6</option>
            <option value="Grade 7">Grade 7</option>
            <option value="Grade 8">Grade 8</option>
            <option value="Grade 9">Grade 9</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="planner-competency" style={fieldLabelStyle}>NIE Competency Level</label>
        <input
          id="planner-competency"
          type="text"
          value={store.competencyLevel}
          onChange={(e) => store.setInputs({ competencyLevel: e.target.value })}
          placeholder="e.g. 8.1.1"
          required
          style={{
            ...fieldStyle,
            border: '1.5px solid #818cf8',
            fontSize: '15px',
            fontWeight: 600,
            fontFamily: 'monospace',
            color: '#4338ca',
          }}
        />
        <p style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '8px', margin: '4px 0 0', color: '#64748b', fontSize: '11px' }}>
          <span>Enter Civic Education Competency Code (e.g. 8.1.1, 8.4.2)</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            Class size
            <input
              aria-label="Student count"
              type="number"
              min={5}
              max={80}
              value={store.studentCount}
              onChange={(e) => store.setInputs({ studentCount: Number(e.target.value) })}
              style={{ width: '64px', padding: '3px 6px', border: '1px solid #cbd5e1', borderRadius: '6px', backgroundColor: '#f8fafc', color: '#334155', fontSize: '11px' }}
            />
            students
          </span>
        </p>
      </div>

      <div>
        <label htmlFor="planner-topic" style={fieldLabelStyle}>Lesson Topic or Focus (Optional)</label>
        <input
          id="planner-topic"
          type="text"
          value={store.topicQuery}
          onChange={(e) => store.setInputs({ topicQuery: e.target.value })}
          placeholder="e.g. Public services in the local community"
          style={fieldStyle}
        />
      </div>

      <div>
        <label htmlFor="planner-periods" style={fieldLabelStyle}>Lesson Allocation (Periods &amp; Duration)</label>
        <select
          id="planner-periods"
          value={store.totalPeriods}
          onChange={(e) => store.setInputs({ totalPeriods: Number(e.target.value) })}
          style={fieldStyle}
        >
          {[1, 2, 3, 4].map((periodCount) => (
            <option key={periodCount} value={periodCount}>
              {periodCount} {periodCount === 1 ? 'Period' : 'Periods'} — {periodCount * 40} Minutes (Max. 4 periods)
            </option>
          ))}
        </select>
        <span style={{ display: 'block', marginTop: '4px', color: '#64748b', fontSize: '11px' }}>
          NIE Standard: 40 minutes per period ({durationMinutes} minutes total)
        </span>
      </div>

      <button
        type="submit"
        disabled={loading}
        style={{
          width: '100%',
          marginTop: '6px',
          padding: '12px 16px',
          borderRadius: '10px',
          backgroundColor: loading ? '#94a3b8' : '#4f46e5',
          color: '#ffffff',
          fontWeight: 700,
          fontSize: '14px',
          border: 'none',
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
        }}
      >
        {loading ? 'Retrieving curriculum and activities...' : <>✨ Generate Civic Education Lesson Plan ({store.competencyLevel || '...'})</>}
      </button>
    </form>
  );
}