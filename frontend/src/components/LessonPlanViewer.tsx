'use client';

import React from 'react';
import { FactCheckReport, AlignmentReport } from '@/services/lessonPlanApi';

export interface LessonDevelopmentStep {
  step_number: number;
  teacher_activities: string;
  student_activities: string;
  learning_teaching_method: string;
  learning_teaching_aids: string;
  assessment_and_feedback: string;
  time_minutes: number;
  other?: string;
}

export interface PeradeniyaLessonPlan {
  lesson_plan_number?: string;
  page_no?: string;
  date?: string;
  grade: string;
  subject: string;
  time_allocation: string;
  competence: string;
  competence_level: string;
  lesson: string;
  unique_learning_outcome: string[];
  the_entrance: string;
  lesson_development_steps: LessonDevelopmentStep[];
  summary: string;
  assessment_and_feedback_whole_lesson: string;
  post_activity: string;
  information_sources?: string[];
  attachments?: string[];
  reflection?: string;
  supervisors_notes?: string;
}

interface Props {
  plan: PeradeniyaLessonPlan | any;
  factCheck?: FactCheckReport;
  alignment?: AlignmentReport;
}

export default function LessonPlanViewer({ plan, factCheck, alignment }: Props) {
  if (!plan) return null;

  return (
    <article className="bg-white border border-slate-300 rounded-2xl shadow-sm p-6 sm:p-10 space-y-6 text-slate-900 font-serif print:p-0 print:border-none print:shadow-none">
      {/* 1. Official Header */}
      <div className="text-center border-b border-slate-300 pb-4">
        <h2 className="text-xs uppercase tracking-widest text-slate-600 font-bold font-sans">
          Education Science Division • University of Peradeniya[cite: 1]
        </h2>
        <h1 className="text-2xl font-black uppercase tracking-tight text-slate-900 mt-1">
          Lesson Plan Format[cite: 1]
        </h1>
      </div>

      {/* 2. Top Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs border-b border-slate-200 pb-4 font-sans">
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Date[cite: 1]</span>
          <span className="font-semibold">{plan.date || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Grade[cite: 1]</span>
          <span className="font-semibold">{plan.grade || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Subject[cite: 1]</span>
          <span className="font-semibold">{plan.subject || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Time[cite: 1]</span>
          <span className="font-semibold">{plan.time_allocation || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Lesson Plan No[cite: 1]</span>
          <span className="font-semibold font-mono">{plan.lesson_plan_number || '01'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Page No[cite: 1]</span>
          <span className="font-semibold font-mono">{plan.page_no || '01'}</span>
        </div>
      </div>

      {/* 3. Competence & Outcomes */}
      <div className="space-y-2.5 text-xs border-b border-slate-200 pb-4">
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide">Competence: </strong>[cite: 1]
          <span className="leading-relaxed">{plan.competence}</span>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide">Competence level: </strong>[cite: 1]
          <span className="leading-relaxed">{plan.competence_level}</span>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide">Lesson: </strong>[cite: 1]
          <span className="font-semibold text-slate-900 text-sm">{plan.lesson}</span>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Unique learning outcome :[cite: 1]
          </strong>
          <ul className="list-disc list-inside space-y-1 ml-2 leading-relaxed text-slate-800">
            {plan.unique_learning_outcome?.map((outcome: string, idx: number) => (
              <li key={idx}>{outcome}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* 4. The Entrance */}
      <div className="text-xs border-b border-slate-200 pb-4">
        <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
          The entrance :[cite: 1]
        </strong>
        <p className="leading-relaxed text-slate-800 whitespace-pre-line bg-slate-50 p-3 rounded-lg border border-slate-200">
          {plan.the_entrance}
        </p>
      </div>

      {/* 5. 7-Column Lesson Development Table */}
      <div>
        <h3 className="text-xs font-bold font-sans uppercase tracking-wide text-slate-800 mb-2">
          Lesson development :[cite: 1]
        </h3>
        <div className="overflow-x-auto border border-slate-300 rounded-lg">
          <table className="min-w-full text-left text-xs border-collapse divide-y divide-slate-300">
            <thead className="bg-slate-100 font-sans font-bold text-slate-700 uppercase tracking-wider">
              <tr className="divide-x divide-slate-300">
                <th className="p-2.5 w-12 text-center">Steps[cite: 1]</th>
                <th className="p-2.5 w-1/4">Teacher activities[cite: 1]</th>
                <th className="p-2.5 w-1/4">Student activities[cite: 1]</th>
                <th className="p-2.5">Learning and teaching method[cite: 1]</th>
                <th className="p-2.5">Learning and teaching aids[cite: 1]</th>
                <th className="p-2.5">Assessment and feedback[cite: 1]</th>
                <th className="p-2.5 w-14 text-center">Time[cite: 1]</th>
                <th className="p-2.5 w-16">Other[cite: 1]</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {plan.lesson_development_steps?.map((step: LessonDevelopmentStep, idx: number) => (
                <tr key={idx} className="divide-x divide-slate-200 align-top hover:bg-slate-50/50">
                  <td className="p-2.5 text-center font-bold font-mono text-slate-700">
                    {step.step_number || idx + 1}
                  </td>
                  <td className="p-2.5 whitespace-pre-line leading-relaxed text-slate-800">
                    {step.teacher_activities}
                  </td>
                  <td className="p-2.5 whitespace-pre-line leading-relaxed text-slate-800">
                    {step.student_activities}
                  </td>
                  <td className="p-2.5 leading-relaxed text-slate-800">
                    {step.learning_teaching_method}
                  </td>
                  <td className="p-2.5 leading-relaxed text-slate-800">
                    {step.learning_teaching_aids}
                  </td>
                  <td className="p-2.5 leading-relaxed text-slate-800">
                    {step.assessment_and_feedback}
                  </td>
                  <td className="p-2.5 text-center font-mono text-slate-600 whitespace-nowrap">
                    {step.time_minutes}m
                  </td>
                  <td className="p-2.5 text-[11px] text-slate-500">
                    {step.other || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 6. Post-Lesson Syntheses & Resources */}
      <div className="space-y-3 text-xs border-b border-slate-200 pb-5">
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-0.5">
            Summary:[cite: 1]
          </strong>
          <p className="leading-relaxed text-slate-800">{plan.summary}</p>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-0.5">
            Assessment and feedback (whole lesson):[cite: 1]
          </strong>
          <p className="leading-relaxed text-slate-800">{plan.assessment_and_feedback_whole_lesson}</p>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-0.5">
            Post activity (relevant to the lesson):[cite: 1]
          </strong>
          <p className="leading-relaxed text-slate-800">{plan.post_activity}</p>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-0.5">
            Information sources:[cite: 1]
          </strong>
          <p className="leading-relaxed text-slate-800">
            {Array.isArray(plan.information_sources)
              ? plan.information_sources.join(', ')
              : plan.information_sources || '—'}
          </p>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-0.5">
            Attachments:[cite: 1]
          </strong>
          <p className="leading-relaxed text-slate-800">
            {Array.isArray(plan.attachments)
              ? plan.attachments.join(', ')
              : plan.attachments || 'None'}
          </p>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-0.5">
            Reflection:[cite: 1]
          </strong>
          <p className="leading-relaxed text-slate-600 italic">
            {plan.reflection || 'To be completed post-delivery by the teacher.'}
          </p>
        </div>
      </div>

      {/* 7. Official Signatures and Supervisor's Notes */}
      <div className="pt-2 text-xs">
        <div className="grid grid-cols-2 gap-12 font-sans mb-8">
          <div>
            <div className="mt-12 border-t border-dashed border-slate-400 pt-1.5 text-center text-slate-700">
              Teacher&apos;s signature[cite: 1]
            </div>
          </div>
          <div>
            <div className="mt-12 border-t border-dashed border-slate-400 pt-1.5 text-center text-slate-700">
              Signature of the principal/head teacher:[cite: 1]
            </div>
          </div>
        </div>
        <div className="border border-slate-300 rounded-lg p-3 bg-slate-50">
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Supervisor&apos;s notes
          </strong>
          <p className="text-slate-600 italic text-[11px] min-h-9">
            {plan.supervisors_notes || '—'}
          </p>
        </div>
      </div>

      {/* 8. Action Controls */}
      <div className="flex justify-end pt-2 print:hidden">
        <button
          type="button"
          onClick={() => window.print()}
          className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold font-sans rounded-xl shadow-sm transition-all flex items-center gap-2 cursor-pointer"
        >
          🖨️ Print / Export PDF
        </button>
      </div>
    </article>
  );
}