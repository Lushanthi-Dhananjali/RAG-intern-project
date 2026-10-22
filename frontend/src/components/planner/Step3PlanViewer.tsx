'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { fetchPedagogicalOptions } from '@/services/lessonPlanApi';

export default function Step3PlanViewer() {
  const store = useLessonPlanStore();
  const [loadingNext, setLoadingNext] = useState(false);
  const currentPlan = store.generatedPlans[store.currentPeriod];

  if (!currentPlan) {
    return (
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '14px',
          padding: '24px',
          textAlign: 'center',
          color: '#64748b',
          fontSize: '14px',
        }}
      >
        No generated plan found for Period {store.currentPeriod}.
      </div>
    );
  }

  const handleNextPeriodClick = async () => {
    setLoadingNext(true);
    const nextP = store.currentPeriod + 1;
    try {
      const options = await fetchPedagogicalOptions({
        competencyLevel: store.competencyLevel,
        studentCount: store.studentCount,
        periods: store.totalPeriods,
        requestedPeriod: nextP,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        topicQuery: store.topicQuery,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(nextP),
      });

      store.setOptions(options);
      store.nextPeriod();
    } catch (err: any) {
      alert(`Could not fetch options for Period ${nextP}: ${err.message}`);
    } finally {
      setLoadingNext(false);
    }
  };

  const handleChangeActivity = async () => {
    setLoadingNext(true);
    try {
      const options = await fetchPedagogicalOptions({
        competencyLevel: store.competencyLevel,
        studentCount: store.studentCount,
        periods: store.totalPeriods,
        requestedPeriod: store.currentPeriod,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        topicQuery: store.topicQuery,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.otherActivityTitles(store.currentPeriod),
      });
      store.setOptions(options);
    } catch (err: any) {
      alert(`Could not fetch new options for Period ${store.currentPeriod}: ${err.message}`);
    } finally {
      setLoadingNext(false);
    }
  };

  const sectionLabelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '11px',
    fontWeight: 800,
    textTransform: 'uppercase',
    color: '#4338ca',
    letterSpacing: '0.06em',
    marginBottom: '6px',
  };

  const boxCardStyle: React.CSSProperties = {
    backgroundColor: '#ffffff',
    border: '1px solid #cbd5e1',
    borderRadius: '14px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.04)',
  };

  // Find the selected activity option details from currentPlan.activity_options or store.selectedOption
  const selectedOpt =
    (currentPlan.activity_options && currentPlan.activity_options.length > 0 ? currentPlan.activity_options[0] : null) ||
    store.selectedOption;

  const displaySelectedTitle =
    currentPlan.selected_activity_title ||
    store.activityByPeriod[store.currentPeriod] ||
    selectedOpt?.title ||
    'Selected Pedagogical Strategy';

  const displaySelectedDesc =
    (selectedOpt && selectedOpt.description) ||
    currentPlan.selected_activity ||
    currentPlan.custom_teacher_activity ||
    'Interactive curriculum-aligned classroom activity.';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Sequence Tabs for Multi-Period Navigation */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          backgroundColor: '#f8fafc',
          border: '1px solid #cbd5e1',
          borderRadius: '12px',
          padding: '8px',
        }}
      >
        {Array.from({ length: store.totalPeriods }).map((_, idx) => {
          const pNum = idx + 1;
          const isDone = !!store.generatedPlans[pNum];
          const isCurrent = store.currentPeriod === pNum;
          return (
            <button
              key={pNum}
              type="button"
              onClick={() => store.previousPeriod(pNum)}
              disabled={!isDone}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 700,
                border: isCurrent ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                backgroundColor: isCurrent ? '#4f46e5' : isDone ? '#ffffff' : '#f1f5f9',
                color: isCurrent ? '#ffffff' : isDone ? '#334155' : '#94a3b8',
                cursor: isDone ? 'pointer' : 'not-allowed',
                boxShadow: isCurrent ? '0 2px 4px rgba(79, 70, 229, 0.25)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              Period {pNum} {isDone ? '✓' : ''}
            </button>
          );
        })}
      </div>

      {/* 2. Generated Plan Status Banner */}
      <div
        style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '12px',
          padding: '14px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div>
          <span style={sectionLabelStyle}>Generated Lesson Plan</span>
          <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#475569' }}>
            This period plan is automatically persisted to the Generated Plans Library.
          </p>
        </div>
        <span
          style={{
            padding: '4px 12px',
            backgroundColor: '#ffffff',
            border: '1px solid #bfdbfe',
            borderRadius: '9999px',
            fontSize: '12px',
            fontWeight: 800,
            color: '#1e40af',
          }}
        >
          Period {store.currentPeriod} of {store.totalPeriods}
        </span>
      </div>

      {/* 3. PROMINENT LESSON TOPIC BOX (Required for Multi Period Planner Generated Plan Page) */}
      <div style={boxCardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <span style={sectionLabelStyle}>Lesson Topic</span>
            <h1 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 800, color: '#0f172a', lineHeight: 1.35 }}>
              {currentPlan.lesson || 'Civic Education Curriculum Topic'}
            </h1>
          </div>
          <span
            style={{
              padding: '4px 10px',
              backgroundColor: '#eef2ff',
              border: '1px solid #c7d2fe',
              borderRadius: '8px',
              color: '#3730a3',
              fontSize: '11px',
              fontWeight: 800,
              textTransform: 'uppercase',
            }}
          >
            NIE &amp; LEARN Aligned
          </span>
        </div>

        {/* Core Lesson Meta Badges in Design Boxes */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '12px',
            marginTop: '16px',
          }}
        >
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '10px 12px' }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Subject</span>
            <strong style={{ display: 'block', marginTop: '2px', fontSize: '13px', color: '#0f172a' }}>{currentPlan.subject}</strong>
          </div>
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '10px 12px' }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Grade</span>
            <strong style={{ display: 'block', marginTop: '2px', fontSize: '13px', color: '#0f172a' }}>{currentPlan.grade}</strong>
          </div>
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '10px 12px' }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Competency Level</span>
            <strong style={{ display: 'block', marginTop: '2px', fontSize: '13px', color: '#4338ca', fontFamily: 'monospace' }}>{currentPlan.competence_level}</strong>
          </div>
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '10px 12px' }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Time Allocation</span>
            <strong style={{ display: 'block', marginTop: '2px', fontSize: '13px', color: '#0f172a' }}>{currentPlan.time_allocation}</strong>
          </div>
        </div>
      </div>

      {/* 4. SELECTED ACTIVITY BOX (Displays ONLY the selected activity — NO unselected option cards) */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1.5px solid #818cf8',
          borderRadius: '14px',
          padding: '20px',
          boxShadow: '0 2px 6px rgba(99, 102, 241, 0.08)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              textTransform: 'uppercase',
              color: '#4338ca',
              letterSpacing: '0.06em',
            }}
          >
            Selected Activity (Period {store.currentPeriod})
          </span>
          <span
            style={{
              padding: '3px 8px',
              backgroundColor: '#4f46e5',
              borderRadius: '6px',
              color: '#ffffff',
              fontSize: '10px',
              fontWeight: 800,
              textTransform: 'uppercase',
            }}
          >
            Active Choice
          </span>
        </div>

        <h3 style={{ margin: '4px 0 0', fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>
          {displaySelectedTitle}
        </h3>

        <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#475569', lineHeight: 1.55 }}>
          {displaySelectedDesc}
        </p>

        {selectedOpt?.student_action_summary && (
          <div
            style={{
              marginTop: '12px',
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '10px 12px',
              fontSize: '12px',
              color: '#334155',
            }}
          >
            <strong style={{ color: '#1e40af' }}>Student Participation: </strong>
            <span>{selectedOpt.student_action_summary}</span>
          </div>
        )}

        <div
          style={{
            marginTop: '10px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          {selectedOpt?.student_grouping && (
            <span
              style={{
                fontSize: '11px',
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                padding: '4px 10px',
                borderRadius: '6px',
                color: '#334155',
                fontWeight: 600,
              }}
            >
              <strong>Grouping:</strong> {selectedOpt.student_grouping}
            </span>
          )}
          {selectedOpt?.pedagogy_type && (
            <span
              style={{
                fontSize: '11px',
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                padding: '4px 10px',
                borderRadius: '6px',
                color: '#334155',
                fontWeight: 600,
              }}
            >
              <strong>Pedagogy:</strong> {selectedOpt.pedagogy_type}
            </span>
          )}
        </div>

        {currentPlan.custom_teacher_activity && (
          <div
            style={{
              marginTop: '12px',
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: '8px',
              padding: '10px 12px',
              fontSize: '12px',
              color: '#1e3a8a',
            }}
          >
            <strong>Teacher Custom Approach Details: </strong>
            <p style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>{currentPlan.custom_teacher_activity}</p>
          </div>
        )}
      </div>

      {/* 5. Allocated Learning Outcomes for THIS Period Box */}
      <div style={boxCardStyle}>
        <span style={sectionLabelStyle}>Teacher Guide Allocated Learning Outcomes</span>
        <ul style={{ margin: '8px 0 0', paddingLeft: '18px', fontSize: '13px', color: '#1e293b', lineHeight: 1.6 }}>
          {currentPlan.unique_learning_outcome.map((o, idx) => (
            <li key={idx} style={{ marginBottom: '4px' }}>{o}</li>
          ))}
        </ul>
      </div>

      {/* 6. The Entrance (Introduction) Box */}
      <div style={boxCardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#0f172a' }}>
            The Entrance — Introduction
          </h4>
          <span
            style={{
              padding: '3px 10px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: 700,
              color: '#334155',
            }}
          >
            {currentPlan.entrance_duration_minutes ?? 5} Minutes
          </span>
        </div>
        <p style={{ margin: '10px 0 0', whiteSpace: 'pre-line', fontSize: '13px', color: '#334155', lineHeight: 1.6 }}>
          {currentPlan.the_entrance}
        </p>
      </div>

      {/* 7. Lesson Development Steps Box */}
      <div style={boxCardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#0f172a' }}>
            Lesson Development Steps
          </h4>
          <span
            style={{
              padding: '3px 10px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: 700,
              color: '#334155',
            }}
          >
            30 Minutes Total
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {currentPlan.lesson_development_steps.map((st) => (
            <div
              key={st.step_number}
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '16px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    backgroundColor: '#eef2ff',
                    color: '#4338ca',
                    fontSize: '12px',
                    fontWeight: 800,
                  }}
                >
                  {st.step_number}
                </span>
                <strong style={{ fontSize: '13px', color: '#0f172a' }}>Development Step {st.step_number}</strong>
                <span style={{ marginLeft: 'auto', fontSize: '12px', fontWeight: 700, color: '#4338ca' }}>
                  {st.time_minutes} Mins
                </span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '10px',
                }}
              >
                <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px' }}>
                  <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', color: '#64748b' }}>
                    Teacher Activities
                  </span>
                  <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#1e293b', lineHeight: 1.5 }}>
                    {st.teacher_activities}
                  </p>
                </div>

                <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px' }}>
                  <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', color: '#4338ca' }}>
                    Student Activities
                  </span>
                  <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#1e293b', lineHeight: 1.5 }}>
                    {st.student_activities}
                  </p>
                </div>

                <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px' }}>
                  <span style={{ display: 'block', fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', color: '#64748b' }}>
                    Method &amp; Aids
                  </span>
                  <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#1e293b', lineHeight: 1.5 }}>
                    <strong>Method:</strong> {st.learning_teaching_method}<br />
                    <strong>Aids:</strong> {st.learning_teaching_aids}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 8. Change Activity Option Button */}
      <button
        type="button"
        onClick={handleChangeActivity}
        disabled={loadingNext}
        style={{
          width: '100%',
          padding: '11px 16px',
          borderRadius: '10px',
          backgroundColor: '#ffffff',
          border: '1.5px solid #cbd5e1',
          color: '#334155',
          fontWeight: 700,
          fontSize: '13px',
          cursor: loadingNext ? 'not-allowed' : 'pointer',
          boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
          transition: 'all 0.15s ease',
        }}
      >
        {loadingNext ? 'Loading period-specific options...' : `🔄 Choose a different activity for Period ${store.currentPeriod}`}
      </button>

      {/* 9. Five-Minute Assignment & Closure Box */}
      <div style={boxCardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#0f172a' }}>
            Five-Minute Assignment &amp; Closure
          </h4>
          <span
            style={{
              padding: '3px 10px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: 700,
              color: '#334155',
            }}
          >
            {currentPlan.assignment_duration_minutes ?? 5} Minutes
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '12px',
            marginTop: '12px',
          }}
        >
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px' }}>
            <span style={{ display: 'block', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: '#4338ca' }}>
              Closure Summary
            </span>
            <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#334155', lineHeight: 1.5, whiteSpace: 'pre-line' }}>
              {currentPlan.summary}
            </p>
          </div>

          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px' }}>
            <span style={{ display: 'block', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: '#4338ca' }}>
              Concluding Task / Assignment
            </span>
            <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#334155', lineHeight: 1.5, whiteSpace: 'pre-line' }}>
              {currentPlan.post_activity}
            </p>
          </div>
        </div>

        <div style={{ marginTop: '12px', padding: '10px 12px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px', color: '#475569' }}>
          <strong style={{ color: '#334155' }}>Assessment &amp; Feedback Guidance: </strong>
          <span>{currentPlan.assessment_and_feedback_whole_lesson}</span>
        </div>
      </div>

      {/* 10. Sequential Progression Action Button */}
      {store.currentPeriod < store.totalPeriods ? (
        <button
          type="button"
          onClick={handleNextPeriodClick}
          disabled={loadingNext}
          style={{
            width: '100%',
            padding: '14px 20px',
            borderRadius: '10px',
            backgroundColor: loadingNext ? '#94a3b8' : '#4f46e5',
            color: '#ffffff',
            fontWeight: 800,
            fontSize: '14px',
            border: 'none',
            cursor: loadingNext ? 'not-allowed' : 'pointer',
            boxShadow: '0 2px 6px rgba(79, 70, 229, 0.3)',
            transition: 'background-color 0.2s ease',
          }}
        >
          {loadingNext
            ? `Querying Fresh Options for Period ${store.currentPeriod + 1}...`
            : `Plan Next Period (Period ${store.currentPeriod + 1} of ${store.totalPeriods}) →`}
        </button>
      ) : (
        <div
          style={{
            backgroundColor: '#f0fdf4',
            border: '1.5px solid #bbf7d0',
            borderRadius: '12px',
            padding: '16px',
            textAlign: 'center',
            fontWeight: 800,
            fontSize: '14px',
            color: '#166534',
          }}
        >
          🎉 All {store.totalPeriods} Periods for Competency {store.competencyLevel} Successfully Generated &amp; Saved!
        </div>
      )}
    </div>
  );
}