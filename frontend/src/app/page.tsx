"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getStoredAuth, getCurrentUserApi, clearStoredAuth, UserDto } from "@/services/authApi";

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
  generateLessonPlan,
  LessonPlanResponse,
  LessonPlanPayload,
  LessonPlanDto,
} from "@/services/lessonPlanApi";
import {
  PedagogicalActivityOption,
  PedagogicalOptionsResponse,
  LessonPlanSchemaDto,
} from "@/types/lessonPlan";

const API_BASE_URL =
  typeof window !== "undefined" && window.location.hostname
    ? `http://${window.location.hostname}:8000`
    : process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<UserDto | null>(null);
  const [authStatus, setAuthStatus] = useState<"checking" | "authenticated" | "unauthenticated" | "error">("checking");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authRetry, setAuthRetry] = useState(0);

  useEffect(() => {
    let active = true;
    const { token } = getStoredAuth();

    if (!token) {
      setAuthStatus("unauthenticated");
      router.replace("/login");
      return () => {
        active = false;
      };
    }

    getCurrentUserApi()
      .then((user) => {
        if (active) {
          setCurrentUser(user);
          setAuthStatus("authenticated");
          setAuthError(null);
        }
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (!getStoredAuth().token) {
          setAuthStatus("unauthenticated");
          router.replace("/login");
          return;
        }
        setAuthError(err instanceof Error ? err.message : "Could not verify your account.");
        setAuthStatus("error");
      });

    return () => {
      active = false;
    };
  }, [authRetry, router]);

  const handleLogout = () => {
    clearStoredAuth();
    setCurrentUser(null);
    setAuthStatus("unauthenticated");
    window.location.href = "/login";
  };

  // Main Navigation Tabs: 'wizard' (Existing Wizard), 'planner' (New Step 9 State Machine), 'generator' (Classic Direct), 'library' (Saved Plans)
  const [activeMainTab, setActiveMainTab] = useState<"wizard" | "planner" | "generator" | "library">("planner");

  // Step 9 Multi-Period Zustand State
  const {
    step: multiPeriodStep,
    resetAll: resetMultiPeriodPlanner,
    goToStep,
    goToChooseActivity,
    viewPeriodPlan,
    currentPeriod,
    optionsByPeriod,
    currentOptions,
    generatedPlans,
    apiKey,
    llmProvider,
    setApiKey,
    setLlmProvider,
  } = useLessonPlanStore();

  const [isAiSettingsOpen, setIsAiSettingsOpen] = useState(false);
  const [tempApiKey, setTempApiKey] = useState(apiKey || "");
  const [showKeyText, setShowKeyText] = useState(false);

  // Sync tempApiKey when modal opens or apiKey changes
  React.useEffect(() => {
    setTempApiKey(apiKey || "");
  }, [apiKey]);

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
  const [activityOptionsByPeriod, setActivityOptionsByPeriod] = useState<
    Record<number, PedagogicalActivityOption[]>
  >({});
  const [selectedOptionIdsByPeriod, setSelectedOptionIdsByPeriod] = useState<
    Record<number, string>
  >({});
  const [customStrategiesByPeriod, setCustomStrategiesByPeriod] = useState<
    Record<number, string>
  >({});
  const [wizardCurrentPeriod, setWizardCurrentPeriod] = useState(1);
  const [wizardGenerationProgress, setWizardGenerationProgress] = useState("");

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
      const targetP = wizardCurrentPeriod || 1;
      const res = await fetch(`${API_BASE_URL}/api/v1/suggest-pedagogical-options`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          competency_level: wizardCompetency.trim(),
          grade_level: wizardGrade,
          subject: wizardSubject,
          student_count: Number(wizardStudentCount),
          periods: Number(wizardPeriods),
          requested_period: targetP,
          topic_query: wizardTopicQuery.trim(),
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Activity discovery failed with status: ${res.status}`
        );
      }

      const data: PedagogicalOptionsResponse = await res.json();
      if (!Array.isArray(data.options) || data.options.length !== 3) {
        throw new Error(`Activity discovery did not return exactly three options for Period ${targetP}.`);
      }
      setDiscoveredTopic(data.lesson_topic);
      setActivityOptionsByPeriod({ [targetP]: data.options });
      setSelectedOptionIdsByPeriod({ [targetP]: data.options[0].id });
      setCustomStrategiesByPeriod({});
      setWizardCurrentPeriod(targetP);
      setWizardGenerationProgress("");
      setMultiPeriodPlans([]);
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

    try {
      const currentPeriod = wizardCurrentPeriod;
      const customActivity = (customStrategiesByPeriod[currentPeriod] || "").trim();
      const selectedOption = (activityOptionsByPeriod[currentPeriod] || []).find(
        (option) => option.id === selectedOptionIdsByPeriod[currentPeriod]
      );

      if (!customActivity && !selectedOption) {
        throw new Error(`Choose an activity for Period ${currentPeriod} before generating its plan.`);
      }

      let nextPeriodOptions: PedagogicalActivityOption[] = [];
      if (currentPeriod < wizardPeriods) {
        const nextPeriod = currentPeriod + 1;
        setWizardGenerationProgress(`Preparing distinct activity options for Period ${nextPeriod}...`);
        const optionsResponse = await fetch(
          `${API_BASE_URL}/api/v1/suggest-pedagogical-options`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              competency_level: wizardCompetency.trim(),
              grade_level: wizardGrade,
              subject: wizardSubject,
              student_count: Number(wizardStudentCount),
              periods: Number(wizardPeriods),
              requested_period: nextPeriod,
              topic_query: wizardTopicQuery.trim(),
              previous_period_activities: [
                ...Array.from({ length: currentPeriod }, (_, index) => {
                  const period = index + 1;
                  const custom = (customStrategiesByPeriod[period] || "").trim();
                  if (custom) return `Period ${period}: ${custom}`;
                  const option = (activityOptionsByPeriod[period] || []).find(
                    (candidate) => candidate.id === selectedOptionIdsByPeriod[period]
                  );
                  return option ? `Period ${period}: ${option.title}` : "";
                }).filter(Boolean),
              ],
            }),
          }
        );

        if (!optionsResponse.ok) {
          const errorData = await optionsResponse.json().catch(() => ({}));
          throw new Error(
            errorData.detail ||
              `Activity discovery failed for Period ${nextPeriod} (Status ${optionsResponse.status})`
          );
        }

        const optionsData: PedagogicalOptionsResponse = await optionsResponse.json();
        if (!Array.isArray(optionsData.options) || optionsData.options.length !== 3) {
          throw new Error(
            `Activity discovery did not return exactly three options for Period ${nextPeriod}.`
          );
        }
        nextPeriodOptions = optionsData.options;
      }

      setWizardGenerationProgress(`Generating the Period ${currentPeriod} lesson plan...`);
      const chosenDescription = selectedOption
        ? [
            `Activity: ${selectedOption.title}`,
            `Approach: ${selectedOption.description}`,
            `Student task: ${selectedOption.student_action_summary || selectedOption.description}`,
            `Teacher facilitation: ${selectedOption.teacher_facilitation_summary || "Facilitate student participation and outcome-focused discussion."}`,
            `Expected output: ${selectedOption.expected_student_output || "A student-created response demonstrating the allocated learning outcomes."}`,
            `Grouping: ${selectedOption.student_grouping}`,
          ].join("\n")
        : undefined;
      const previousActivities = Array.from(
        { length: currentPeriod - 1 },
        (_, index) => {
          const period = index + 1;
          const custom = (customStrategiesByPeriod[period] || "").trim();
          if (custom) return `Period ${period}: ${custom}`;
          const option = (activityOptionsByPeriod[period] || []).find(
            (candidate) => candidate.id === selectedOptionIdsByPeriod[period]
          );
          return option ? `Period ${period}: ${option.title}` : "";
        }
      ).filter(Boolean);

      const data = await generateLessonPlan({
        competencyLevel: wizardCompetency.trim(),
        topicQuery: wizardTopicQuery.trim() || discoveredTopic,
        gradeLevel: wizardGrade,
        subject: wizardSubject,
        periods: Number(wizardPeriods),
        requestedPeriod: currentPeriod,
        singlePeriodOnly: true,
        studentCount: Number(wizardStudentCount),
        teacherMode: customActivity ? "own_approach" : "suggested",
        selectedActivityOption: customActivity ? undefined : chosenDescription,
        selectedActivityTitle: customActivity
          ? `Teacher approach: ${customActivity}`
          : selectedOption?.title,
        customTeacherActivity: customActivity || undefined,
        activityOptions: activityOptionsByPeriod[currentPeriod] || [],
        previousPeriodActivities: previousActivities,
      });

      const generatedPlan: LessonPlanSchemaDto = {
        ...data.lesson_plan,
        period_number: currentPeriod,
        total_periods: wizardPeriods,
        post_activity: data.lesson_plan.post_activity || "",
        information_sources: data.lesson_plan.information_sources || [],
        attachments: data.lesson_plan.attachments || [],
      };
      const updatedPlans = [
        ...multiPeriodPlans.filter(
          (plan) => (plan.period_number || 1) !== currentPeriod
        ),
        generatedPlan,
      ].sort((left, right) => (left.period_number || 1) - (right.period_number || 1));
      setMultiPeriodPlans(updatedPlans);

      setPlanData({
        competency_level: data.competency_level,
        grade_level: data.grade_level,
        subject: data.subject,
        lesson_plan: generatedPlan,
        fact_check_report: data.fact_check_report || null,
        alignment_report: data.alignment_report || null,
      });
      setCurrentPlanFilename(null);

      if (nextPeriodOptions.length === 3 && currentPeriod < wizardPeriods) {
        const nextPeriod = currentPeriod + 1;
        setActivityOptionsByPeriod((previous) => ({
          ...previous,
          [nextPeriod]: nextPeriodOptions,
        }));
        setSelectedOptionIdsByPeriod((previous) => ({
          ...previous,
          [nextPeriod]: nextPeriodOptions[0].id,
        }));
        setWizardCurrentPeriod(nextPeriod);
        setWizardGenerationProgress("");
      } else {
        setWizardStep(3);
        setWizardGenerationProgress("");
        setNotificationMessage(
          `Successfully generated ${updatedPlans.length} period-specific lesson plan(s).`
        );
      }
    } catch (err: any) {
      setError(err.message || "Failed to generate sequential lesson plans.");
      setWizardGenerationProgress("");
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

      const periodPlans =
        Array.isArray((result as any).all_period_plans) && (result as any).all_period_plans.length > 0
          ? (result as any).all_period_plans
          : [result.plan];

      setPlanData({
        competency_level: result.plan.competence_level,
        grade_level: result.plan.grade,
        subject: result.plan.subject,
        lesson_plan: result.plan,
        lesson_plans: periodPlans,
        fact_check_report: null,
        alignment_report: null,
      });
      setMultiPeriodPlans(periodPlans as any);
      setCurrentPlanFilename(result.filename);
      setGenerationMode("standard");
      setActiveViewTab("viewer");
      setNotificationMessage(
        periodPlans.length > 1
          ? `Showing ${periodPlans.length} saved period plans for Competency Level ${formData.competencyLevel}`
          : `Showing saved lesson plan for Competency Level ${formData.competencyLevel} (${result.filename})`
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
      const plans =
        Array.isArray(result.lesson_plans) && result.lesson_plans.length > 0
          ? result.lesson_plans
          : [result.lesson_plan as any];
      setMultiPeriodPlans(plans as any);
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

  if (authStatus !== "authenticated") {
    return (
      <main
        style={{
          minHeight: "100vh",
          backgroundColor: "#eef2f7",
          backgroundImage: "radial-gradient(circle at 50% 20%, #ffffff 0%, #eef2f7 75%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px 16px",
          fontFamily:
            "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "500px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          {/* Header Tag Badge */}
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
              marginBottom: "14px",
            }}
          >
            LEARN Kandy Practice Teaching Pedagogy
          </span>

          {/* Main Box - Styled matching Lesson Plan Generator / Login Box */}
          <section
            style={{
              backgroundColor: "#ffffff",
              padding: "32px 28px",
              borderRadius: "16px",
              border: "1px solid #e2e8f0",
              boxShadow:
                "0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04)",
              width: "100%",
              boxSizing: "border-box",
              display: "flex",
              flexDirection: "column",
              gap: "20px",
            }}
          >
            {/* Box Header */}
            <div
              style={{
                borderBottom: "1px solid #f1f5f9",
                paddingBottom: "16px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <span
                style={{
                  backgroundColor: "#eef2ff",
                  color: "#4f46e5",
                  padding: "10px",
                  borderRadius: "12px",
                  fontSize: "22px",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                🔐
              </span>
              <div>
                <h1
                  style={{
                    fontSize: "20px",
                    fontWeight: "800",
                    color: "#0f172a",
                    margin: 0,
                    letterSpacing: "-0.01em",
                  }}
                >
                  Civic Education AI Planner
                </h1>
                <p
                  style={{
                    fontSize: "13px",
                    color: "#64748b",
                    margin: "4px 0 0 0",
                  }}
                >
                  Multi-Period Lesson Plan Generator
                </p>
              </div>
            </div>

            {/* Inner Status Box based on auth state */}
            {authStatus === "checking" ? (
              <div
                style={{
                  backgroundColor: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "12px",
                  padding: "24px 16px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  textAlign: "center",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    border: "3px solid #e2e8f0",
                    borderTopColor: "#4f46e5",
                    borderRadius: "50%",
                    animation: "authSpin 0.8s linear infinite",
                  }}
                />
                <style>{`@keyframes authSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                <div>
                  <h3
                    style={{
                      fontSize: "15px",
                      fontWeight: "700",
                      color: "#1e293b",
                      margin: "0 0 4px 0",
                    }}
                  >
                    Verifying your session…
                  </h3>
                  <p
                    style={{
                      fontSize: "13px",
                      color: "#64748b",
                      margin: 0,
                    }}
                  >
                    Checking authentication credentials and permissions.
                  </p>
                </div>
              </div>
            ) : authStatus === "unauthenticated" ? (
              <div
                style={{
                  backgroundColor: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "12px",
                  padding: "20px 16px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  textAlign: "center",
                  gap: "8px",
                }}
              >
                <span style={{ fontSize: "24px" }}>👋</span>
                <h3
                  style={{
                    fontSize: "15px",
                    fontWeight: "700",
                    color: "#1e293b",
                    margin: 0,
                  }}
                >
                  Sign In Required
                </h3>
                <p
                  style={{
                    fontSize: "13px",
                    color: "#64748b",
                    margin: 0,
                  }}
                >
                  Please sign in to access and generate curriculum lesson plans.
                </p>
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: "12px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "16px" }}>⚠️</span>
                  <span
                    style={{
                      fontSize: "13px",
                      fontWeight: "700",
                      color: "#b91c1c",
                    }}
                  >
                    Authentication Notice
                  </span>
                </div>
                <p
                  style={{
                    fontSize: "13px",
                    color: "#991b1b",
                    margin: 0,
                    lineHeight: "1.4",
                  }}
                >
                  {authError || "Your session could not be verified or has expired. Please sign in again."}
                </p>
                <div style={{ display: "flex", gap: "10px", marginTop: "6px" }}>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthStatus("checking");
                      setAuthRetry((attempt) => attempt + 1);
                    }}
                    style={{
                      padding: "8px 14px",
                      borderRadius: "8px",
                      backgroundColor: "#ffffff",
                      border: "1px solid #cbd5e1",
                      fontSize: "12px",
                      fontWeight: "700",
                      color: "#334155",
                      cursor: "pointer",
                    }}
                  >
                    🔄 Retry Check
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}
            >
              <Link
                href="/login"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  padding: "12px 18px",
                  borderRadius: "10px",
                  backgroundColor: "#4f46e5",
                  color: "#ffffff",
                  fontSize: "14px",
                  fontWeight: "700",
                  textDecoration: "none",
                  boxShadow: "0 4px 10px rgba(79, 70, 229, 0.25)",
                  transition: "background-color 0.15s ease",
                }}
              >
                <span>🔐</span>
                <span>Sign In to Your Account</span>
                <span>→</span>
              </Link>
            </div>

            {/* Footer / Alternate Link */}
            <div
              style={{
                borderTop: "1px solid #f1f5f9",
                paddingTop: "14px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: "12px",
                color: "#64748b",
              }}
            >
              <span>Need an account?</span>
              <Link
                href="/signup"
                style={{
                  color: "#4f46e5",
                  fontWeight: "700",
                  textDecoration: "none",
                }}
              >
                Create Account →
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-8 px-4 sm:px-8 max-w-5xl mx-auto font-sans">
      {/* Top Utility Bar with Authentication Status */}
      <div
        style={{
          maxWidth: "860px",
          margin: "0 auto 16px auto",
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          gap: "10px",
          width: "100%",
        }}
      >
        {currentUser ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              backgroundColor: "#ffffff",
              padding: "6px 14px",
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 2px 4px rgba(0,0,0,0.03)",
              fontSize: "13px",
            }}
          >
            <span style={{ color: "#334155", fontWeight: "600" }}>
              👤 Logged in as <strong style={{ color: "#4f46e5" }}>{currentUser.username}</strong>
            </span>
            <button
              type="button"
              onClick={handleLogout}
              style={{
                background: "none",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                padding: "3px 8px",
                fontSize: "11px",
                fontWeight: "700",
                color: "#64748b",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#dc2626";
                e.currentTarget.style.borderColor = "#fca5a5";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "#64748b";
                e.currentTarget.style.borderColor = "#cbd5e1";
              }}
            >
              Sign Out
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Link
              href="/login"
              style={{
                textDecoration: "none",
                fontSize: "12px",
                fontWeight: "700",
                color: "#4f46e5",
                backgroundColor: "#ffffff",
                border: "1px solid #c7d2fe",
                padding: "6px 14px",
                borderRadius: "8px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
              }}
            >
              <span>🔐</span>
              <span>Log In</span>
            </Link>
            <Link
              href="/signup"
              style={{
                textDecoration: "none",
                fontSize: "12px",
                fontWeight: "700",
                color: "#ffffff",
                backgroundColor: "#4f46e5",
                border: "1px solid #4338ca",
                padding: "6px 14px",
                borderRadius: "8px",
                boxShadow: "0 2px 4px rgba(79, 70, 229, 0.2)",
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
              }}
            >
              <span>👤</span>
              <span>Sign Up</span>
            </Link>
          </div>
        )}
      </div>

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
          {/* Civic Education multi-period planner */}
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
            <span>Multi-Period Lesson Planner</span>
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
              <span className={`px-2.5 py-1 rounded-full ${wizardStep === 1 ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                1
              </span>
              <span className={wizardStep === 1 ? "text-blue-800 font-extrabold" : "text-slate-500"}>
                Class & Curriculum
              </span>
            </div>
            <span className="text-slate-300">→</span>
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${wizardStep === 2 ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                2
              </span>
              <span className={wizardStep === 2 ? "text-blue-800 font-extrabold" : "text-slate-500"}>
                Activity Strategy
              </span>
            </div>
            <span className="text-slate-300">→</span>
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded-full ${wizardStep === 3 ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                3
              </span>
              <span className={wizardStep === 3 ? "text-blue-800 font-extrabold" : "text-slate-500"}>
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
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs font-mono font-bold focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs font-bold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                  <span className="text-[11px] text-slate-400">Class logistics & task cards scale to this count.</span>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">
                    Number of Periods (40 mins each)
                  </label>
                  <select
                    value={wizardPeriods}
                    onChange={(e) => {
                      const newP = Number(e.target.value);
                      setWizardPeriods(newP);
                      if (wizardCurrentPeriod > newP) {
                        setWizardCurrentPeriod(newP);
                      }
                    }}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs font-bold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value={1}>1 Period (40 Minutes)</option>
                    <option value={2}>2 Periods (80 Minutes Total)</option>
                    <option value={3}>3 Periods (120 Minutes Total)</option>
                    <option value={4}>4 Periods (160 Minutes Total)</option>
                  </select>
                </div>

                {wizardPeriods > 1 && (
                  <div className="col-span-full bg-blue-50/70 border border-blue-200 rounded-xl p-3">
                    <label className="block text-[11px] font-bold text-blue-900 uppercase tracking-wide mb-1.5">
                      Select Period to Plan (Skip previous periods if desired):
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {Array.from({ length: wizardPeriods }, (_, i) => i + 1).map((pNum) => {
                        const isSelected = wizardCurrentPeriod === pNum;
                        return (
                          <button
                            key={pNum}
                            type="button"
                            onClick={() => setWizardCurrentPeriod(pNum)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                              isSelected
                                ? "bg-blue-600 text-white shadow-xs"
                                : "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
                            }`}
                          >
                            Period {pNum}
                          </button>
                        );
                      })}
                    </div>
                    <span className="block text-[10px] text-blue-700 mt-1">
                      You can generate any period directly. Outcomes are divided equally according to curriculum priority.
                    </span>
                  </div>
                )}

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wide mb-1">Topic Query (Optional focus)</label>
                  <input
                    type="text"
                    placeholder="e.g. Public services, Democratic councils"
                    value={wizardTopicQuery}
                    onChange={(e) => setWizardTopicQuery(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t">
                <button
                  type="submit"
                  disabled={isLoadingOptions}
                  className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition-all shadow-sm hover:shadow disabled:opacity-50"
                >
                  {isLoadingOptions ? "🔎 Querying Syllabus Guidelines..." : "Discover Pedagogical Activities →"}
                </button>
              </div>
            </form>
          )}

          {/* WIZARD STEP 2: CHOOSE ACTIVITY THEME (MODULAR COMPONENT) */}
          {wizardStep === 2 && (
            <ActivitySelectionStep
              activityOptions={activityOptionsByPeriod[wizardCurrentPeriod] || []}
              selectedOptionId={selectedOptionIdsByPeriod[wizardCurrentPeriod] || ""}
              setSelectedOptionId={(id) =>
                setSelectedOptionIdsByPeriod((previous) => ({
                  ...previous,
                  [wizardCurrentPeriod]: id,
                }))
              }
              customStrategy={customStrategiesByPeriod[wizardCurrentPeriod] || ""}
              setCustomStrategy={(value) =>
                setCustomStrategiesByPeriod((previous) => ({
                  ...previous,
                  [wizardCurrentPeriod]: value,
                }))
              }
              discoveredTopic={discoveredTopic}
              studentCount={wizardStudentCount}
              periods={wizardPeriods}
              currentPeriod={wizardCurrentPeriod}
              completedPeriods={multiPeriodPlans.length}
              isLoading={isLoading}
              progressMessage={wizardGenerationProgress}
              errorMessage={error}
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
        <div className="mx-auto w-full max-w-[860px]">
          <section
            style={{
              backgroundColor: '#ffffff',
              padding: '24px',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              width: '100%',
              boxSizing: 'border-box',
            }}
          >
            <header style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '12px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
              <div>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0, color: '#0f172a', fontSize: '16px', fontWeight: 800 }}>
                  <span aria-hidden="true">✨</span>
                  <span>Lesson Plan Generator</span>
                </h2>
                <p style={{ margin: '2px 0 0', color: '#64748b', fontSize: '12px' }}>
                  Configure curriculum parameters to generate an NIE &amp; LEARN aligned lesson plan
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setIsAiSettingsOpen(true)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    backgroundColor: '#ffffff',
                    fontSize: '12px',
                    fontWeight: 700,
                    color: '#334155',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                  }}
                  title="Configure LLM Provider & API Key"
                >
                  <span>⚙️</span>
                  <span>AI Model &amp; Key</span>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 800,
                      padding: '2px 6px',
                      borderRadius: '9999px',
                      backgroundColor: llmProvider === 'ollama' ? '#f1f5f9' : '#e0e7ff',
                      color: llmProvider === 'ollama' ? '#475569' : '#3730a3',
                    }}
                  >
                    {llmProvider === 'openai' ? 'OpenAI' : llmProvider === 'gemini' ? 'Gemini' : llmProvider === 'ollama' ? 'Ollama' : apiKey ? 'Cloud API' : 'Auto'}
                  </span>
                </button>

                {multiPeriodStep > 1 && (
                  <button
                    type="button"
                    onClick={resetMultiPeriodPlanner}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      backgroundColor: '#ffffff',
                      fontSize: '12px',
                      fontWeight: 700,
                      color: '#475569',
                      cursor: 'pointer',
                    }}
                  >
                    Reset
                  </button>
                )}
              </div>
            </header>

            <nav aria-label="Lesson plan progress" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {[
                { number: 1, title: "Lesson Details" },
                { number: 2, title: "Choose Activity" },
                { number: 3, title: "Generated Plan" },
              ].map((step) => {
                const current = multiPeriodStep === step.number;
                const complete = multiPeriodStep > step.number;
                const canClick =
                  step.number === 1 ||
                  (step.number === 2 && (currentOptions.length > 0 || (optionsByPeriod[currentPeriod]?.length ?? 0) > 0)) ||
                  (step.number === 3 && (!!generatedPlans[currentPeriod] || Object.keys(generatedPlans).length > 0));

                const handleStepClick = () => {
                  if (step.number === 1) {
                    goToStep(1);
                  } else if (step.number === 2 && canClick) {
                    goToChooseActivity(currentPeriod);
                  } else if (step.number === 3 && canClick) {
                    const targetP = generatedPlans[currentPeriod] ? currentPeriod : Number(Object.keys(generatedPlans)[0]);
                    viewPeriodPlan(targetP);
                  }
                };

                return (
                  <button
                    key={step.number}
                    type="button"
                    disabled={!canClick}
                    onClick={handleStepClick}
                    aria-current={current ? "step" : undefined}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      borderRadius: '8px',
                      border: current ? '1.5px solid #6366f1' : complete ? '1px solid #cbd5e1' : '1px solid #f1f5f9',
                      backgroundColor: current ? '#eef2ff' : complete ? '#ffffff' : '#f8fafc',
                      padding: '8px 10px',
                      cursor: canClick ? 'pointer' : 'default',
                      textAlign: 'left',
                      transition: 'all 0.15s ease',
                      boxShadow: current ? '0 2px 4px rgba(99, 102, 241, 0.15)' : 'none',
                    }}
                  >
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        fontSize: '10px',
                        fontWeight: 800,
                        backgroundColor: current || complete ? '#4f46e5' : '#e2e8f0',
                        color: current || complete ? '#ffffff' : '#64748b',
                        flexShrink: 0,
                      }}
                    >
                      {complete ? "✓" : step.number}
                    </span>
                    <span
                      style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        color: current ? '#312e81' : complete ? '#334155' : '#94a3b8',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {step.title}
                    </span>
                  </button>
                );
              })}
            </nav>

            {multiPeriodStep === 1 && <Step1Inputs />}
            {multiPeriodStep === 2 && <Step2OptionsSelection />}
            {multiPeriodStep === 3 && <Step3PlanViewer />}
          </section>

          {/* AI Model & API Key Configuration Modal */}
          {isAiSettingsOpen && (
            <div
              role="dialog"
              aria-modal="true"
              style={{
                position: "fixed",
                inset: 0,
                backgroundColor: "rgba(15, 23, 42, 0.6)",
                backdropFilter: "blur(4px)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 9999,
                padding: "16px",
              }}
            >
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "16px",
                  padding: "24px",
                  width: "100%",
                  maxWidth: "520px",
                  boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                  border: "1px solid #e2e8f0",
                  display: "flex",
                  flexDirection: "column",
                  gap: "18px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "20px" }}>⚡</span>
                    <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 800, color: "#0f172a" }}>
                      AI Model &amp; API Key Settings
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsAiSettingsOpen(false)}
                    style={{
                      border: "none",
                      backgroundColor: "transparent",
                      fontSize: "18px",
                      color: "#64748b",
                      cursor: "pointer",
                      padding: "4px 8px",
                    }}
                  >
                    ✕
                  </button>
                </div>

                <p style={{ margin: 0, fontSize: "13px", color: "#64748b", lineHeight: 1.5 }}>
                  Choose your preferred AI execution provider. The project supports both cloud API keys (OpenAI / Google Gemini) and local offline Ollama (llama3).
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>
                    LLM Provider
                  </label>
                  <select
                    value={llmProvider}
                    onChange={(e) => setLlmProvider(e.target.value as any)}
                    style={{
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid #cbd5e1",
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "#1e293b",
                      backgroundColor: "#f8fafc",
                      outline: "none",
                    }}
                  >
                    <option value="auto">Auto (Cloud API if key present, else local Ollama)</option>
                    <option value="openai">OpenAI (GPT-4o-mini)</option>
                    <option value="gemini">Google Gemini (Gemini 1.5 Flash)</option>
                    <option value="ollama">Local Ollama (Llama 3 - Offline)</option>
                  </select>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>
                      API Key (OpenAI or Gemini)
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowKeyText(!showKeyText)}
                      style={{
                        border: "none",
                        backgroundColor: "transparent",
                        fontSize: "11px",
                        fontWeight: 700,
                        color: "#4f46e5",
                        cursor: "pointer",
                      }}
                    >
                      {showKeyText ? "Hide Key" : "Show Key"}
                    </button>
                  </div>
                  <input
                    type={showKeyText ? "text" : "password"}
                    placeholder="sk-proj-... or AIzaSy..."
                    value={tempApiKey}
                    onChange={(e) => setTempApiKey(e.target.value)}
                    style={{
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid #cbd5e1",
                      fontSize: "13px",
                      fontFamily: "monospace",
                      color: "#1e293b",
                      backgroundColor: "#ffffff",
                      outline: "none",
                    }}
                  />
                  <span style={{ fontSize: "11px", color: "#64748b" }}>
                    Keys can also be permanently stored in <code>backend pycharm/.env</code>.
                  </span>
                </div>

                <div
                  style={{
                    backgroundColor: "#eff6ff",
                    border: "1px solid #bfdbfe",
                    borderRadius: "10px",
                    padding: "10px 12px",
                    fontSize: "12px",
                    color: "#1e40af",
                    lineHeight: 1.4,
                  }}
                >
                  💡 <strong>Tip:</strong> If using <strong>Local Ollama</strong>, ensure Ollama is running (<code>ollama run llama3</code>). If using <strong>OpenAI</strong> or <strong>Gemini</strong>, enter your API key above or save in <code>backend pycharm/.env</code>.
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
                  <button
                    type="button"
                    onClick={() => setIsAiSettingsOpen(false)}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "8px",
                      border: "1px solid #cbd5e1",
                      backgroundColor: "#ffffff",
                      fontSize: "13px",
                      fontWeight: 700,
                      color: "#475569",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setApiKey(tempApiKey.trim());
                      setIsAiSettingsOpen(false);
                      setNotificationMessage("AI Model and API Key settings saved successfully!");
                      setTimeout(() => setNotificationMessage(null), 3500);
                    }}
                    style={{
                      padding: "8px 18px",
                      borderRadius: "8px",
                      border: "none",
                      backgroundColor: "#4f46e5",
                      fontSize: "13px",
                      fontWeight: 700,
                      color: "#ffffff",
                      cursor: "pointer",
                      boxShadow: "0 2px 4px rgba(79, 70, 229, 0.25)",
                    }}
                  >
                    Save Settings
                  </button>
                </div>
              </div>
            </div>
          )}
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
                    {multiPeriodPlans && multiPeriodPlans.length > 1 ? (
                      <MultiPeriodPlanViewer
                        plans={multiPeriodPlans}
                        onNewPlan={() => {
                          setPlanData(null);
                          setMultiPeriodPlans([]);
                        }}
                        onEditPlan={(chosenPlan) => {
                          setPlanData((prev) =>
                            prev ? { ...prev, lesson_plan: chosenPlan as any } : null
                          );
                          setActiveViewTab("editor");
                        }}
                      />
                    ) : (
                      <LessonPlanViewer
                        plan={planData.lesson_plan}
                        factCheck={planData.fact_check_report}
                        alignment={planData.alignment_report}
                        filename={currentPlanFilename || undefined}
                        onEditInGenerator={() => setActiveViewTab("editor")}
                        onDeletePlan={currentPlanFilename ? () => setIsDeleteModalOpen(true) : undefined}
                      />
                    )}

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
                    Use the <strong>"Multi-Period Lesson Planner"</strong> above to pick period-specific activities, or configure
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