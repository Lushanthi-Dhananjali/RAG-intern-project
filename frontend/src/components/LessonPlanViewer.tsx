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

  const summaryText = plan.summary || (plan as any).Summary || '—';
  const wholeLessonAssessment =
    plan.assessment_and_feedback_whole_lesson ||
    (plan as any).assessmentAndFeedbackWholeLesson ||
    (plan as any).assessment_and_feedback ||
    '—';
  const postActivity = plan.post_activity || (plan as any).postActivity || '—';
  const informationSources = plan.information_sources || (plan as any).informationSources;
  const attachmentsList = plan.attachments || (plan as any).Attachments;

  return (
    <article className="bg-white border border-slate-300 rounded-2xl shadow-sm p-6 sm:p-10 space-y-6 text-slate-900 font-serif print:p-0 print:border-none print:shadow-none">
      {/* 1. Official Header */}
      <div className="text-center border-b border-slate-300 pb-4">
        <h2 className="text-xs uppercase tracking-widest text-slate-600 font-bold font-sans">
          Education Science Division • University of Peradeniya
        </h2>
        <h1 className="text-2xl font-black uppercase tracking-tight text-slate-900 mt-1">
          Lesson Plan Format
        </h1>
      </div>

      {/* 2. Top Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs border-b border-slate-200 pb-4 font-sans">
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Date</span>
          <span className="font-semibold">{plan.date || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Grade</span>
          <span className="font-semibold">{plan.grade || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Subject</span>
          <span className="font-semibold">{plan.subject || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Time</span>
          <span className="font-semibold">{plan.time_allocation || '—'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Lesson Plan No</span>
          <span className="font-semibold font-mono">{plan.lesson_plan_number || '01'}</span>
        </div>
        <div>
          <span className="font-bold text-slate-500 block uppercase tracking-wider text-[10px]">Page No</span>
          <span className="font-semibold font-mono">{plan.page_no || '01'}</span>
        </div>
      </div>

      {/* 3. Competence & Outcomes */}
      <div className="space-y-2.5 text-xs border-b border-slate-200 pb-4">
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide">Competence: </strong>
          <span className="leading-relaxed">{plan.competence}</span>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide">Competence level: </strong>
          <span className="leading-relaxed font-mono font-bold text-indigo-700">{plan.competence_level}</span>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide">Lesson: </strong>
          <span className="font-semibold text-slate-900 text-sm">{plan.lesson}</span>
        </div>
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Unique learning outcome:
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
          The entrance:
        </strong>
        <p className="leading-relaxed text-slate-800 whitespace-pre-line bg-slate-50 p-3 rounded-lg border border-slate-200">
          {plan.the_entrance}
        </p>
      </div>

      {/* 5. 7-Column Lesson Development Table */}
      <div>
        <h3 className="text-xs font-bold font-sans uppercase tracking-wide text-slate-800 mb-2">
          Lesson development:
        </h3>
        <div className="overflow-x-auto border border-slate-300 rounded-lg">
          <table className="min-w-full text-left text-xs border-collapse divide-y divide-slate-300">
            <thead className="bg-slate-100 font-sans font-bold text-slate-700 uppercase tracking-wider">
              <tr className="divide-x divide-slate-300">
                <th className="p-2.5 w-12 text-center">Steps</th>
                <th className="p-2.5 w-1/4">Teacher activities</th>
                <th className="p-2.5 w-1/4">Student activities</th>
                <th className="p-2.5">Learning and teaching method</th>
                <th className="p-2.5">Learning and teaching aids</th>
                <th className="p-2.5">Assessment and feedback</th>
                <th className="p-2.5 w-14 text-center">Time</th>
                <th className="p-2.5 w-16">Other</th>
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
      <div className="space-y-4 text-xs border-b border-slate-200 pb-5">
        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Summary:
          </strong>
          <p className="leading-relaxed text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
            {summaryText}
          </p>
        </div>

        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Assessment and feedback (whole lesson):
          </strong>
          <p className="leading-relaxed text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
            {wholeLessonAssessment}
          </p>
        </div>

        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Post activity (relevant to the lesson):
          </strong>
          <p className="leading-relaxed text-slate-800 bg-blue-50/60 p-3 rounded-lg border border-blue-100 font-medium">
            {postActivity}
          </p>
        </div>

        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Information sources:
          </strong>
          {Array.isArray(informationSources) && informationSources.length > 0 ? (
            <ul className="list-disc list-inside space-y-1.5 ml-1 leading-relaxed text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
              {informationSources.map((source: string, idx: number) => (
                <li key={idx} className="font-medium text-slate-800">
                  {source}
                </li>
              ))}
            </ul>
          ) : (
            <p className="leading-relaxed text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
              {typeof informationSources === 'string' && informationSources.trim()
                ? informationSources
                : '—'}
            </p>
          )}
        </div>

        <div>
          <strong className="font-sans uppercase text-slate-700 tracking-wide block mb-1">
            Attachments:
          </strong>
          {Array.isArray(attachmentsList) && attachmentsList.length > 0 ? (
            <ul className="list-disc list-inside space-y-1.5 ml-1 leading-relaxed text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
              {attachmentsList.map((item: string, idx: number) => (
                <li key={idx} className="font-medium text-slate-800">
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="leading-relaxed text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
              {typeof attachmentsList === 'string' && attachmentsList.trim()
                ? attachmentsList
                : 'None'}
            </p>
          )}
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