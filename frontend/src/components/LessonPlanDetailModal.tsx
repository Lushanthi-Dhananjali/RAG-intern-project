'use client';

import React, { useState } from 'react';
import { LessonPlanDto } from '@/services/lessonPlanApi';

interface LessonPlanDetailModalProps {
  isOpen: boolean;
  filename: string;
  plan: LessonPlanDto | null;
  onClose: () => void;
}

export default function LessonPlanDetailModal({
  isOpen,
  filename,
  plan,
  onClose,
}: LessonPlanDetailModalProps) {
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen || !plan) return null;

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(plan, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/70 backdrop-blur-xs overflow-y-auto">
      <div className="relative bg-white rounded-2xl max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150 my-auto">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/80 rounded-t-2xl">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100/90 px-2.5 py-0.5 rounded-full">
                Peradeniya Practice Teaching Format
              </span>
              <span className="text-xs font-mono text-slate-500 bg-slate-200/80 px-2 py-0.5 rounded-md">
                {filename}
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-black text-slate-900">
              {plan.lesson || `Competency ${plan.competence_level}`}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrint}
              className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors shadow-2xs inline-flex items-center gap-1.5"
              title="Print Lesson Plan"
            >
              🖨️ Print
            </button>
            <button
              type="button"
              onClick={handleCopyJson}
              className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors shadow-2xs inline-flex items-center gap-1.5"
              title="Copy JSON Payload"
            >
              {copied ? '✅ Copied!' : '📋 Copy JSON'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-200 hover:bg-slate-300 text-slate-700 flex items-center justify-center font-bold text-sm transition-colors ml-1"
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-slate-800">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Grade</span>
              <span className="font-extrabold text-slate-900">{plan.grade}</span>
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Subject</span>
              <span className="font-extrabold text-slate-900">{plan.subject}</span>
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Competency Level</span>
              <span className="font-extrabold text-indigo-700 font-mono">{plan.competence_level}</span>
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">Time Allocation</span>
              <span className="font-extrabold text-emerald-700">{plan.time_allocation}</span>
            </div>
          </div>

          {/* Competence Statement */}
          <div className="space-y-1">
            <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Competence</h4>
            <p className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100 text-slate-900 font-medium">
              {plan.competence}
            </p>
          </div>

          {/* Unique Learning Outcomes */}
          {plan.unique_learning_outcome && plan.unique_learning_outcome.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">
                Unique Learning Outcomes ({plan.unique_learning_outcome.length})
              </h4>
              <ul className="space-y-1.5">
                {plan.unique_learning_outcome.map((outcome, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 p-2.5 bg-white rounded-lg border border-slate-200 text-xs text-slate-800"
                  >
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 font-bold text-[11px] flex items-center justify-center mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="font-medium leading-relaxed">{outcome}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* The Entrance */}
          {plan.the_entrance && (
            <div className="space-y-1">
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">The Entrance (Introduction)</h4>
              <div className="p-3.5 bg-amber-50/60 rounded-xl border border-amber-200/80 text-xs leading-relaxed text-amber-950 font-medium">
                {plan.the_entrance}
              </div>
            </div>
          )}

          {/* Lesson Development Steps Table */}
          {plan.lesson_development_steps && plan.lesson_development_steps.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">
                Lesson Development Steps ({plan.lesson_development_steps.length} Steps)
              </h4>
              <div className="overflow-x-auto border border-slate-200 rounded-xl shadow-2xs">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100 text-slate-700 uppercase text-[10px] tracking-wider font-extrabold border-b border-slate-200">
                    <tr>
                      <th className="p-2.5 border-r border-slate-200 w-12 text-center">Step</th>
                      <th className="p-2.5 border-r border-slate-200 min-w-44">Teacher Activities</th>
                      <th className="p-2.5 border-r border-slate-200 min-w-44">Student Activities</th>
                      <th className="p-2.5 border-r border-slate-200 min-w-28">Method</th>
                      <th className="p-2.5 border-r border-slate-200 min-w-28">Aids</th>
                      <th className="p-2.5 border-r border-slate-200 min-w-36">Assessment & Feedback</th>
                      <th className="p-2.5 w-16 text-center">Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {plan.lesson_development_steps.map((step, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition-colors align-top">
                        <td className="p-2.5 border-r border-slate-200 text-center font-bold text-indigo-700">
                          {step.step_number || idx + 1}
                        </td>
                        <td className="p-2.5 border-r border-slate-200 text-slate-800 leading-relaxed font-medium">
                          {step.teacher_activities}
                        </td>
                        <td className="p-2.5 border-r border-slate-200 text-slate-800 leading-relaxed font-medium">
                          {step.student_activities}
                        </td>
                        <td className="p-2.5 border-r border-slate-200 text-slate-700">
                          <span className="inline-block px-2 py-0.5 bg-slate-100 rounded text-[11px] font-semibold">
                            {step.learning_teaching_method}
                          </span>
                        </td>
                        <td className="p-2.5 border-r border-slate-200 text-slate-700 text-[11px]">
                          {step.learning_teaching_aids}
                        </td>
                        <td className="p-2.5 border-r border-slate-200 text-slate-700 text-[11px]">
                          {step.assessment_and_feedback}
                        </td>
                        <td className="p-2.5 text-center font-extrabold text-slate-900 whitespace-nowrap">
                          {step.time_minutes} m
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Summary & Assessment Whole Lesson */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {plan.summary && (
              <div className="space-y-1">
                <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Summary</h4>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs leading-relaxed text-slate-800">
                  {plan.summary}
                </div>
              </div>
            )}
            {plan.assessment_and_feedback_whole_lesson && (
              <div className="space-y-1">
                <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Whole Lesson Assessment</h4>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs leading-relaxed text-slate-800">
                  {plan.assessment_and_feedback_whole_lesson}
                </div>
              </div>
            )}
          </div>

          {/* Post Activity */}
          {plan.post_activity && (
            <div className="space-y-1">
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">Post Activity (Homework / Extension)</h4>
              <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100 text-xs leading-relaxed text-blue-950 font-medium">
                {plan.post_activity}
              </div>
            </div>
          )}

          {/* Sources and Attachments */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-200">
            {plan.information_sources && plan.information_sources.length > 0 && (
              <div>
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Information Sources
                </h5>
                <ul className="list-disc list-inside text-xs text-slate-600 space-y-0.5">
                  {plan.information_sources.map((src, idx) => (
                    <li key={idx}>{src}</li>
                  ))}
                </ul>
              </div>
            )}
            {plan.attachments && plan.attachments.length > 0 && (
              <div>
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Attachments
                </h5>
                <ul className="list-disc list-inside text-xs text-slate-600 space-y-0.5">
                  {plan.attachments.map((att, idx) => (
                    <li key={idx}>{att}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-3 border-t border-slate-200 bg-slate-50/80 rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
