"use client";

import React, { useState } from "react";
import { LessonPlanSchemaDto } from "@/types/lessonPlan";

interface MultiPeriodPlanViewerProps {
  plans: LessonPlanSchemaDto[];
  studentCount?: number;
  onNewPlan?: () => void;
  onEditPlan?: (plan: LessonPlanSchemaDto) => void;
}

export default function MultiPeriodPlanViewer({
  plans,
  studentCount = 35,
  onNewPlan,
  onEditPlan,
}: MultiPeriodPlanViewerProps) {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [viewMode, setViewMode] = useState<"tabs" | "accordion">("tabs");
  const [openAccordions, setOpenAccordions] = useState<Record<number, boolean>>({ 0: true });

  if (!plans || plans.length === 0) {
    return null;
  }

  const toggleAccordion = (index: number) => {
    setOpenAccordions((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const primaryPlan = plans[0];
  const cleanTitle = primaryPlan.lesson.replace(/\(Period \d+\)/i, "").trim();

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-200">
      {/* Top Meta Bar */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              {primaryPlan.subject} — {primaryPlan.grade}
            </span>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
              Level {primaryPlan.competence_level}
            </span>
          </div>

          <h2 className="text-lg sm:text-xl font-extrabold text-slate-900">
            {cleanTitle}
          </h2>

          <p className="text-xs text-slate-500 mt-0.5">
            Total Allocation: <span className="font-semibold text-slate-700">{plans.length * 40} Minutes</span> ({plans.length} Sequential Periods) | Target Class:{" "}
            <span className="font-semibold text-slate-700">{studentCount} Students</span>
          </p>
        </div>

        {/* Action Buttons & View Mode Switcher */}
        <div className="flex items-center gap-2">
          {plans.length > 1 && (
            <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200 flex text-xs font-bold mr-2">
              <button
                type="button"
                onClick={() => setViewMode("tabs")}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  viewMode === "tabs" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                📑 Tabs
              </button>
              <button
                type="button"
                onClick={() => setViewMode("accordion")}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  viewMode === "accordion" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                🗂️ Accordion
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={() => window.print()}
            className="px-3 py-1.5 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
          >
            🖨️ Print Plans
          </button>

          {onNewPlan && (
            <button
              type="button"
              onClick={onNewPlan}
              className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-xs"
            >
              + New Plan
            </button>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODE 1: HORIZONTAL PERIOD TABS VIEW                                       */}
      {/* ========================================================================= */}
      {viewMode === "tabs" && (
        <div className="space-y-4">
          {plans.length > 1 && (
            <div className="flex border-b border-slate-200 bg-white px-3 pt-2 rounded-t-2xl space-x-2 overflow-x-auto shadow-2xs">
              {plans.map((p, idx) => {
                const isActive = activeTab === idx;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setActiveTab(idx)}
                    className={`py-2.5 px-4 text-xs font-bold border-b-2 whitespace-nowrap transition-all flex items-center gap-2 ${
                      isActive
                        ? "border-emerald-600 text-emerald-800 bg-emerald-50/50 rounded-t-xl"
                        : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
                    }`}
                  >
                    <span>Period {idx + 1}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                        isActive ? "bg-emerald-200 text-emerald-900 font-extrabold" : "bg-slate-200 text-slate-600"
                      }`}
                    >
                      40m
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Render Active Plan */}
          <SinglePeriodCard
            plan={plans[activeTab] || plans[0]}
            periodIndex={activeTab}
            totalPeriods={plans.length}
            onEdit={onEditPlan}
          />
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 2: COLLAPSIBLE ACCORDION VIEW                                        */}
      {/* ========================================================================= */}
      {viewMode === "accordion" && (
        <div className="space-y-4">
          {plans.map((p, idx) => {
            const isOpen = !!openAccordions[idx];
            return (
              <div key={idx} className="border border-slate-200 rounded-2xl bg-white shadow-xs overflow-hidden transition-all">
                {/* Accordion Trigger Header */}
                <button
                  type="button"
                  onClick={() => toggleAccordion(idx)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50/70 transition-colors select-none"
                >
                  <div className="flex items-center gap-3">
                    <span className="h-7 w-7 rounded-full bg-emerald-100 text-emerald-800 font-extrabold text-xs flex items-center justify-center border border-emerald-200">
                      {idx + 1}
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">
                        Period {idx + 1}: {p.lesson}
                      </h3>
                      <p className="text-[11px] text-slate-500 font-medium">
                        Allocation: {p.time_allocation} | Steps: {p.lesson_development_steps?.length || 0} Phases
                      </p>
                    </div>
                  </div>

                  <span className="text-slate-400 font-bold text-sm">
                    {isOpen ? "▲" : "▼"}
                  </span>
                </button>

                {/* Collapsible Content */}
                {isOpen && (
                  <div className="px-6 pb-6 pt-2 border-t border-slate-100">
                    <SinglePeriodCard
                      plan={p}
                      periodIndex={idx}
                      totalPeriods={plans.length}
                      onEdit={onEditPlan}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ===========================================================================
// SUB-COMPONENT: SINGLE 40-MINUTE PERIOD PLAN DETAILS (5m - 30m - 5m)
// ===========================================================================
function SinglePeriodCard({
  plan,
  periodIndex,
  totalPeriods,
  onEdit,
}: {
  plan: LessonPlanSchemaDto;
  periodIndex: number;
  totalPeriods: number;
  onEdit?: (plan: LessonPlanSchemaDto) => void;
}) {
  const isCivicPlan = plan.subject.trim().toLocaleLowerCase() === "civic education";

  return (
    <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-6">
      {/* 4-Column Metadata Header */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Target Level</span>
          <span className="font-mono font-bold text-slate-800">{plan.competence_level}</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Strict Allocation</span>
          <span className="font-extrabold text-emerald-700">40 Minutes ({plan.time_allocation})</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Sequence</span>
          <span className="font-bold text-slate-800">Period {periodIndex + 1} of {totalPeriods}</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Lesson Focus</span>
          <span className="font-bold text-slate-800 truncate block">{plan.lesson}</span>
        </div>
      </div>

      {/* Broad Competency */}
      {plan.competence && (
        <div className="text-xs border-l-4 border-emerald-500 pl-3 py-0.5 bg-emerald-50/30 rounded-r-lg">
          <strong className="text-slate-800 font-bold">Main Competency: </strong>
          <span className="text-slate-600">{plan.competence}</span>
        </div>
      )}

      {/* Assigned Verbatim Learning Outcomes for THIS Period */}
      {plan.unique_learning_outcome && plan.unique_learning_outcome.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700">
              Assigned NIE Outcomes (Period {periodIndex + 1}):
            </span>
            <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {plan.unique_learning_outcome.length} Outcomes Covered
            </span>
          </div>

          <ul className="text-xs text-slate-700 bg-emerald-50/40 border border-emerald-200/80 p-3.5 rounded-xl space-y-1.5">
            {plan.unique_learning_outcome.map((outcome, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-emerald-600 font-extrabold">•</span>
                <span className="leading-relaxed">{outcome}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* PHASE 1: 5-MINUTE ENTRANCE                                          */}
      {/* ------------------------------------------------------------------- */}
      <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 space-y-1.5">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-extrabold uppercase tracking-wide text-amber-900 flex items-center gap-1.5">
            <span>🚪 Phase 1: The Entrance</span>
            <span className="text-[10px] font-normal text-amber-700">(Motivational Hook / Everyday Scenario)</span>
          </h4>
          <span className="text-[10px] font-extrabold px-2 py-0.5 bg-amber-100 text-amber-900 rounded-md border border-amber-200">
            Strictly 5 Mins
          </span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed pl-1">
          {plan.the_entrance}
        </p>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* PHASE 2: 30-MINUTE DEVELOPMENT STEPS                                */}
      {/* ------------------------------------------------------------------- */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-extrabold uppercase tracking-wide text-slate-800 flex items-center gap-1.5">
            <span>📋 Phase 2: Lesson Development Steps</span>
            <span className="text-[10px] font-normal text-slate-500">(Student-Centered Investigation)</span>
          </h4>
          <span className="text-[10px] font-extrabold px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md border border-slate-200">
            Sum: Exactly 30 Mins
          </span>
        </div>

        <div className="space-y-3">
          {plan.lesson_development_steps?.map((step) => (
            <div key={step.step_number} className="border border-slate-200 rounded-xl p-4 bg-white space-y-3 shadow-2xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-extrabold text-emerald-800 flex items-center gap-1.5">
                  <span className="h-4 w-4 rounded-full bg-emerald-100 text-emerald-700 text-[10px] flex items-center justify-center font-bold">
                    {step.step_number}
                  </span>
                  {step.learning_teaching_method}
                </span>

                <span className="text-[11px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-900 rounded border border-emerald-200 font-mono">
                  {step.time_minutes} Mins
                </span>
              </div>

              {/* 2-Column: Teacher Activities vs Student Activities */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="bg-slate-50/60 p-3 rounded-lg border border-slate-100">
                  <strong className="text-slate-600 block mb-1 font-bold">
                    Teacher Activities:
                  </strong>
                  <p className="text-slate-700 leading-relaxed">{step.teacher_activities}</p>
                </div>

                <div className="bg-emerald-50/30 p-3 rounded-lg border border-emerald-100">
                  <strong className="text-emerald-900 block mb-1 font-bold">
                    Student Activities:
                  </strong>
                  <p className="text-slate-700 leading-relaxed">{step.student_activities}</p>
                </div>
              </div>

              {/* Aids and period time */}
              <div className="flex flex-wrap items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-500 gap-2">
                <div>
                  <strong className="text-slate-700 font-semibold">Learning and Teaching Aids: </strong>
                  {step.learning_teaching_aids || "Standard Classroom Resources"}
                </div>
                {!isCivicPlan && step.assessment_and_feedback && (
                  <div>
                    <strong className="text-slate-700 font-semibold">Assessment & Feedback: </strong>
                    {step.assessment_and_feedback}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* PHASE 3: 5-MINUTE CREATIVE ASSESSMENT                               */}
      {/* ------------------------------------------------------------------- */}
      <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 space-y-1.5">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-extrabold uppercase tracking-wide text-indigo-950 flex items-center gap-1.5">
            <span>⚡ Assessment & Closure</span>
            <span className="text-[10px] font-normal text-indigo-700">(Active Review / Jingle / Freeze Frame / Quiz)</span>
          </h4>
          <span className="text-[10px] font-extrabold px-2 py-0.5 bg-indigo-100 text-indigo-900 rounded-md border border-indigo-200">
            Strictly 5 Mins
          </span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed pl-1 italic">
          "{plan.assessment_and_feedback_whole_lesson}"
        </p>
      </div>

      {/* Summary & Post Activity */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-200 text-xs">
        <div>
          <strong className="text-slate-600 block mb-1 font-bold">🎯 Synthesis / Summary:</strong>
          <p className="text-slate-700 leading-relaxed">{plan.summary}</p>
        </div>
        <div>
          <strong className="text-slate-600 block mb-1 font-bold">🏠 Post Activity (Take-Home Inquiry):</strong>
          <p className="text-slate-700 leading-relaxed">{plan.post_activity}</p>
        </div>
      </div>

      {/* Attachments / References footer */}
      {plan.attachments && plan.attachments.length > 0 && (
        <div className="text-[11px] text-slate-500 pt-2 border-t border-slate-100 flex items-center justify-between">
          <span>
            <strong className="text-slate-700">Attachments: </strong>
            {plan.attachments.join(", ")}
          </span>

          {onEdit && (
            <button
              type="button"
              onClick={() => onEdit(plan)}
              className="text-emerald-700 hover:text-emerald-900 font-bold underline cursor-pointer"
            >
              Edit in Structural Editor →
            </button>
          )}
        </div>
      )}
    </div>
  );
}