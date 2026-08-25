'use client';

import React, { useState } from 'react';
import { LessonPlanRequest } from '@/types/lessonPlan';

interface LessonPlanFormProps {
  onSubmit: (formData: LessonPlanRequest) => void;
  isLoading: boolean;
}

export default function LessonPlanForm({ onSubmit, isLoading }: LessonPlanFormProps) {
  const [query, setQuery] = useState('');
  const [gradeLevel, setGradeLevel] = useState('Grade 9');
  const [subject, setSubject] = useState<'Civic Education' | 'Science'>('Civic Education');
  const [useRAG, setUseRAG] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ query, gradeLevel, subject, useRAG });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl border border-slate-200/80 mb-10 transition-all">
      
      {/* Subject Selection Tabs */}
      <div className="mb-6">
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
          Select Subject
        </label>
        <div className="grid grid-cols-2 gap-3 p-1.5 bg-slate-100 rounded-xl">
          <button
            type="button"
            onClick={() => setSubject('Civic Education')}
            className={`py-3 px-4 rounded-lg font-bold text-sm transition flex items-center justify-center gap-2 ${
              subject === 'Civic Education'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span>🏛️</span> Civic Education
          </button>

          <button
            type="button"
            onClick={() => setSubject('Science')}
            className={`py-3 px-4 rounded-lg font-bold text-sm transition flex items-center justify-center gap-2 ${
              subject === 'Science'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span>🧪</span> Science
          </button>
        </div>
      </div>

      {/* Grade Level Buttons (6 to 9) */}
      <div className="mb-6">
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
          Grade Level
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {['Grade 6', 'Grade 7', 'Grade 8', 'Grade 9'].map((grade) => (
            <button
              key={grade}
              type="button"
              onClick={() => setGradeLevel(grade)}
              className={`py-2.5 px-4 rounded-xl text-sm font-bold border transition ${
                gradeLevel === grade
                  ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-sm ring-2 ring-indigo-500/20'
                  : 'border-slate-200 text-slate-700 hover:bg-slate-50 bg-white'
              }`}
            >
              {grade}
            </button>
          ))}
        </div>
      </div>

      {/* Goal / Topic Input Prompt */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-bold text-slate-800">
            Educational Goal / Topic Details
          </label>
          <span className="text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
            Optional - Add goal now or later
          </span>
        </div>
        <textarea
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            subject === 'Civic Education'
              ? "e.g., Fundamental human rights, democratic values, or local government structure..."
              : "e.g., Photosynthesis process, electric circuits, or states of matter..."
          }
          className="w-full p-3.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-800 transition placeholder:text-slate-400 text-sm shadow-inner"
        />
      </div>

      {/* RAG Toggle & Submit Action Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <label className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200/80 cursor-pointer w-full sm:w-auto">
          <input
            type="checkbox"
            checked={useRAG}
            onChange={(e) => setUseRAG(e.target.checked)}
            className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500 cursor-pointer"
          />
          <div>
            <span className="block text-xs font-bold text-slate-800">ChromaDB RAG Grounding</span>
            <span className="text-[10px] text-slate-500">Retrieve matching syllabus documents</span>
          </div>
        </label>

        <button
          type="submit"
          disabled={isLoading}
          className={`w-full sm:w-auto flex-1 py-3.5 px-8 font-bold text-sm text-white rounded-xl shadow-lg transition-all ${
            isLoading
              ? 'bg-indigo-300 cursor-not-allowed'
              : 'bg-linear-to-r from-indigo-600 via-blue-600 to-indigo-700 hover:opacity-95 active:scale-[0.99]'
          }`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              Generating Lesson Plan...
            </span>
          ) : (
            '✨ Generate Lesson Plan'
          )}
        </button>
      </div>
    </form>
  );
}