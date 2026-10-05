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
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center justify-between animate-in fade-in duration-150">
          <span>{successMessage}</span>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 text-sm"
          >
            ✕
          </button>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-800 rounded-xl text-xs font-semibold flex items-center justify-between animate-in fade-in duration-150">
          <span>⚠️ {error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-red-700 hover:text-red-900 font-bold ml-2 text-sm"
          >
            ✕
          </button>
        </div>
      )}

      {/* Competency Level Selection Panel */}
      <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        {/* Panel Header */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base sm:text-lg font-black text-slate-900 flex items-center gap-2">
              📚 View Saved Lesson Plan
            </h3>
            <p className="text-xs text-slate-500">
              Select or type the Competency Level to view the lesson plan below
            </p>
          </div>

          <button
            type="button"
            onClick={() => loadPlans(true)}
            disabled={isRefreshing || isLoading}
            className="px-4 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors inline-flex items-center gap-2 self-start sm:self-auto disabled:opacity-50 shadow-2xs"
            title="Refresh saved lesson plans from backend storage"
          >
            <span className={isRefreshing ? 'animate-spin inline-block' : ''}>🔄</span>
            <span>{isRefreshing ? 'Refreshing...' : `Refresh List (${plans.length} Saved)`}</span>
          </button>
        </div>

        {/* Selectors Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Subject */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
              Subject
            </label>
            <select
              value={selectedSubject}
              onChange={(e) => {
                setSelectedSubject(e.target.value);
                setError(null);
              }}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-slate-900 font-semibold"
            >
              <option value="Civic Education">🏛️ Civic Education</option>
              <option value="Science">🧪 Science</option>
              <option value="All">All Subjects</option>
            </select>
          </div>

          {/* Grade */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
              Grade Level
            </label>
            <select
              value={selectedGrade}
              onChange={(e) => {
                setSelectedGrade(e.target.value);
                setError(null);
              }}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-slate-900 font-semibold"
            >
              <option value="Grade 8">Grade 8</option>
              <option value="Grade 6">Grade 6</option>
              <option value="Grade 7">Grade 7</option>
              <option value="Grade 9">Grade 9</option>
              <option value="All">All Grades</option>
            </select>
          </div>

          {/* Competency Level Input & Quick Dropdown */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
              Competency Level
            </label>
            <div className="space-y-1.5">
              <input
                type="text"
                value={typedCompetency}
                onChange={(e) => {
                  setTypedCompetency(e.target.value);
                  setError(null);
                }}
                placeholder="e.g. 8.1.1, 8.4.2"
                className="w-full px-3 py-2 text-xs font-mono font-bold bg-slate-50 border border-indigo-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-indigo-700 placeholder:text-slate-400"
              />

              {/* Quick Dropdown Picker from Saved Plans */}
              {filteredPlans.length > 0 && (
                <select
                  value={filteredPlans.some((p) => p.competence_level === typedCompetency) ? typedCompetency : ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      setTypedCompetency(e.target.value);
                      setError(null);
                    }
                  }}
                  className="w-full px-2 py-1 text-[11px] bg-slate-100 border border-slate-200 rounded-lg text-slate-700 focus:outline-hidden cursor-pointer"
                >
                  <option value="">-- Or choose from {filteredPlans.length} saved plans --</option>
                  {filteredPlans.map((p) => (
                    <option key={p.filename} value={p.competence_level}>
                      Level {p.competence_level} ({p.lesson || p.competence || p.filename})
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        </div>

        {/* View Plan Button */}
        <div className="pt-2">
          <button
            type="button"
            onClick={handleViewCompetencyPlan}
            disabled={isDetailLoading || !typedCompetency.trim()}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs sm:text-sm font-bold transition-all shadow-xs flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isDetailLoading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Loading Lesson Plan...
              </>
            ) : (
              `👁️ View Plan for Competency Level ${typedCompetency || '...'}`
            )}
          </button>
        </div>
      </div>

      {/* LESSON PLAN VIEWED DIRECTLY BELOW COMPETENCY LEVEL (NO WALL OF 30 PLANS) */}
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
                className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors inline-flex items-center gap-1.5"
              >
                🖨️ Print
              </button>
              <button
                type="button"
                onClick={handleCopyJson}
                className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors inline-flex items-center gap-1.5"
              >
                {copied ? '✅ Copied' : '📋 Copy JSON'}
              </button>
              {onPlanLoadedToViewer && (
                <button
                  type="button"
                  onClick={() => onPlanLoadedToViewer(activePlan)}
                  className="px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-lg transition-colors inline-flex items-center gap-1.5"
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
                  className="px-3 py-1.5 text-xs font-bold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-colors inline-flex items-center gap-1.5 disabled:opacity-50"
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
