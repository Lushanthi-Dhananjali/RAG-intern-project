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
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window !== 'undefined'
    ? `http://${window.location.hostname}:8000`
    : 'http://localhost:8000');

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

          {/* Generation Form with Dynamic Selectors */}
          <LessonPlanForm
            onSubmit={handleFormSubmit}
            isLoading={isLoading}
          />

          {/* Success / Info Alert */}
          {notificationMessage && (
            <div className="p-4 my-4 text-emerald-800 bg-emerald-50 rounded-xl border border-emerald-200 shadow-2xs text-xs font-semibold flex items-center justify-between animate-in fade-in duration-150">
              <span>✅ {notificationMessage}</span>
              <button
                type="button"
                onClick={() => setNotificationMessage(null)}
                className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 text-sm"
              >
                ✕
              </button>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <div className="p-4 my-6 text-red-700 bg-red-50 rounded-xl border border-red-200 shadow-sm text-sm font-semibold">
              ⚠️ {error}
            </div>
          )}

          {/* Structured Output Section: Viewed / Generated Lesson Plan Below Competency Level */}
          {generationMode === 'standard' && planData && (
            <div className="mt-8 space-y-6">
              {/* Action Toolbar for the Viewed Plan */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">
                    📄 Level {planData.competency_level}
                  </span>
                  <span className="text-xs font-semibold text-slate-600">
                    {planData.grade_level} • {planData.subject}
                  </span>
                  {currentPlanFilename && (
                    <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md hidden sm:inline-block">
                      {currentPlanFilename}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors inline-flex items-center gap-1.5"
                  >
                    🖨️ Print
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(planData.lesson_plan, null, 2));
                      setNotificationMessage("Lesson plan JSON copied to clipboard!");
                      setTimeout(() => setNotificationMessage(null), 3000);
                    }}
                    className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors inline-flex items-center gap-1.5"
                  >
                    📋 Copy JSON
                  </button>
                  {currentPlanFilename && (
                    <button
                      type="button"
                      onClick={() => setIsDeleteModalOpen(true)}
                      disabled={isDeleting}
                      className="px-3 py-1.5 text-xs font-bold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-colors inline-flex items-center gap-1.5 disabled:opacity-50"
                      title="Permanently delete this generated lesson plan from storage"
                    >
                      🗑️ Delete Plan
                    </button>
                  )}
                </div>
              </div>

              {/* Verification Guardrails Summary */}
              {(planData.fact_check_report || planData.alignment_report) && (
                <section className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap gap-4 items-center justify-between text-xs">
                  {planData.fact_check_report && (
                    <div>
                      <span className="font-bold text-slate-700">Fact-Check Grounding: </span>
                      <span
                        className={`font-semibold ${
                          planData.fact_check_report.passed ? 'text-emerald-600' : 'text-amber-600'
                        }`}
                      >
                        {(planData.fact_check_report.grounding_score * 100).toFixed(1)}% (
                        {planData.fact_check_report.passed ? 'Passed' : 'Review Needed'})
                      </span>
                    </div>
                  )}
                  {planData.alignment_report && (
                    <div>
                      <span className="font-bold text-slate-700">Goal Alignment: </span>
                      <span
                        className={`font-semibold ${
                          planData.alignment_report.passed_alignment_guardrail
                            ? 'text-emerald-600'
                            : 'text-amber-600'
                        }`}
                      >
                        {(planData.alignment_report.overall_alignment_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </section>
              )}

              {/* Tab Switcher between Viewer and Raw Editor */}
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveViewTab('viewer')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      activeViewTab === 'viewer'
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                    }`}
                  >
                    📄 Peradeniya Table Viewer
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveViewTab('editor')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      activeViewTab === 'editor'
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                    }`}
                  >
                    ✏️ Structural Editor
                  </button>
                </div>
                <span className="text-xs text-slate-400 font-medium">Peradeniya Practice Teaching Layout</span>
              </div>

              {/* Tab 1: Render Peradeniya Practice Teaching Viewer */}
              {activeViewTab === 'viewer' && (
                <LessonPlanViewer
                  plan={planData.lesson_plan}
                  factCheck={planData.fact_check_report}
                  alignment={planData.alignment_report}
                />
              )}

              {/* Tab 2: Render Interactive Structural Editor */}
              {activeViewTab === 'editor' && (
                <StructuralEditor initialPlan={planData.lesson_plan as any} />
              )}
            </div>
          )}

          {/* Real-time Streaming Display */}
          {generationMode === 'stream' && (streamedText || isLoading) && (
            <div className="mt-8 bg-slate-900 p-6 rounded-2xl shadow-xl border border-slate-800 text-green-400 font-mono text-sm leading-relaxed whitespace-pre-wrap min-h-56">
              {streamedText}
              {isLoading && (
                <span className="animate-pulse inline-block w-2 h-4 bg-green-400 ml-1">▌</span>
              )}
            </div>
          )}
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
 