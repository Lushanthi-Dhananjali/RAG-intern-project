'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import { generateSinglePeriodPlan } from '@/services/lessonPlanApi';

export default function Step2OptionsSelection() {
  const store = useLessonPlanStore();
  const [loading, setLoading] = useState(false);
  const [customMode, setCustomMode] = useState(false);
  const [customText, setCustomText] = useState('');
  const [generationError, setGenerationError] = useState<string | null>(null);

  const handleGenerate = async (selectedDesc?: string, isCustom = false, activityTitle?: string) => {
    setLoading(true);
    const chosenTitle = isCustom
      ? `Teacher approach: ${customText.trim()}`
      : (activityTitle || 'Selected Strategy');
    setGenerationError(null);
    try {
      const plan = await generateSinglePeriodPlan({
        competencyLevel: store.competencyLevel,
        topicQuery: store.topicQuery,
        periods: store.totalPeriods,
        requestedPeriod: store.currentPeriod,
        studentCount: store.studentCount,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        teacherMode: isCustom ? 'own_approach' : 'suggested',
        selectedActivityOption: selectedDesc,
        selectedActivityTitle: isCustom
          ? `Teacher approach: ${customText.trim()}`
          : activityTitle,
        customTeacherActivity: isCustom ? customText : undefined,
        activityOptions: store.currentOptions,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(store.currentPeriod),
      });

      store.setGeneratedPlan(store.currentPeriod, plan, chosenTitle);
    } catch (err: any) {
      setGenerationError(err.message || 'Generation failed. Your activity selection has been kept.');
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner / Selection Header Box matching Lesson Details Card Style */}
      <div
        style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '12px',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              textTransform: 'uppercase',
              color: '#1e40af',
              letterSpacing: '0.06em',
            }}
          >
            Period {store.currentPeriod} Activity Selection
          </span>
          <h2 style={{ margin: '4px 0 0', fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
            Choose an activity for Period {store.currentPeriod} of {store.totalPeriods}
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#475569' }}>
            Select an active learning approach for this 40-minute lesson.
          </p>
          {store.priorActivityTitles(store.currentPeriod).length > 0 && (
            <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#1e3a8a' }}>
              <strong>Activities used in earlier periods:</strong> {store.priorActivityTitles(store.currentPeriod).join(', ')}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => setCustomMode(!customMode)}
          style={{
            padding: '8px 14px',
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            fontSize: '13px',
            fontWeight: 700,
            color: '#334155',
            cursor: 'pointer',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            transition: 'all 0.15s ease',
          }}
        >
          {customMode ? '← View activity options' : '✏️ Use my own activity'}
        </button>
      </div>

      {generationError && (
        <div
          role="alert"
          style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '13px',
            color: '#991b1b',
            fontWeight: 600,
          }}
        >
          {generationError}
        </div>
      )}

      {loading && (
        <div
          role="status"
          style={{
            backgroundColor: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '13px',
            color: '#1e40af',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span>Generating the Period {store.currentPeriod} plan from your selected activity...</span>
        </div>
      )}

      {!customMode ? (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={fieldLabelStyle}>Curriculum-Aligned Activity Options</span>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b' }}>
              {store.currentOptions.length} choices available
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '16px',
            }}
          >
            {store.currentOptions.map((opt, index) => {
              const isSelected = store.selectedOption?.id === opt.id;
              return (
                <article
                  key={opt.id}
                  onClick={() => store.selectOption(opt)}
                  style={{
                    backgroundColor: '#ffffff',
                    border: isSelected ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                    borderRadius: '14px',
                    padding: '18px',
                    boxShadow: isSelected
                      ? '0 4px 12px rgba(79, 70, 229, 0.15)'
                      : '0 2px 4px rgba(0, 0, 0, 0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '28px',
                        height: '28px',
                        borderRadius: '8px',
                        backgroundColor: '#eef2ff',
                        color: '#4338ca',
                        fontSize: '12px',
                        fontWeight: 800,
                      }}
                    >
                      {index + 1}
                    </span>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        backgroundColor: '#f1f5f9',
                        color: '#475569',
                        fontSize: '10px',
                        fontWeight: 800,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}
                    >
                      {opt.pedagogy_type}
                    </span>
                  </div>

                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800, color: '#0f172a', lineHeight: 1.35 }}>
                    {opt.title}
                  </h3>

                  <p style={{ margin: 0, fontSize: '12px', color: '#475569', lineHeight: 1.55 }}>
                    {opt.description}
                  </p>

                  {opt.learning_outcomes_addressed && opt.learning_outcomes_addressed.length > 0 && (
                    <div
                      style={{
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '10px',
                        padding: '10px 12px',
                        fontSize: '11px',
                        color: '#334155',
                      }}
                    >
                      <strong style={{ color: '#1e40af' }}>Period {store.currentPeriod} Outcomes Covered:</strong>
                      <ul style={{ margin: '6px 0 0', paddingLeft: '16px', lineHeight: 1.45 }}>
                        {opt.learning_outcomes_addressed.map((outcome, oIdx) => (
                          <li key={oIdx}>{outcome}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div
                    style={{
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '8px 10px',
                      fontSize: '11px',
                      color: '#475569',
                    }}
                  >
                    <strong style={{ color: '#334155' }}>Student Grouping: </strong>
                    <span>{opt.student_grouping}</span>
                  </div>

                  <button
                    type="button"
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
                    style={{
                      marginTop: 'auto',
                      width: '100%',
                      padding: '11px 16px',
                      borderRadius: '10px',
                      backgroundColor: loading && isSelected ? '#94a3b8' : '#4f46e5',
                      color: '#ffffff',
                      fontWeight: 700,
                      fontSize: '13px',
                      border: 'none',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      boxShadow: '0 2px 4px rgba(79, 70, 229, 0.25)',
                      transition: 'background-color 0.2s ease',
                    }}
                  >
                    {loading && isSelected ? 'Generating plan...' : '✨ Choose & Generate Plan'}
                  </button>
                </article>
              );
            })}
          </div>
        </div>
      ) : (
        /* Custom Activity Box styled with matching design box */
        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '14px',
            padding: '22px',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.04)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div>
            <span style={fieldLabelStyle}>Teacher-Designed Custom Activity</span>
            <h3 style={{ margin: '2px 0 0', fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>
              Your Own Classroom Activity or Simulation
            </h3>
            <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Enter your custom activity idea or video simulation below. The lesson plan introduction,
              step-by-step development, and closure assessment will be built around your chosen activity.
            </p>
          </div>

          <textarea
            rows={4}
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="e.g. Play a 3-minute clip of a municipal council debate, then ask student groups to draft two formal citizen complaints regarding road drainage..."
            style={{
              width: '100%',
              padding: '12px 14px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              fontSize: '14px',
              fontWeight: 500,
              color: '#1e293b',
              outline: 'none',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
          />

          <button
            type="button"
            disabled={loading || !customText.trim()}
            onClick={() => handleGenerate(customText, true)}
            style={{
              width: '100%',
              padding: '12px 18px',
              borderRadius: '10px',
              backgroundColor: loading || !customText.trim() ? '#94a3b8' : '#4f46e5',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '14px',
              border: 'none',
              cursor: loading || !customText.trim() ? 'not-allowed' : 'pointer',
              boxShadow: '0 2px 4px rgba(79, 70, 229, 0.25)',
              transition: 'background-color 0.2s ease',
            }}
          >
            {loading ? 'Generating plan...' : '✨ Generate Plan From My Activity'}
          </button>
        </div>
      )}
    </div>
  );
}