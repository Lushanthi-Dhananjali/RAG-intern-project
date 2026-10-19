"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";

import LessonPlanForm from "../components/LessonPlanForm";
import StructuralEditor from "../components/StructuralEditor";
import LessonPlanViewer from "../components/LessonPlanViewer";
import GeneratedPlansLibrary from "../components/GeneratedPlansLibrary";
import DeleteConfirmModal from "../components/DeleteConfirmModal";
import ActivitySelectionStep from "../components/ActivitySelectionStep";
import MultiPeriodPlanViewer from "../components/MultiPeriodPlanViewer";

// Dynamic import of Step 9 planner views with ssr: false prevents export evaluation crashes
const Step1Inputs = dynamic(() => import("../components/planner/Step1Inputs"), {
  ssr: false,
  loading: () => <div className="p-6 text-center text-xs text-slate-500 font-semibold bg-white rounded-xl border">Loading Step 1 Inputs...</div>,
});
const Step2OptionsSelection = dynamic(() => import("../components/planner/Step2OptionsSelection"), {
  ssr: false,
  loading: () => <div className="p-6 text-center text-xs text-slate-500 font-semibold bg-white rounded-xl border">Loading Step 2 Options...</div>,
});
const Step3PlanViewer = dynamic(() => import("../components/planner/Step3PlanViewer"), {
  ssr: false,
  loading: () => <div className="p-6 text-center text-xs text-slate-500 font-semibold bg-white rounded-xl border">Loading Step 3 Viewer...</div>,
});

import { useLessonPlanStore } from "@/store/useLessonPlanStore";

import {
  fetchLessonPlan,
  fetchPlanByCompetency,
  deleteGeneratedPlan,
  LessonPlanResponse,
  LessonPlanPayload,
  LessonPlanDto,
} from "@/services/lessonPlanApi";
import {
  PedagogicalActivityOption,
  PedagogicalOptionsResponse,
  CompetencyLevelGenerateResponse,
  LessonPlanSchemaDto,
} from "@/types/lessonPlan";

const API_BASE_URL =
  typeof window !== "undefined" && window.location.hostname
    ? `http://${window.location.hostname}:8000`
    : process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  // Main Navigation Tabs: 'wizard' (Existing Wizard), 'planner' (New Step 9 State Machine), 'generator' (Classic Direct), 'library' (Saved Plans)
  const [activeMainTab, setActiveMainTab] = useState<"wizard" | "planner" | "generator" | "library">("wizard");

  // Step 9 Multi-Period Zustand State
  const { step: multiPeriodStep, resetAll: resetMultiPeriodPlanner } = useLessonPlanStore();

  // Wizard Sub-steps: 1 = Inputs, 2 = Select Activity, 3 = View Plans
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3>(1);

  // Wizard Form State
  const [wizardGrade, setWizardGrade] = useState("Grade 8");
  const [wizardSubject, setWizardSubject] = useState("Civic Education");
  const [wizardCompetency, setWizardCompetency] = useState("8.1.1");
  const [wizardTopicQuery, setWizardTopicQuery] = useState("");
  const [wizardPeriods, setWizardPeriods] = useState<number>(2);
  const [wizardStudentCount, setWizardStudentCount] = useState<number>(35);

  // Activity Discovery State
  const [isLoadingOptions, setIsLoadingOptions] = useState<boolean>(false);
  const [discoveredTopic, setDiscoveredTopic] = useState<string>("");
  const [activityOptions, setActivityOptions] = useState<PedagogicalActivityOption[]>([]);
  const [selectedOptionId, setSelectedOptionId] = useState<string>("");
  const [customStrategy, setCustomStrategy] = useState<string>("");

  // Plan Generation & Execution State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isViewing, setIsViewing] = useState<boolean>(false);
  const [generationMode, setGenerationMode] = useState<"standard" | "stream">("standard");
  const [activeViewTab, setActiveViewTab] = useState<"viewer" | "editor">("viewer");
  const [planData, setPlanData] = useState<LessonPlanResponse | null>(null);
  const [multiPeriodPlans, setMultiPeriodPlans] = useState<LessonPlanSchemaDto[]>([]);

  // Storage, Modal & Notifications
  const [currentPlanFilename, setCurrentPlanFilename] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [streamedText, setStreamedText] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [notificationMessage, setNotificationMessage] = useState<string | null>(null);

  // =========================================================================
  // 1. WIZARD HANDLERS
  // =========================================================================

  const handleDiscoverOptions = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoadingOptions(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/suggest-pedagogical-options`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          competency_level: wizardCompetency.trim(),
          grade_level: wizardGrade,
          subject: wizardSubject,
          student_count: Number(wizardStudentCount),
          periods: Number(wizardPeriods),
        }),
      });

      if (!res.ok) {
        throw new Error(`Activity discovery failed with status: ${res.status}`);
      }

      const data: PedagogicalOptionsResponse = await res.json();
      setDiscoveredTopic(data.lesson_topic);
      setActivityOptions(data.options || []);
      if (data.options && data.options.length > 0) {
        setSelectedOptionId(data.options[0].id);
      }
      setWizardStep(2);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend pedagogical discovery endpoint.");
    } finally {
      setIsLoadingOptions(false);
    }
  };

  const handleGenerateWizardPlans = async () => {
    setError(null);
    setIsLoading(true);

    const selectedOptionObj = activityOptions.find((o) => o.id === selectedOptionId);
    const chosenDescription = selectedOptionObj
      ? `[${selectedOptionObj.title}] ${selectedOptionObj.description} (Grouping: ${selectedOptionObj.student_grouping})`
      : undefined;

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/generate-by-competency-level`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          competency_level: wizardCompetency.trim(),
          topic_query: wizardTopicQuery.trim() || discoveredTopic,
          grade_level: wizardGrade,
          subject: wizardSubject,
          periods: Number(wizardPeriods),
          student_count: Number(wizardStudentCount),
          selected_activity_option: customStrategy.trim() ? undefined : chosenDescription,
          custom_teacher_activity: customStrategy.trim() ? customStrategy.trim() : undefined,
        }),
      });

      if (!res.ok) {
        throw new Error(`Sequential plan generation failed with status: ${res.status}`);
      }

      const data: CompetencyLevelGenerateResponse = await res.json();
      const plans = data.lesson_plans && data.lesson_plans.length > 0
        ? data.lesson_plans
        : [data.lesson_plan];

      setMultiPeriodPlans(plans);

      setPlanData({
        competency_level: data.competency_level,
        grade_level: data.grade_level,
        subject: data.subject,
        lesson_plan: plans[0] as any,
        fact_check_report: data.fact_check_report || null,
        alignment_report: data.alignment_report || null,
      });

      setCurrentPlanFilename(null);
      setWizardStep(3);
      setNotificationMessage(`Successfully generated ${plans.length} sequential 40-minute lesson plan(s).`);
    } catch (err: any) {
      setError(err.message || "Failed to generate sequential lesson plans.");
    } finally {
      setIsLoading(false);
    }
  };

  // =========================================================================
  // 2. CLASSIC GENERATOR HANDLERS
  // =========================================================================

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
      setMultiPeriodPlans([result.plan as any]);
      setCurrentPlanFilename(result.filename);
      setGenerationMode("standard");
      setActiveViewTab("viewer");
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
      const competency = formData.competencyLevel || "8.1.1";
      const periodsCount = Math.min(Math.max(Number(formData.periods) || 1, 1), 4);
      const duration = Number(formData.durationMinutes) || periodsCount * 40;
      const timeSlotString =
        formData.timeSlot || `${duration} Minutes (${periodsCount} ${periodsCount === 1 ? "Period" : "Periods"})`;

      const payload: LessonPlanPayload = {
        competency_level: competency,
        topic_query: `Competency ${competency}`,
        grade_level: formData.gradeLevel || "Grade 8",
        subject: formData.subject || "Civic Education",
        periods: periodsCount,
        time_slot: timeSlotString,
        duration_minutes: duration,
      };

      const result: LessonPlanResponse = await fetchLessonPlan(payload);
      setPlanData(result);
      setMultiPeriodPlans([result.lesson_plan as any]);
      setCurrentPlanFilename(null);
      setActiveViewTab("viewer");
    } catch (err: any) {
      setError(err.message || "Failed to generate lesson plan. Ensure backend and Ollama are running.");
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
    setStreamedText("");
    setPlanData(null);
    setCurrentPlanFilename(null);

    const competency = formData.competencyLevel || "8.1.1";
    const periodsCount = Math.min(Math.max(Number(formData.periods) || 1, 1), 4);
    const duration = Number(formData.durationMinutes) || periodsCount * 40;
    const timeSlotString =
      formData.timeSlot || `${duration} Minutes (${periodsCount} ${periodsCount === 1 ? "Period" : "Periods"})`;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/lessonplan/generate-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: `Competency ${competency}`,
          competency_level: competency,
          grade_level: formData.gradeLevel || "Grade 8",
          subject: formData.subject || "Civic Education",
          periods: periodsCount,
          time_slot: timeSlotString,
          duration_minutes: duration,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Streaming failed with status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const textChunk = line.replace("data: ", "");
            setStreamedText((prev) => prev + textChunk + " ");
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "Real-time stream processing failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClassicFormSubmit = (formData: any) => {
    if (generationMode === "standard") {
      handleStandardGenerate(formData);
    } else {
      handleGenerateStream(formData);
    }
  };

  // =========================================================================
  // 3. STORAGE & DELETION HANDLERS
  // =========================================================================

  const handleLoadPlanToViewer = (savedPlan: LessonPlanDto) => {
    setPlanData({
      competency_level: savedPlan.competence_level,
      grade_level: savedPlan.grade,
      subject: savedPlan.subject,
      lesson_plan: savedPlan,
      fact_check_report: null,
      alignment_report: null,
    });
    setMultiPeriodPlans([savedPlan as any]);
    setGenerationMode("standard");
    setActiveViewTab("viewer");
    setActiveMainTab("generator");
  };

  const handleDeleteCurrentPlan = async () => {
    if (!currentPlanFilename) return;
    setIsDeleting(true);
    setError(null);

    try {
      const res = await deleteGeneratedPlan(currentPlanFilename);
      const deletedName = currentPlanFilename;
      setPlanData(null);
      setMultiPeriodPlans([]);
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

  return (
    <main className="min-h-screen py-10 px-4 sm:px-8 max-w-5xl mx-auto font-sans">
      {/* Header */}
      <header
        style={{
          maxWidth: "860px",
          margin: "0 auto 20px auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          width: "100%",
        }}
      >
        <span
          style={{
            fontSize: "11px",
            fontWeight: "800",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "#059669",
            backgroundColor: "#ecfdf5",
            border: "1px solid #a7f3d0",
            padding: "4px 12px",
            borderRadius: "9999px",
            marginBottom: "10px",
          }}
        >
          LEARN Kandy Practice Teaching Pedagogy
        </span>

        <h1
          className="text-4xl sm:text-5xl font-black tracking-tight"
          style={{ color: "#2563eb", margin: "0 0 8px 0", textAlign: "center" }}
        >
          Lesson Plan Generator
        </h1>
        <p
          className="text-sm sm:text-base font-bold"
          style={{ color: "#65a30d", margin: "0 0 16px 0", textAlign: "center", maxWidth: "680px" }}
        >
          Student-centered 40-minute periods (5m Entrance, 30m Development, 5m Creative Assessment)
        </p>

        {/* Buttons Row 1: Top Navigation Tabs */}
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
            width: "100%",
            margin: "0 auto",
            flexWrap: "wrap",
          }}
        >
          {/* Tab 1: Interactive Wizard */}
          <button
            type="button"
            onClick={() => setActiveMainTab("wizard")}
            style={{
              padding: "10px 18px",
              borderRadius: "12px",
              fontSize: "13px",
              fontWeight: "800",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: activeMainTab === "wizard" ? "#bbf7d0" : "#f0fdf4",
              color: activeMainTab === "wizard" ? "#14532d" : "#166534",
              border: activeMainTab === "wizard" ? "1.5px solid #22c55e" : "1px solid #86efac",
              boxShadow: activeMainTab === "wizard" ? "0 2px 8px -1px rgba(34, 197, 94, 0.35)" : "none",
            }}
          >
            <span>🎯</span>
            <span>2-Step Activity Wizard</span>
            <span
              style={{
                fontSize: "10px",
                fontWeight: "800",
                padding: "2px 6px",
                borderRadius: "9999px",
                backgroundColor: "#dcfce7",
                color: "#15803d",
                border: "1px solid #86efac",
              }}
            >
              Classic
            </span>
          </button>

          {/* Tab 2 (NEW): Multi-Period Planner (Zustand Step 9) */}
          <button
            type="button"
            onClick={() => setActiveMainTab("planner")}
            style={{
              padding: "10px 18px",
              borderRadius: "12px",
              fontSize: "13px",
              fontWeight: "800",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: activeMainTab === "planner" ? "#bbf7d0" : "#f0fdf4",
              color: activeMainTab === "planner" ? "#14532d" : "#166534",
              border: activeMainTab === "planner" ? "1.5px solid #22c55e" : "1px solid #86efac",
              boxShadow: activeMainTab === "planner" ? "0 2px 8px -1px rgba(34, 197, 94, 0.35)" : "none",
            }}
          >
            <span>🚀</span>
            <span>Multi-Period Planner</span>
            <span
              style={{
                fontSize: "10px",
                fontWeight: "800",
                padding: "2px 6px",
                borderRadius: "9999px",
                backgroundColor: "#dcfce7",
                color: "#15803d",
                border: "1px solid #86efac",
              }}
            >
              Step 9
            </span>
          </button>

          {/* Tab 3: Classic Lesson Plan Generator */}
          <button
            type="button"
            onClick={() => setActiveMainTab("generator")}
            style={{
              padding: "10px 18px",
              borderRadius: "12px",
              fontSize: "13px",
              fontWeight: "800",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: activeMainTab === "generator" ? "#bbf7d0" : "#f0fdf4",
              color: activeMainTab === "generator" ? "#14532d" : "#166534",
              border: activeMainTab === "generator" ? "1.5px solid #22c55e" : "1px solid #86efac",
              boxShadow: activeMainTab === "generator" ? "0 2px 8px -1px rgba(34, 197, 94, 0.35)" : "none",
            }}
          >
            <span>✨</span>
            <span>Classic Generator</span>
          </button>

          {/* Tab 4: Generated Plans Library */}
          <button
            type="button"
            onClick={() => setActiveMainTab("library")}
            style={{
              padding: "10px 18px",
              borderRadius: "12px",
              fontSize: "13px",
              fontWeight: "800",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: activeMainTab === "library" ? "#bbf7d0" : "#f0fdf4",
              color: activeMainTab === "library" ? "#14532d" : "#166534",
              border: activeMainTab === "library" ? "1.5px solid #22c55e" : "1px solid #86efac",
              boxShadow: activeMainTab === "library" ? "0 2px 8px -1px rgba(34, 197, 94, 0.35)" : "none",
            }}
          >
            <span>📚</span>
            <span>Generated Plans Library</span>
          </button>
        </div>

        {/* Buttons Row 2: Stream vs Structured toggle (Only on Classic Generator tab) */}
        {activeMainTab === "generator" && (
          <div
            style={{
              display: "flex",
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              width: "100%",
              margin: "10px auto 0 auto",
              flexWrap: "wrap",
            }}
          >
            <button
              type="button"
              onClick={() => setGenerationMode("standard")}
              style={{
                padding: "8px 16px",
                borderRadius: "10px",
                fontSize: "12px",
                fontWeight: "800",
                cursor: "pointer",
                backgroundColor: generationMode === "standard" ? "#e0e7ff" : "#f8fafc",
                color: generationMode === "standard" ? "#3730a3" : "#64748b",
                border: generationMode === "standard" ? "1px solid #818cf8" : "1px solid #cbd5e1",
              }}
            >
              📋 Structured Plan Mode
            </button>
            <button
              type="button"
              onClick={() => setGenerationMode("stream")}
              style={{
                padding: "8px 16px",
                borderRadius: "10px",
                fontSize: "12px",
                fontWeight: "800",
                cursor: "pointer",
                backgroundColor: generationMode === "stream" ? "#e0e7ff" : "#f8fafc",
                color: generationMode === "stream" ? "#3730a3" : "#64748b",
                border: generationMode === "stream" ? "1px solid #818cf8" : "1px solid #cbd5e1",
              }}
            >
              ⚡ Real-Time Stream Mode
            </button>
          </div>
        )}
      </header>

      {/* Global Alerts */}
      {notificationMessage && (
        <div className="max-w-[860px] mx-auto p-3.5 my-3 text-emerald-800 bg-emerald-50 rounded-xl border border-emerald-200 text-xs font-semibold flex items-center justify-between">
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

      {error && (
        <div className="max-w-[860px] mx-auto p-3.5 my-3 text-red-700 bg-red-50 rounded-xl border border-red-200 text-xs font-semibold flex items-center justify-between">
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

      {/* ========================================================================= */}
      {/* VIEW A: 2-STEP INTERACTIVE ACTIVITY WIZARD (EXISTING PIPELINE PRESERVED)  */}
      {/* ========================================================================= */}
      {activeMainTab === "wizard" && (
        <div className="space-y-6 max-w-[860px] mx-auto">
          {/* Stepper Navigation Indicator */}
          <div className="flex items-center justify-between bg-white px-5 py-3 rounded-xl border border-slate-200 text-xs font-bold">
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${wizardStep === 1 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                1
              </span>
              <span className={wizardStep === 1 ? "text-emerald-800 font-extrabold" : "text-slate-500"}>
                Class & Curriculum
              </span>
            </div>
            <span className="text-slate-300">→</span>
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${wizardStep === 2 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                2
              </span>
              <span className={wizardStep === 2 ? "text-emerald-800 font-extrabold" : "text-slate-500"}>
                Activity Strategy
              </span>
            </div>
            <span className="text-slate-300">→</span>
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${wizardStep === 3 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                3
              </span>
              <span className={wizardStep === 3 ? "text-emerald-800 font-extrabold" : "text-slate-500"}>
                Sequential 40m Plans
              </span>
            </div>
          </div>

          {/* WIZARD STEP 1: PARAMETERS FORM */}
          {wizardStep === 1 && (
            <form onSubmit={handleDiscoverOptions} className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
              <div className="border-b pb-3">
                <h3 className="text-base font-extrabold text-slate-800">
                  Step 1: Input Class Constraints & Competency Level
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  The AI will inspect official NIE syllabus guidelines and recommend 3 tailored student-centered activities.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">Grade Level</label>
                  <select
                    value={wizardGrade}
                    onChange={(e) => setWizardGrade(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  >
                    <option value="Grade 6">Grade 6</option>
                    <option value="Grade 7">Grade 7</option>
                    <option value="Grade 8">Grade 8</option>
                    <option value="Grade 9">Grade 9</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">Subject</label>
                  <select
                    value={wizardSubject}
                    onChange={(e) => setWizardSubject(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  >
                    <option value="Civic Education">Civic Education</option>
                    <option value="Science">Science</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">Competency Level Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 8.1.1, 8.2.2, 8.4.4"
                    value={wizardCompetency}
                    onChange={(e) => setWizardCompetency(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs font-mono font-bold focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">
                    Class Size (Number of Students)
                  </label>
                  <input
                    type="number"
                    min={5}
                    max={80}
                    required
                    value={wizardStudentCount}
                    onChange={(e) => setWizardStudentCount(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs font-bold focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                  <span className="text-[11px] text-slate-400">Class logistics & task cards scale to this count.</span>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">
                    Number of Periods (40 mins each)
                  </label>
                  <select
                    value={wizardPeriods}
                    onChange={(e) => setWizardPeriods(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs font-bold focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  >
                    <option value={1}>1 Period (40 Minutes)</option>
                    <option value={2}>2 Periods (80 Minutes Sequential)</option>
                    <option value={3}>3 Periods (120 Minutes Sequential)</option>
                    <option value={4}>4 Periods (160 Minutes Sequential)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">Topic Query (Optional focus)</label>
                  <input
                    type="text"
                    placeholder="e.g. Public services, Democratic councils"
                    value={wizardTopicQuery}
                    onChange={(e) => setWizardTopicQuery(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t">
                <button
                  type="submit"
                  disabled={isLoadingOptions}
                  className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all shadow-sm hover:shadow disabled:opacity-50"
                >
                  {isLoadingOptions ? "🔎 Querying Syllabus Guidelines..." : "Discover Pedagogical Activities →"}
                </button>
              </div>
            </form>
          )}

          {/* WIZARD STEP 2: CHOOSE ACTIVITY THEME (MODULAR COMPONENT) */}
          {wizardStep === 2 && (
            <ActivitySelectionStep
              activityOptions={activityOptions}
              selectedOptionId={selectedOptionId}
              setSelectedOptionId={setSelectedOptionId}
              customStrategy={customStrategy}
              setCustomStrategy={setCustomStrategy}
              discoveredTopic={discoveredTopic}
              studentCount={wizardStudentCount}
              periods={wizardPeriods}
              isLoading={isLoading}
              onBack={() => setWizardStep(1)}
              onProceed={handleGenerateWizardPlans}
            />
          )}

          {/* WIZARD STEP 3: MULTI-PERIOD TABBED / ACCORDION VIEWER */}
          {wizardStep === 3 && multiPeriodPlans.length > 0 && (
            <MultiPeriodPlanViewer
              plans={multiPeriodPlans}
              studentCount={wizardStudentCount}
              onNewPlan={() => setWizardStep(1)}
              onEditPlan={(chosenPlan) => {
                setPlanData((prev) =>
                  prev ? { ...prev, lesson_plan: chosenPlan as any } : null
                );
                setActiveMainTab("generator");
                setActiveViewTab("editor");
              }}
            />
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* VIEW B (NEW): MULTI-PERIOD PLANNER (STEP 9 STATE MACHINE PIPELINE)        */}
      {/* ========================================================================= */}
      {activeMainTab === "planner" && (
        <div className="space-y-6 max-w-[860px] mx-auto">
          {/* Progress Indicator for Step 9 */}
          <div className="flex items-center justify-between bg-white px-5 py-3 rounded-xl border border-slate-200 text-xs font-bold shadow-sm">
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${multiPeriodStep === 1 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                1
              </span>
              <span className={multiPeriodStep === 1 ? "text-emerald-800 font-extrabold" : "text-slate-500"}>
                Class & Curriculum Inputs
              </span>
            </div>
            <span className="text-slate-300">→</span>
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${multiPeriodStep === 2 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                2
              </span>
              <span className={multiPeriodStep === 2 ? "text-emerald-800 font-extrabold" : "text-slate-500"}>
                Period-Aware Options / Mode B
              </span>
            </div>
            <span className="text-slate-300">→</span>
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${multiPeriodStep === 3 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                3
              </span>
              <span className={multiPeriodStep === 3 ? "text-emerald-800 font-extrabold" : "text-slate-500"}>
                40m Plan Viewer & Next Period
              </span>
            </div>
            {multiPeriodStep > 1 && (
              <button
                type="button"
                onClick={resetMultiPeriodPlanner}
                className="text-xs text-rose-600 hover:underline font-semibold ml-4"
              >
                Reset
              </button>
            )}
          </div>

          {/* Step 9 Sub-Views rendered dynamically without SSR build conflicts */}
          {multiPeriodStep === 1 && <Step1Inputs />}
          {multiPeriodStep === 2 && <Step2OptionsSelection />}
          {multiPeriodStep === 3 && <Step3PlanViewer />}
        </div>
      )}

      {/* ========================================================================= */}
      {/* VIEW C: GENERATED PLANS LIBRARY (STORAGE REPOSITORY)                      */}
      {/* ========================================================================= */}
      {activeMainTab === "library" && (
        <div className="max-w-[860px] mx-auto">
          <GeneratedPlansLibrary onPlanLoadedToViewer={handleLoadPlanToViewer} />
        </div>
      )}

      {/* ========================================================================= */}
      {/* VIEW D: CLASSIC LESSON PLAN GENERATOR (DIRECT FORM ENTRY)                 */}
      {/* ========================================================================= */}
      {activeMainTab === "generator" && (
        <div className="space-y-4">
          <LessonPlanForm
            onSubmit={handleClassicFormSubmit}
            onViewPlan={handleViewPlan}
            isLoading={isLoading}
            isViewing={isViewing}
          />

          <div style={{ marginTop: "24px" }}>
            {isLoading ? (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  padding: "40px 24px",
                  borderRadius: "16px",
                  border: "1.5px solid #818cf8",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  textAlign: "center",
                  gap: "16px",
                  maxWidth: "860px",
                  margin: "0 auto",
                  width: "100%",
                }}
              >
                <div
                  style={{
                    width: "60px",
                    height: "60px",
                    borderRadius: "50%",
                    backgroundColor: "#eef2ff",
                    border: "2px solid #c7d2fe",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "28px",
                  }}
                >
                  <span className="animate-spin inline-block">⏳</span>
                </div>
                <div>
                  <h4 style={{ fontSize: "18px", fontWeight: "800", color: "#1e1b4b", margin: "0 0 6px 0" }}>
                    Generating Lesson Plan...
                  </h4>
                  <p style={{ fontSize: "13px", color: "#64748b", maxWidth: "480px", margin: "0 auto", lineHeight: "1.5" }}>
                    Retrieving official NIE curriculum guidelines, constructing student-centered activities, and auto-balancing
                    the 40-minute structure.
                  </p>
                </div>
              </div>
            ) : generationMode === "stream" && (streamedText || isLoading) ? (
              <div
                style={{
                  backgroundColor: "#0f172a",
                  padding: "24px",
                  borderRadius: "16px",
                  border: "1px solid #1e293b",
                  maxWidth: "860px",
                  margin: "0 auto",
                  width: "100%",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #334155", paddingBottom: "12px", marginBottom: "16px" }}>
                  <span style={{ fontSize: "13px", fontWeight: "800", color: "#38bdf8" }}>
                    ⚡ Real-Time Lesson Plan Stream
                  </span>
                  <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#94a3b8" }}>
                    Ollama Streaming Output
                  </span>
                </div>
                <div className="text-emerald-400 font-mono text-xs sm:text-sm leading-relaxed whitespace-pre-wrap min-h-56">
                  {streamedText}
                  {isLoading && <span className="animate-pulse inline-block w-2 h-4 bg-emerald-400 ml-1">▌</span>}
                </div>
              </div>
            ) : planData ? (
              <div style={{ maxWidth: "860px", margin: "0 auto", width: "100%", display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 4px", marginBottom: "16px" }}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab("viewer")}
                      style={{
                        padding: "7px 16px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        border: "none",
                        backgroundColor: activeViewTab === "viewer" ? "#4f46e5" : "#e2e8f0",
                        color: activeViewTab === "viewer" ? "#ffffff" : "#334155",
                      }}
                    >
                      📄 Table Viewer
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab("editor")}
                      style={{
                        padding: "7px 16px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        border: "none",
                        backgroundColor: activeViewTab === "editor" ? "#4f46e5" : "#e2e8f0",
                        color: activeViewTab === "editor" ? "#ffffff" : "#334155",
                      }}
                    >
                      ✏️ Structural Editor
                    </button>
                  </div>
                  <span style={{ fontSize: "11px", color: "#64748b", fontWeight: "600" }}>
                    LEARN Practice Teaching Layout
                  </span>
                </div>

                {activeViewTab === "viewer" && (
                  <>
                    <LessonPlanViewer
                      plan={planData.lesson_plan}
                      factCheck={planData.fact_check_report}
                      alignment={planData.alignment_report}
                      filename={currentPlanFilename || undefined}
                      onEditInGenerator={() => setActiveViewTab("editor")}
                      onDeletePlan={currentPlanFilename ? () => setIsDeleteModalOpen(true) : undefined}
                    />

                    <DeleteConfirmModal
                      isOpen={isDeleteModalOpen}
                      filename={currentPlanFilename || ""}
                      planTitle={planData?.lesson_plan?.lesson || planData?.lesson_plan?.competence || ""}
                      grade={planData?.lesson_plan?.grade}
                      subject={planData?.lesson_plan?.subject}
                      competenceLevel={planData?.lesson_plan?.competence_level}
                      timeAllocation={planData?.lesson_plan?.time_allocation}
                      isDeleting={isDeleting}
                      onConfirm={handleDeleteCurrentPlan}
                      onCancel={() => setIsDeleteModalOpen(false)}
                    />
                  </>
                )}

                {activeViewTab === "editor" && (
                  <StructuralEditor
                    initialPlan={planData.lesson_plan as any}
                    filename={currentPlanFilename || undefined}
                    onSave={(updated) => {
                      setPlanData((prev) => (prev ? { ...prev, lesson_plan: updated as any } : null));
                      setNotificationMessage("Updated lesson plan saved successfully!");
                      setTimeout(() => setNotificationMessage(null), 3000);
                    }}
                  />
                )}
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  padding: "36px 24px",
                  borderRadius: "16px",
                  border: "1.5px dashed #cbd5e1",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  textAlign: "center",
                  gap: "12px",
                  maxWidth: "860px",
                  margin: "0 auto",
                  width: "100%",
                }}
              >
                <div
                  style={{
                    width: "54px",
                    height: "54px",
                    borderRadius: "50%",
                    backgroundColor: "#eef2ff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "26px",
                    color: "#4f46e5",
                  }}
                >
                  📄
                </div>
                <div>
                  <h4 style={{ fontSize: "16px", fontWeight: "800", color: "#0f172a", margin: "0 0 4px 0" }}>
                    See Lesson Plan
                  </h4>
                  <p style={{ fontSize: "13px", color: "#64748b", maxWidth: "480px", margin: "0 auto", lineHeight: "1.5" }}>
                    Use the <strong>"2-Step Activity Wizard"</strong> or <strong>"Multi-Period Planner"</strong> above to pick interactive activities, or configure
                    parameters manually in the Classic Generator.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}