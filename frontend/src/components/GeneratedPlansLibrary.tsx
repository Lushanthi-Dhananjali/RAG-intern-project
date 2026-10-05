'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  fetchGeneratedPlans,
  fetchGeneratedPlanDetail,
  deleteGeneratedPlan,
  fetchPlanByCompetency,
  GeneratedPlanSummary,
  LessonPlanDto,
} from '@/services/lessonPlanApi';
import DeleteConfirmModal from './DeleteConfirmModal';
import LessonPlanViewer from './LessonPlanViewer';

interface GeneratedPlansLibraryProps {
  onPlanLoadedToViewer?: (plan: LessonPlanDto) => void;
}

export default function GeneratedPlansLibrary({
  onPlanLoadedToViewer,
}: GeneratedPlansLibraryProps) {
  const [plans, setPlans] = useState<GeneratedPlanSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [selectedGrade, setSelectedGrade] = useState<string>('Grade 8');
  const [selectedSubject, setSelectedSubject] = useState<string>('Civic Education');
  const [typedCompetency, setTypedCompetency] = useState<string>('8.1.1');

  // Currently viewed plan (rendered below competency level)
  const [activePlan, setActivePlan] = useState<LessonPlanDto | null>(null);
  const [activeFilename, setActiveFilename] = useState<string>('');
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  // Delete Modal state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Load all plans from backend storage
  const loadPlans = useCallback(async (manual = false) => {
    if (manual) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const data = await fetchGeneratedPlans();
      setPlans(data);
      if (manual) {
        setSuccessMessage(`✅ Refreshed! Found ${data.length} saved lesson plans.`);
        setTimeout(() => setSuccessMessage(null), 3500);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch generated lesson plans. Ensure backend is running.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  // Saved plans matching the current Subject and Grade
  const filteredPlans = useMemo(() => {
    return plans.filter((p) => {
      const matchGrade = !selectedGrade || selectedGrade === 'All' || p.grade.toLowerCase().includes(selectedGrade.toLowerCase());
      const matchSubject = !selectedSubject || selectedSubject === 'All' || p.subject.toLowerCase().includes(selectedSubject.toLowerCase());
      return matchGrade && matchSubject;
    });
  }, [plans, selectedGrade, selectedSubject]);

  // Handle viewing plan for the chosen competency level
  const handleViewCompetencyPlan = async () => {
    const comp = typedCompetency.trim();
    if (!comp) {
      setError('Please enter or select a Competency Level (e.g. 8.1.1).');
      return;
    }

    setIsDetailLoading(true);
    setError(null);
    setSuccessMessage(null);

    // 1. Try local cache from matching plans first
    const localMatch = filteredPlans.find(
      (p) => p.competence_level.toLowerCase() === comp.toLowerCase()
    ) || plans.find(
      (p) => p.competence_level.toLowerCase() === comp.toLowerCase()
    );

    if (localMatch) {
      try {
        const detail = await fetchGeneratedPlanDetail(localMatch.filename);
        setActivePlan(detail.plan);
        setActiveFilename(detail.filename);
        setIsDetailLoading(false);
        return;
      } catch {
        // Fall back to direct backend lookup
      }
    }

    // 2. Fetch directly from backend by competency
    try {
      const result = await fetchPlanByCompetency(
        comp,
        selectedGrade !== 'All' ? selectedGrade : undefined,
        selectedSubject !== 'All' ? selectedSubject : undefined
      );
      setActivePlan(result.plan);
      setActiveFilename(result.filename);
    } catch (err: any) {
      setActivePlan(null);
      setActiveFilename('');
      setError(
        err.message ||
        `No saved lesson plan found for Competency Level "${comp}". Check Grade and Subject or generate a new plan.`
      );
    } finally {
      setIsDetailLoading(false);
    }
  };

  // Handle delete confirmation
  const handleConfirmDelete = async () => {
    if (!activeFilename) return;

    setIsDeleting(true);
    setError(null);
    try {
      const res = await deleteGeneratedPlan(activeFilename);
      const deletedName = activeFilename;
      setActivePlan(null);
      setActiveFilename('');
      setIsDeleteModalOpen(false);
      setSuccessMessage(res.message || `Successfully deleted lesson plan "${deletedName}".`);
      await loadPlans();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.message || `Failed to delete lesson plan "${activeFilename}".`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCopyJson = () => {
    if (!activePlan) return;
    navigator.clipboard.writeText(JSON.stringify(activePlan, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="space-y-6">
      {/* Action / Notification Alerts */}
      {successMessage && (
        <div className="max-w-[640px] mx-auto p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center justify-between shadow-xs animate-in fade-in duration-150">
          <span>{successMessage}</span>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 text-sm cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {error && (
        <div className="max-w-[640px] mx-auto p-3.5 bg-red-50 border border-red-200 text-red-800 rounded-xl text-xs font-semibold flex items-center justify-between shadow-xs animate-in fade-in duration-150">
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

      {/* Competency Level Selection Panel: Styled Exactly Like LessonPlanForm Box */}
      <div
        style={{
          backgroundColor: '#ffffff',
          padding: '24px',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '18px',
          maxWidth: '640px',
          margin: '0 auto',
        }}
      >
        {/* Panel Header with Title and Refresh Button */}
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
              <span>📚</span>
              <span>View Saved Lesson Plan</span>
            </h3>
            <p
              style={{
                fontSize: '12px',
                color: '#64748b',
                margin: '2px 0 0 0',
              }}
            >
              Select or type the Competency Level to view the lesson plan below
            </p>
          </div>

          <button
            type="button"
            onClick={() => loadPlans(true)}
            disabled={isRefreshing || isLoading}
            style={{
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: '700',
              color: '#334155',
              backgroundColor: '#f1f5f9',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              cursor: isRefreshing || isLoading ? 'not-allowed' : 'pointer',
              opacity: isRefreshing || isLoading ? 0.6 : 1,
              transition: 'background-color 0.2s',
            }}
            title="Refresh saved lesson plans from backend storage"
          >
            <span className={isRefreshing ? 'animate-spin inline-block' : ''}>🔄</span>
            <span>{isRefreshing ? 'Refreshing...' : `Refresh List (${plans.length} Saved)`}</span>
          </button>
        </div>

        {/* 1. Subject and Grade Level (Grid matching LessonPlanForm) */}
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
              Subject
            </label>
            <select
              value={selectedSubject}
              onChange={(e) => {
                setSelectedSubject(e.target.value);
                setError(null);
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
                cursor: 'pointer',
              }}
            >
              <option value="Civic Education">🏛️ Civic Education</option>
              <option value="Science">🧪 Science</option>
              <option value="All">All Subjects</option>
            </select>
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
              Grade Level
            </label>
            <select
              value={selectedGrade}
              onChange={(e) => {
                setSelectedGrade(e.target.value);
                setError(null);
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
                cursor: 'pointer',
              }}
            >
              <option value="Grade 8">Grade 8</option>
              <option value="Grade 6">Grade 6</option>
              <option value="Grade 7">Grade 7</option>
              <option value="Grade 9">Grade 9</option>
              <option value="All">All Grades</option>
            </select>
          </div>
        </div>

        {/* 2. Competency Level Input & Quick Dropdown (Matching LessonPlanForm input style) */}
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
            NIE Competency Level
          </label>
          <input
            type="text"
            value={typedCompetency}
            onChange={(e) => {
              setTypedCompetency(e.target.value);
              setError(null);
            }}
            placeholder={selectedSubject === 'Science' ? 'e.g. 1.6, 1.7, 2.1' : 'e.g. 8.1.1, 8.4.2, 8.6.8'}
            disabled={isLoading || isDetailLoading}
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

          {/* Quick Dropdown Picker from Saved Plans */}
          {filteredPlans.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <select
                value={filteredPlans.some((p) => p.competence_level === typedCompetency) ? typedCompetency : ''}
                onChange={(e) => {
                  if (e.target.value) {
                    setTypedCompetency(e.target.value);
                    setError(null);
                  }
                }}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  backgroundColor: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: '500',
                  color: '#334155',
                  outline: 'none',
                  boxSizing: 'border-box',
                  cursor: 'pointer',
                }}
              >
                <option value="">-- Or choose from {filteredPlans.length} saved plans --</option>
                {filteredPlans.map((p) => (
                  <option key={p.filename} value={p.competence_level}>
                    Level {p.competence_level} ({p.lesson || p.competence || p.filename})
                  </option>
                ))}
              </select>
            </div>
          )}

          <span style={{ display: 'block', fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
            {selectedSubject === 'Science'
              ? 'Enter Science Competency Level (e.g. 1.6)'
              : 'Enter Civic Education Competency Code (e.g. 8.1.1, 8.4.2, 8.6.8)'}
          </span>
        </div>

        {/* 3. View Plan Button (Matching LessonPlanForm Submit Button) */}
        <button
          type="button"
          onClick={handleViewCompetencyPlan}
          disabled={isDetailLoading || !typedCompetency.trim()}
          style={{
            width: '100%',
            marginTop: '6px',
            padding: '12px 16px',
            borderRadius: '10px',
            backgroundColor: isDetailLoading || !typedCompetency.trim() ? '#94a3b8' : '#4f46e5',
            color: '#ffffff',
            fontWeight: '700',
            fontSize: '14px',
            border: 'none',
            cursor: isDetailLoading || !typedCompetency.trim() ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          {isDetailLoading ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Loading Lesson Plan...</span>
            </>
          ) : (
            `👁️ View Plan for Competency Level ${typedCompetency || '...'}`
          )}
        </button>
      </div>

      {/* LESSON PLAN VIEWED DIRECTLY BELOW COMPETENCY LEVEL */}
      {activePlan && (
        <div className="space-y-4 animate-in fade-in duration-200">
          {/* Action Toolbar on Viewed Plan */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
            <div className="flex items-center gap-2">
              <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">
                📄 Competency Level {activePlan.competence_level}
              </span>
              <span className="text-xs font-semibold text-slate-600">
                {activePlan.grade} • {activePlan.subject}
              </span>
              {activeFilename && (
                <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md hidden sm:inline-block">
                  {activeFilename}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => window.print()}
                className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors inline-flex items-center gap-1.5 cursor-pointer"
              >
                🖨️ Print
              </button>
              <button
                type="button"
                onClick={handleCopyJson}
                className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors inline-flex items-center gap-1.5 cursor-pointer"
              >
                {copied ? '✅ Copied' : '📋 Copy JSON'}
              </button>
              {onPlanLoadedToViewer && (
                <button
                  type="button"
                  onClick={() => onPlanLoadedToViewer(activePlan)}
                  className="px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-lg transition-colors inline-flex items-center gap-1.5 cursor-pointer"
                  title="Load into Main Viewer and Structural Editor"
                >
                  ✏️ Edit in Generator
                </button>
              )}
              {activeFilename && (
                <button
                  type="button"
                  onClick={() => setIsDeleteModalOpen(true)}
                  disabled={isDeleting}
                  className="px-3 py-1.5 text-xs font-bold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-colors inline-flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                  title="Delete this generated lesson plan permanently from storage"
                >
                  🗑️ Delete Plan
                </button>
              )}
            </div>
          </div>

          {/* Full Peradeniya Practice Teaching Table Layout */}
          <LessonPlanViewer plan={activePlan} />
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        filename={activeFilename}
        planTitle={activePlan?.lesson || activePlan?.competence || ''}
        isDeleting={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </section>
  );
}
