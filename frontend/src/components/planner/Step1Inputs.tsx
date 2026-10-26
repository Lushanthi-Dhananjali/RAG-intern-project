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
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >

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
        <label htmlFor="planner-periods" style={fieldLabelStyle}>Total Lesson Allocation (Periods &amp; Duration)</label>
        <select
          id="planner-periods"
          value={store.totalPeriods}
          onChange={(e) => {
            const newTotal = Number(e.target.value);
            store.setInputs({
              totalPeriods: newTotal,
              currentPeriod: Math.min(store.currentPeriod, newTotal),
            });
          }}
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

      {store.totalPeriods > 1 && (
        <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '12px 14px' }}>
          <label style={{ ...fieldLabelStyle, color: '#166534', marginBottom: '8px' }}>
            🎯 Select Period to Plan / Generate (Skip previous periods if desired):
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {Array.from({ length: store.totalPeriods }, (_, i) => i + 1).map((pNum) => {
              const isSelected = store.currentPeriod === pNum;
              const hasPlan = !!store.generatedPlans[pNum];
              return (
                <button
                  key={pNum}
                  type="button"
                  onClick={() => store.setInputs({ currentPeriod: pNum })}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    fontWeight: 800,
                    cursor: 'pointer',
                    border: isSelected ? '2px solid #16a34a' : '1px solid #cbd5e1',
                    backgroundColor: isSelected ? '#15803d' : hasPlan ? '#dcfce7' : '#ffffff',
                    color: isSelected ? '#ffffff' : hasPlan ? '#166534' : '#334155',
                    boxShadow: isSelected ? '0 2px 4px rgba(22, 163, 74, 0.3)' : 'none',
                    transition: 'all 0.15s ease',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <span>Period {pNum}</span>
                  {hasPlan && <span style={{ fontSize: '10px' }}>✓</span>}
                </button>
              );
            })}
          </div>
          <p style={{ margin: '8px 0 0', fontSize: '11px', color: '#15803d', lineHeight: 1.4 }}>
            💡 <strong>Flexible period planning:</strong> You can generate any period (e.g. Period 2 or Period 4) without generating previous periods. Learning outcomes are divided equally and deterministically across all {store.totalPeriods} periods following NIE curriculum priority.
          </p>
        </div>
      )}

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
        {loading
          ? `Retrieving curriculum and activities for Period ${store.currentPeriod}...`
          : <>✨ Plan Period {store.currentPeriod} of {store.totalPeriods} ({store.competencyLevel || '...'})</>}
      </button>
    </form>
  );
}