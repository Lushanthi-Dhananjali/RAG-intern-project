'use client';
import React, { useState } from 'react';
import { useLessonPlanStore } from '@/store/useLessonPlanStore';
import {
  generateSinglePeriodPlan,
  fetchPedagogicalOptions,
  checkActivitySuitability,
  CheckActivitySuitabilityResponse,
} from '@/services/lessonPlanApi';

export default function Step2OptionsSelection() {
  const store = useLessonPlanStore();
  const [loading, setLoading] = useState(false);
  const [customMode, setCustomMode] = useState(false);
  const [customText, setCustomText] = useState('');
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [checkingSuitability, setCheckingSuitability] = useState(false);
  const [suitabilityResult, setSuitabilityResult] = useState<CheckActivitySuitabilityResponse | null>(null);

  const handleSwitchPeriod = async (targetPeriod: number) => {
    if (targetPeriod === store.currentPeriod) return;
    if (store.generatedPlans[targetPeriod]) {
      store.viewPeriodPlan(targetPeriod);
      return;
    }
    setLoading(true);
    setGenerationError(null);
    try {
      const options = await fetchPedagogicalOptions({
        competencyLevel: store.competencyLevel,
        studentCount: store.studentCount,
        periods: store.totalPeriods,
        requestedPeriod: targetPeriod,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        topicQuery: store.topicQuery,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.otherActivityTitles(targetPeriod),
      });
      store.startPlanningPeriod(targetPeriod, options);
    } catch (err: any) {
      setGenerationError(`Failed to fetch options for Period ${targetPeriod}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (selectedDesc?: string, isCustom = false, activityTitle?: string) => {
    setLoading(true);
    setGenerationError(null);

    // 1. If custom activity, check suitability against period learning outcomes first
    if (isCustom) {
      setCheckingSuitability(true);
      try {
        const check = await checkActivitySuitability({
          customActivity: customText.trim(),
          competencyLevel: store.competencyLevel,
          gradeLevel: store.gradeLevel,
          subject: store.subject,
          requestedPeriod: store.currentPeriod,
          totalPeriods: store.totalPeriods,
          studentCount: store.studentCount,
          classroomEnvironment: store.classroomEnvironment,
          accessibleResources: store.accessibleResources,
        });
        setSuitabilityResult(check);
        setCheckingSuitability(false);

        if (!check.is_suitable) {
          setLoading(false);
          return;
        }
      } catch (err: any) {
        setCheckingSuitability(false);
        // If endpoint returned an error message, display it
        if (err.message && err.message.includes('Activity not suitable')) {
          setGenerationError(err.message);
          setLoading(false);
          return;
        }
      }
    }

    const chosenTitle = isCustom
      ? (customText.trim().length > 60 ? `Teacher Activity: ${customText.trim().slice(0, 60)}...` : `Teacher Activity: ${customText.trim()}`)
      : (activityTitle || 'Selected Strategy');

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
        selectedActivityTitle: chosenTitle,
        customTeacherActivity: isCustom ? customText : undefined,
        activityOptions: isCustom ? [] : store.currentOptions,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
        previousPeriodActivities: store.priorActivityTitles(store.currentPeriod),
      });

      store.setGeneratedPlan(store.currentPeriod, plan, chosenTitle);
    } catch (err: any) {
      setGenerationError(err.message || 'Generation failed. Your activity selection has been kept.');
    } finally {
      setLoading(false);
      setCheckingSuitability(false);
    }
  };

  const handleCheckSuitabilityOnly = async () => {
    if (!customText.trim()) return;
    setCheckingSuitability(true);
    setGenerationError(null);
    setSuitabilityResult(null);
    try {
      const check = await checkActivitySuitability({
        customActivity: customText.trim(),
        competencyLevel: store.competencyLevel,
        gradeLevel: store.gradeLevel,
        subject: store.subject,
        requestedPeriod: store.currentPeriod,
        totalPeriods: store.totalPeriods,
        studentCount: store.studentCount,
        classroomEnvironment: store.classroomEnvironment,
        accessibleResources: store.accessibleResources,
      });
      setSuitabilityResult(check);
    } catch (err: any) {
      setGenerationError(err.message || 'Suitability check failed.');
    } finally {
      setCheckingSuitability(false);
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
      {/* Period Selection Bar */}
      {store.totalPeriods > 1 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px',
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '10px 14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', fontWeight: 800, color: '#334155' }}>
              Planning Periods:
            </span>
            {Array.from({ length: store.totalPeriods }, (_, i) => i + 1).map((pNum) => {
              const isCurrent = store.currentPeriod === pNum;
              const hasPlan = !!store.generatedPlans[pNum];
              return (
                <button
                  key={pNum}
                  type="button"
                  disabled={loading}
                  onClick={() => handleSwitchPeriod(pNum)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    border: isCurrent ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                    backgroundColor: isCurrent ? '#4f46e5' : hasPlan ? '#dcfce7' : '#ffffff',
                    color: isCurrent ? '#ffffff' : hasPlan ? '#166534' : '#475569',
                    boxShadow: isCurrent ? '0 2px 4px rgba(79, 70, 229, 0.25)' : 'none',
                    transition: 'all 0.15s ease',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                  }}
                >
                  <span>Period {pNum}</span>
                  {hasPlan && <span style={{ fontSize: '10px' }}>✓</span>}
                  {isCurrent && <span style={{ fontSize: '10px', opacity: 0.9 }}>(Active)</span>}
                </button>
              );
            })}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Click any period to switch &amp; plan independently
          </span>
        </div>
      )}

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
          onClick={() => {
            setCustomMode(!customMode);
            setGenerationError(null);
            setSuitabilityResult(null);
          }}
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

      {(loading || checkingSuitability) && (
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
          <span>
            {checkingSuitability
              ? `Checking activity suitability against Period ${store.currentPeriod} learning outcomes...`
              : `Generating the Period ${store.currentPeriod} plan from your selected activity...`}
          </span>
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
            gap: '16px',
          }}
        >
          <div>
            <span style={fieldLabelStyle}>Teacher-Designed Custom Activity</span>
            <h3 style={{ margin: '2px 0 0', fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>
              Your Own Classroom Activity or Simulation
            </h3>
            <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Enter your custom activity idea below. The RAG system will automatically check if this activity
              is suitable for achieving the <strong>Period {store.currentPeriod}</strong> learning outcomes.
              If suitable, the lesson plan will be generated; if not suitable, the system will explain why and suggest an alternative.
            </p>
          </div>

          <textarea
            rows={4}
            value={customText}
            onChange={(e) => {
              setCustomText(e.target.value);
              setSuitabilityResult(null);
              setGenerationError(null);
            }}
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

          {/* Suitability Feedback Box */}
          {suitabilityResult && !suitabilityResult.is_suitable && (
            <div
              style={{
                backgroundColor: '#fffbeb',
                border: '1.5px solid #fde68a',
                borderRadius: '12px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>⚠️</span>
                <strong style={{ fontSize: '14px', color: '#92400e' }}>
                  Activity Not Suitable for Period {store.currentPeriod}
                </strong>
              </div>
              <p style={{ margin: 0, fontSize: '13px', color: '#78350f', lineHeight: 1.55 }}>
                {suitabilityResult.reason}
              </p>
              {suitabilityResult.suggested_activity && (
                <div
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #fde68a',
                    borderRadius: '10px',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: '#b45309' }}>
                    💡 Recommended Alternative Activity for this Period:
                  </span>
                  {suitabilityResult.suggested_activity_title && (
                    <strong style={{ fontSize: '13px', color: '#0f172a' }}>
                      {suitabilityResult.suggested_activity_title}
                    </strong>
                  )}
                  <p style={{ margin: 0, fontSize: '12px', color: '#475569', lineHeight: 1.5 }}>
                    {suitabilityResult.suggested_activity}
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setCustomText(suitabilityResult.suggested_activity!);
                      setSuitabilityResult(null);
                      setGenerationError(null);
                    }}
                    style={{
                      marginTop: '4px',
                      padding: '7px 12px',
                      backgroundColor: '#fef3c7',
                      border: '1px solid #f59e0b',
                      borderRadius: '8px',
                      color: '#92400e',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      alignSelf: 'flex-start',
                    }}
                  >
                    👉 Use This Suggested Activity
                  </button>
                </div>
              )}
            </div>
          )}

          {suitabilityResult && suitabilityResult.is_suitable && (
            <div
              style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '10px',
                padding: '12px 14px',
                fontSize: '13px',
                color: '#166534',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>✅</span>
              <span>{suitabilityResult.reason || `Activity is suitable for Period ${store.currentPeriod} learning outcomes.`}</span>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '10px' }}>
            <button
              type="button"
              disabled={loading || checkingSuitability || !customText.trim()}
              onClick={handleCheckSuitabilityOnly}
              style={{
                padding: '12px 16px',
                borderRadius: '10px',
                backgroundColor: '#ffffff',
                border: '1.5px solid #cbd5e1',
                color: '#334155',
                fontWeight: 700,
                fontSize: '13px',
                cursor: loading || checkingSuitability || !customText.trim() ? 'not-allowed' : 'pointer',
                boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                whiteSpace: 'nowrap',
              }}
            >
              {checkingSuitability ? 'Checking...' : '🔍 Check Suitability'}
            </button>

            <button
              type="button"
              disabled={loading || checkingSuitability || !customText.trim()}
              onClick={() => handleGenerate(customText, true)}
              style={{
                width: '100%',
                padding: '12px 18px',
                borderRadius: '10px',
                backgroundColor: loading || checkingSuitability || !customText.trim() ? '#94a3b8' : '#4f46e5',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '14px',
                border: 'none',
                cursor: loading || checkingSuitability || !customText.trim() ? 'not-allowed' : 'pointer',
                boxShadow: '0 2px 4px rgba(79, 70, 229, 0.25)',
                transition: 'background-color 0.2s ease',
              }}
            >
              {loading ? 'Validating & Generating...' : '✨ Generate Plan From My Activity'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}