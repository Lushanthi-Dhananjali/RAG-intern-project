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
            <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
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
              className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-xs"
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
                const periodNum = p.period_number ?? (idx + 1);
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setActiveTab(idx)}
                    className={`py-2.5 px-4 text-xs font-bold border-b-2 whitespace-nowrap transition-all flex items-center gap-2 ${
                      isActive
                        ? "border-blue-600 text-blue-800 bg-blue-50/70 rounded-t-xl"
                        : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
                    }`}
                  >
                    <span>Period {periodNum}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                        isActive ? "bg-blue-200 text-blue-900 font-extrabold" : "bg-slate-200 text-slate-600"
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
            periodIndex={(plans[activeTab] || plans[0]).period_number ? ((plans[activeTab] || plans[0]).period_number! - 1) : activeTab}
            totalPeriods={(plans[activeTab] || plans[0]).total_periods || plans.length}
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
            const periodNum = p.period_number ?? (idx + 1);
            return (
              <div key={idx} className="border border-slate-200 rounded-2xl bg-white shadow-xs overflow-hidden transition-all">
                {/* Accordion Trigger Header */}
                <button
                  type="button"
                  onClick={() => toggleAccordion(idx)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50/70 transition-colors select-none"
                >
                  <div className="flex items-center gap-3">
                    <span className="h-7 w-7 rounded-full bg-blue-100 text-blue-800 font-extrabold text-xs flex items-center justify-center border border-blue-200">
                      {periodNum}
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">
                        Period {periodNum}: {p.lesson}
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
                      periodIndex={p.period_number ? p.period_number - 1 : idx}
                      totalPeriods={p.total_periods || plans.length}
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
          <span className="font-extrabold text-blue-700">40 Minutes ({plan.time_allocation})</span>
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
        <div className="text-xs border-l-4 border-blue-500 pl-3 py-0.5 bg-blue-50/40 rounded-r-lg">
          <strong className="text-slate-800 font-bold">Main Competency: </strong>
          <span className="text-slate-600">{plan.competence}</span>
        </div>
      )}

      {/* Selected Activity for this Period (Only selected activity displayed) */}
      {(plan.selected_activity_title || plan.selected_activity || (plan.activity_options && plan.activity_options.length > 0)) && (
        <section className="rounded-xl border border-blue-200 bg-blue-50/50 p-4">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-xs font-extrabold uppercase tracking-wide text-blue-900">
              Selected Activity (Period {periodIndex + 1})
            </h4>
            <span className="rounded-full bg-blue-600 px-2.5 py-0.5 text-[9px] font-bold text-white uppercase">
              Active Strategy
            </span>
          </div>

          <h5 className="mt-2 text-sm font-extrabold text-slate-900">
            {plan.selected_activity_title || (plan.activity_options && plan.activity_options[0]?.title) || "Selected Learning Activity"}
          </h5>

          {((plan.activity_options && plan.activity_options[0]?.description) || plan.selected_activity) && (
            <p className="mt-1.5 text-xs leading-relaxed text-slate-700">
              {(plan.activity_options && plan.activity_options[0]?.description) || plan.selected_activity}
            </p>
          )}

          {plan.activity_options && plan.activity_options[0]?.student_action_summary && (
            <p className="mt-2 rounded-lg border border-blue-100 bg-white p-2.5 text-xs text-slate-600">
              <strong className="text-blue-900">Student Participation: </strong>
              {plan.activity_options[0].student_action_summary}
            </p>
          )}

          <div className="mt-2.5 flex flex-wrap gap-2 text-[11px]">
            {plan.activity_options && plan.activity_options[0]?.student_grouping && (
              <span className="rounded-md border border-slate-200 bg-white px-2 py-1 font-semibold text-slate-700">
                <strong>Grouping:</strong> {plan.activity_options[0].student_grouping}
              </span>
            )}
            {plan.activity_options && plan.activity_options[0]?.pedagogy_type && (
              <span className="rounded-md border border-slate-200 bg-white px-2 py-1 font-semibold text-slate-700">
                <strong>Pedagogy:</strong> {plan.activity_options[0].pedagogy_type}
              </span>
            )}
          </div>

          {plan.custom_teacher_activity && (
            <div className="mt-3 rounded-lg border border-blue-200 bg-white p-2.5 text-xs text-slate-800">
              <strong className="text-blue-900">Teacher's Custom Approach: </strong>
              <span className="whitespace-pre-line">{plan.custom_teacher_activity}</span>
            </div>
          )}
        </section>
      )}

      {/* Assigned Verbatim Learning Outcomes for THIS Period */}
      {plan.unique_learning_outcome && plan.unique_learning_outcome.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700">
              Assigned NIE Outcomes (Period {periodIndex + 1}):
            </span>
            <span className="text-[10px] font-semibold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              {plan.unique_learning_outcome.length} Outcomes Covered
            </span>
          </div>

          <ul className="text-xs text-slate-700 bg-blue-50/50 border border-blue-200/80 p-3.5 rounded-xl space-y-1.5">
            {plan.unique_learning_outcome.map((outcome, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-blue-600 font-extrabold">•</span>
                <span className="leading-relaxed">{outcome}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* PHASE 1: 5-MINUTE ENTRANCE                                          */}
      {/* ------------------------------------------------------------------- */}
      <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/40 space-y-1.5">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-extrabold uppercase tracking-wide text-blue-900 flex items-center gap-1.5">
            <span>🚪 Phase 1: The Entrance</span>
            <span className="text-[10px] font-normal text-blue-700">(Prior Knowledge and Period Topic)</span>
          </h4>
          <span className="text-[10px] font-extrabold px-2 py-0.5 bg-blue-100 text-blue-900 rounded-md border border-blue-200">
            Strictly {plan.entrance_duration_minutes ?? 5} Mins
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
                <span className="text-xs font-extrabold text-blue-800 flex items-center gap-1.5">
                  <span className="h-4 w-4 rounded-full bg-blue-100 text-blue-700 text-[10px] flex items-center justify-center font-bold">
                    {step.step_number}
                  </span>
                  {step.learning_teaching_method}
                </span>

                <span className="text-[11px] font-bold px-2 py-0.5 bg-blue-100 text-blue-900 rounded border border-blue-200 font-mono">
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

                <div className="bg-blue-50/50 p-3 rounded-lg border border-blue-100">
                  <strong className="text-blue-900 block mb-1 font-bold">
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
      {/* ASSESSMENT GUIDANCE FOR THE FIVE-MINUTE ASSIGNMENT                   */}
      {/* ------------------------------------------------------------------- */}
      <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 space-y-1.5">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-extrabold uppercase tracking-wide text-indigo-950 flex items-center gap-1.5">
            <span>⚡ Assignment Assessment & Feedback</span>
            <span className="text-[10px] font-normal text-indigo-700">(Guidance for the five-minute task)</span>
          </h4>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed pl-1 italic">
          "{plan.assessment_and_feedback_whole_lesson}"
        </p>
      </div>

      {/* Five-minute conclusion and assignment */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 rounded-xl border border-blue-200 bg-blue-50/40 p-4 text-xs">
        <div className="rounded-lg border border-blue-100 bg-white p-3">
          <strong className="text-blue-800 block mb-1 font-bold">🎯 Synthesis / Summary (within the 5-minute closure):</strong>
          <p className="text-slate-700 leading-relaxed">{plan.summary}</p>
        </div>
        <div className="rounded-lg border border-blue-100 bg-white p-3">
          <strong className="text-blue-800 block mb-1 font-bold">
            Assignment / Concluding Task ({plan.assignment_duration_minutes ?? 5} minutes):
          </strong>
          <p className="text-slate-700 leading-relaxed">{plan.post_activity}</p>
        </div>
      </div>

      {/* Information Sources & Attachments footer */}
      {((plan.information_sources && plan.information_sources.length > 0) || (plan.attachments && plan.attachments.length > 0) || onEdit) && (
        <div className="text-[11px] text-slate-500 pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-col gap-1">
            {plan.information_sources && plan.information_sources.length > 0 && (
              <span>
                <strong className="text-slate-700">Information Sources: </strong>
                {plan.information_sources.join(", ")}
              </span>
            )}
            {plan.attachments && plan.attachments.length > 0 && (
              <span>
                <strong className="text-slate-700">Attachments: </strong>
                {plan.attachments.join(", ")}
              </span>
            )}
          </div>

          {onEdit && (
            <button
              type="button"
              onClick={() => onEdit(plan)}
              className="text-blue-700 hover:text-blue-900 font-bold underline cursor-pointer ml-auto"
            >
              Edit in Structural Editor →
            </button>
          )}
        </div>
      )}
    </div>
  );
}