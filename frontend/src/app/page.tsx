'use client';

import React, { useState } from 'react';
import LessonPlanForm from '../components/LessonPlanForm';
import StructuralEditor from '../components/StructuralEditor';
import LessonPlanViewer from '../components/LessonPlanViewer';
import GeneratedPlansLibrary from '../components/GeneratedPlansLibrary';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import {
  fetchLessonPlan,
  fetchPlanByCompetency,
  deleteGeneratedPlan,
  LessonPlanResponse,
  LessonPlanPayload,
  LessonPlanDto,
} from '@/services/lessonPlanApi';

const API_BASE_URL =
  typeof window !== 'undefined' && window.location.hostname
    ? `http://${window.location.hostname}:8000`
    : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000');

export default function Home() {
  const [activeMainTab, setActiveMainTab] = useState<'generator' | 'library'>('generator');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isViewing, setIsViewing] = useState<boolean>(false);
  const [generationMode, setGenerationMode] = useState<'standard' | 'stream'>('standard');
  const [activeViewTab, setActiveViewTab] = useState<'viewer' | 'editor'>('viewer');
  const [planData, setPlanData] = useState<LessonPlanResponse | null>(null);
  const [currentPlanFilename, setCurrentPlanFilename] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [streamedText, setStreamedText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [notificationMessage, setNotificationMessage] = useState<string | null>(null);

  // View existing generated plan for the specified competency level
  const handleViewPlan = async (formData: {
    competencyLevel: string;
    gradeLevel: string;
    subject: string;
  }) => {
    setIsViewing(true);
    setError(null);
    setNotificationMessage(null);

    try {
      const result = await fetchPlanByCompetency(
        formData.competencyLevel,
        formData.gradeLevel,
        formData.subject
      );

      setPlanData({
        competency_level: result.plan.competence_level,
        grade_level: result.plan.grade,
        subject: result.plan.subject,
        lesson_plan: result.plan,
        fact_check_report: null,
        alignment_report: null,
      });
      setCurrentPlanFilename(result.filename);
      setGenerationMode('standard');
      setActiveViewTab('viewer');
      setNotificationMessage(
        `Showing saved lesson plan for Competency Level ${formData.competencyLevel} (${result.filename})`
      );
    } catch (err: any) {
      setError(
        err.message ||
        `No saved lesson plan found for ${formData.gradeLevel} ${formData.subject} Competency Level "${formData.competencyLevel}". Click "Generate Lesson Plan" to create one.`
      );
    } finally {
      setIsViewing(false);
    }
  };

  // Permanently delete the currently viewed lesson plan file
  const handleDeleteCurrentPlan = async () => {
    if (!currentPlanFilename) return;
    setIsDeleting(true);
    setError(null);

    try {
      const res = await deleteGeneratedPlan(currentPlanFilename);
      const deletedName = currentPlanFilename;
      setPlanData(null);
      setCurrentPlanFilename(null);
      setIsDeleteModalOpen(false);
      setNotificationMessage(res.message || `Lesson plan "${deletedName}" has been permanently deleted.`);
      setTimeout(() => setNotificationMessage(null), 5000);
    } catch (err: any) {
      setError(err.message || `Failed to delete lesson plan "${currentPlanFilename}".`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleStandardGenerate = async (formData: {
    competencyLevel: string;
    gradeLevel: string;
    subject: string;
    periods: number;
    durationMinutes: number;
    timeSlot: string;
  }) => {
    setIsLoading(true);
    setError(null);
    setPlanData(null);
    setCurrentPlanFilename(null);

    try {
      const competency = formData.competencyLevel || '8.1.1';
      const periodsCount = Math.min(Math.max(Number(formData.periods) || 1, 1), 4);
      const duration = Number(formData.durationMinutes) || periodsCount * 40;
      const timeSlotString =
        formData.timeSlot || `${duration} Minutes (${periodsCount} ${periodsCount === 1 ? 'Period' : 'Periods'})`;

      const payload: LessonPlanPayload = {
        competency_level: competency,
        topic_query: `Competency ${competency}`,
        grade_level: formData.gradeLevel || 'Grade 8',
        subject: formData.subject || 'Civic Education',
        periods: periodsCount,
        time_slot: timeSlotString,
        duration_minutes: duration,
      };

      const result: LessonPlanResponse = await fetchLessonPlan(payload);
      setPlanData(result);
      setCurrentPlanFilename(null);
      setActiveViewTab('viewer');
    } catch (err: any) {
      setError(err.message || 'Failed to generate lesson plan. Ensure backend and Ollama are running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateStream = async (formData: {
    competencyLevel: string;
    gradeLevel: string;
    subject: string;
    periods: number;
    durationMinutes: number;
    timeSlot: string;
  }) => {
    setIsLoading(true);
    setError(null);
    setStreamedText('');
    setPlanData(null);
    setCurrentPlanFilename(null);

    const competency = formData.competencyLevel || '8.1.1';
    const periodsCount = Math.min(Math.max(Number(formData.periods) || 1, 1), 4);
    const duration = Number(formData.durationMinutes) || periodsCount * 40;
    const timeSlotString =
      formData.timeSlot || `${duration} Minutes (${periodsCount} ${periodsCount === 1 ? 'Period' : 'Periods'})`;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/lessonplan/generate-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `Competency ${competency}`,
          competency_level: competency,
          grade_level: formData.gradeLevel || 'Grade 8',
          subject: formData.subject || 'Civic Education',
          periods: periodsCount,
          time_slot: timeSlotString,
          duration_minutes: duration,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Streaming failed with status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const textChunk = line.replace('data: ', '');
            setStreamedText((prev) => prev + textChunk + ' ');
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Real-time stream processing failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (formData: any) => {
    if (generationMode === 'standard') {
      handleStandardGenerate(formData);
    } else {
      handleGenerateStream(formData);
    }
  };

  // Allows loading any saved plan from the library directly into the main viewer & structural editor
  const handleLoadPlanToViewer = (savedPlan: LessonPlanDto) => {
    setPlanData({
      competency_level: savedPlan.competence_level,
      grade_level: savedPlan.grade,
      subject: savedPlan.subject,
      lesson_plan: savedPlan,
      fact_check_report: null,
      alignment_report: null,
    });
    setGenerationMode('standard');
    setActiveViewTab('viewer');
    setActiveMainTab('generator');
  };

  return (
    <main className="min-h-screen bg-slate-100 py-10 px-4 sm:px-8 max-w-5xl mx-auto">
      {/* Header */}
      <header className="mb-8 text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-100/80 border border-indigo-200 text-indigo-700 text-xs font-extrabold tracking-wide uppercase">
          🚀 NIE & University of Peradeniya Practice Teaching RAG
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight">
          Lesson Plan Generator
        </h1>
        <p className="text-slate-600 max-w-lg mx-auto text-sm sm:text-base font-medium">
          Adaptive multi-period lesson plans scaled to NIE curriculum guidelines (Grades 6-9)
        </p>

        {/* Top-Level Navigation Tabs: Generator vs Saved Plans Library */}
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => setActiveMainTab('generator')}
            className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-extrabold transition-all inline-flex items-center gap-2 shadow-xs ${
              activeMainTab === 'generator'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/25 ring-2 ring-indigo-600/30'
                : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-300'
            }`}
          >
            <span>✨</span>
            <span>Lesson Plan Generator</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveMainTab('library')}
            className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-extrabold transition-all inline-flex items-center gap-2 shadow-xs ${
              activeMainTab === 'library'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/25 ring-2 ring-indigo-600/30'
                : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-300'
            }`}
          >
            <span>📚</span>
            <span>Generated Plans Library</span>
            <span className="px-2 py-0.5 text-[10px] font-black rounded-full bg-indigo-100 text-indigo-700 border border-indigo-200">
              Saved
            </span>
          </button>
        </div>
      </header>

      {/* VIEW 1: GENERATED PLANS LIBRARY (VIEW & DELETE OPTIONS) */}
      {activeMainTab === 'library' && (
        <GeneratedPlansLibrary onPlanLoadedToViewer={handleLoadPlanToViewer} />
      )}

      {/* VIEW 2: COMPLETE LESSON PLAN GENERATOR (ALL ORIGINAL ELEMENTS PRESERVED) */}
      {activeMainTab === 'generator' && (
        <div className="space-y-6">
          {/* Mode Toggle */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex p-1.5 bg-slate-200/80 backdrop-blur-md rounded-2xl border border-slate-300/80">
              <button
                type="button"
                onClick={() => setGenerationMode('standard')}
                className={`px-5 py-2 rounded-xl text-xs font-bold transition-all ${
                  generationMode === 'standard'
                    ? 'bg-white text-indigo-700 shadow-md'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                📋 Structured Plan
              </button>
              <button
                type="button"
                onClick={() => setGenerationMode('stream')}
                className={`px-5 py-2 rounded-xl text-xs font-bold transition-all ${
                  generationMode === 'stream'
                    ? 'bg-white text-indigo-700 shadow-md'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ⚡ Real-Time Stream
              </button>
            </div>
          </div>

          {/* 1. LESSON PLAN GENERATOR BOX */}
          <LessonPlanForm
            onSubmit={handleFormSubmit}
            isLoading={isLoading}
          />

          {/* Success / Info Alert */}
          {notificationMessage && (
            <div className="max-w-[860px] mx-auto p-3.5 my-3 text-emerald-800 bg-emerald-50 rounded-xl border border-emerald-200 shadow-2xs text-xs font-semibold flex items-center justify-between animate-in fade-in duration-150">
              <span>✅ {notificationMessage}</span>
              <button
                type="button"
                onClick={() => setNotificationMessage(null)}
                className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <div className="max-w-[860px] mx-auto p-3.5 my-3 text-red-700 bg-red-50 rounded-xl border border-red-200 shadow-sm text-sm font-semibold flex items-center justify-between animate-in fade-in duration-150">
              <span>⚠️ {error}</span>
              <button
                type="button"
                onClick={() => setError(null)}
                className="text-red-700 hover:text-red-900 font-bold ml-2 text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>
          )}

          {/* 2. SEE LESSON PLAN BOX (MATCHING CARD BOX DIRECTLY BELOW GENERATE BOX) */}
          <div style={{ marginTop: '24px' }}>
            {/* State A: Currently Loading / Generating */}
            {isLoading ? (
              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '40px 24px',
                  borderRadius: '16px',
                  border: '1.5px solid #818cf8',
                  boxShadow: '0 10px 25px -5px rgba(99, 102, 241, 0.12), 0 8px 10px -6px rgba(99, 102, 241, 0.08)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  gap: '16px',
                  maxWidth: '860px',
                  margin: '0 auto',
                  width: '100%',
                  boxSizing: 'border-box',
                }}
              >
                <div
                  style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    backgroundColor: '#eef2ff',
                    border: '2px solid #c7d2fe',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '28px',
                  }}
                >
                  <span className="animate-spin inline-block">⏳</span>
                </div>
                <div>
                  <h4 style={{ fontSize: '18px', fontWeight: '800', color: '#1e1b4b', margin: '0 0 6px 0' }}>
                    Generating Lesson Plan...
                  </h4>
                  <p style={{ fontSize: '13px', color: '#64748b', maxWidth: '480px', margin: '0 auto', lineHeight: '1.5' }}>
                    AI is retrieving official NIE curriculum guidelines, constructing teacher-student activities,
                    and structuring the Peradeniya 5-column lesson plan.
                  </p>
                </div>
                {/* Visual Step Progress Badges */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginTop: '6px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', backgroundColor: '#f1f5f9', color: '#475569' }}>
                    📚 1. NIE Syllabus Retrieval
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', backgroundColor: '#f1f5f9', color: '#475569' }}>
                    🎯 2. Bloom's Taxonomy Outcomes
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', backgroundColor: '#e0e7ff', color: '#4338ca', border: '1px solid #c7d2fe' }}>
                    ⏱️ 3. Peradeniya Multi-Period Table
                  </span>
                </div>
              </div>
            ) : generationMode === 'stream' && (streamedText || isLoading) ? (
              /* State B: Real-time Stream Output in matching 860px box */
              <div
                style={{
                  backgroundColor: '#0f172a',
                  padding: '24px',
                  borderRadius: '16px',
                  border: '1px solid #1e293b',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
                  maxWidth: '860px',
                  margin: '0 auto',
                  width: '100%',
                  boxSizing: 'border-box',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #334155', paddingBottom: '12px', marginBottom: '16px' }}>
                  <span style={{ fontSize: '13px', fontWeight: '800', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    ⚡ Real-Time Lesson Plan Stream
                  </span>
                  <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
                    Ollama Streaming Output
                  </span>
                </div>
                <div className="text-emerald-400 font-mono text-xs sm:text-sm leading-relaxed whitespace-pre-wrap min-h-56">
                  {streamedText}
                  {isLoading && (
                    <span className="animate-pulse inline-block w-2 h-4 bg-emerald-400 ml-1">▌</span>
                  )}
                </div>
              </div>
            ) : planData ? (
              /* State C: Generated Lesson Plan Displayed (Standard Mode) */
              <div className="space-y-3" style={{ maxWidth: '860px', margin: '0 auto', width: '100%' }}>
                {/* Tab Switcher between Viewer and Raw Editor */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0 4px',
                  }}
                >
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab('viewer')}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '10px',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        border: 'none',
                        backgroundColor: activeViewTab === 'viewer' ? '#4f46e5' : '#e2e8f0',
                        color: activeViewTab === 'viewer' ? '#ffffff' : '#334155',
                        transition: 'all 0.2s',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <span>📄</span>
                      <span>Peradeniya Table Viewer</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab('editor')}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '10px',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        border: 'none',
                        backgroundColor: activeViewTab === 'editor' ? '#4f46e5' : '#e2e8f0',
                        color: activeViewTab === 'editor' ? '#ffffff' : '#334155',
                        transition: 'all 0.2s',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <span>✏️</span>
                      <span>Structural Editor</span>
                    </button>
                  </div>
                  <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>
                    Peradeniya Practice Teaching Layout
                  </span>
                </div>

                {/* Tab 1: Full Peradeniya Practice Teaching Viewer */}
                {activeViewTab === 'viewer' && (
                  <LessonPlanViewer
                    plan={planData.lesson_plan}
                    factCheck={planData.fact_check_report}
                    alignment={planData.alignment_report}
                    filename={currentPlanFilename || undefined}
                    onEditInGenerator={() => setActiveViewTab('editor')}
                    onDeletePlan={currentPlanFilename ? () => setIsDeleteModalOpen(true) : undefined}
                  />
                )}

                {/* Tab 2: Interactive Structural Editor */}
                {activeViewTab === 'editor' && (
                  <div style={{ maxWidth: '860px', margin: '0 auto', width: '100%' }}>
                    <StructuralEditor
                      initialPlan={planData.lesson_plan as any}
                      onSave={(updated) => {
                        setPlanData((prev) => (prev ? { ...prev, lesson_plan: updated as any } : null));
                        setNotificationMessage('Updated lesson plan saved successfully!');
                        setTimeout(() => setNotificationMessage(null), 3000);
                      }}
                    />
                  </div>
                )}
              </div>
            ) : (
              /* State D: Empty / Placeholder State Box matching Generator Box */
              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '36px 24px',
                  borderRadius: '16px',
                  border: '1.5px dashed #cbd5e1',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  gap: '12px',
                  maxWidth: '860px',
                  margin: '0 auto',
                  width: '100%',
                  boxSizing: 'border-box',
                }}
              >
                <div
                  style={{
                    width: '54px',
                    height: '54px',
                    borderRadius: '50%',
                    backgroundColor: '#eef2ff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '26px',
                    color: '#4f46e5',
                  }}
                >
                  📄
                </div>
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', margin: '0 0 4px 0' }}>
                    See Lesson Plan
                  </h4>
                  <p style={{ fontSize: '13px', color: '#64748b', maxWidth: '480px', margin: '0 auto', lineHeight: '1.5' }}>
                    Configure the Subject, Grade, and Competency Level in the generator box above, then click{' '}
                    <strong style={{ color: '#4f46e5' }}>"✨ Generate Lesson Plan"</strong> to generate and see your
                    lesson plan here.
                  </p>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '600', padding: '3px 10px', borderRadius: '9999px', backgroundColor: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0' }}>
                    🏛️ University of Peradeniya Format
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: '600', padding: '3px 10px', borderRadius: '9999px', backgroundColor: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0' }}>
                    ⏱️ Multi-Period Scaling (40 - 160 min)
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: '600', padding: '3px 10px', borderRadius: '9999px', backgroundColor: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0' }}>
                    🎯 NIE Syllabus Grounding
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        filename={currentPlanFilename || ''}
        planTitle={planData?.lesson_plan?.lesson || planData?.lesson_plan?.competence || ''}
        isDeleting={isDeleting}
        onConfirm={handleDeleteCurrentPlan}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </main>
  );
}
 