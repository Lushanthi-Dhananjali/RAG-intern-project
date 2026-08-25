'use client';

import React, { useState } from 'react';
import LessonPlanForm from '../components/LessonPlanForm';
import StructuralEditor from '../components/StructuralEditor';
import { LessonPlanRequest, LessonPlanGenerateResponse } from '../types/lessonPlan';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [generationMode, setGenerationMode] = useState<'standard' | 'stream'>('standard');
  const [planData, setPlanData] = useState<LessonPlanGenerateResponse | null>(null);
  const [streamedText, setStreamedText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const handleStandardGenerate = async (requestData: LessonPlanRequest) => {
    setIsLoading(true);
    setError(null);
    setPlanData(null);

    try {
      const response = await fetch('http://localhost:5161/api/v1/lessonplan/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: requestData.query || `${requestData.subject} general lesson for ${requestData.gradeLevel}`,
          grade_level: requestData.gradeLevel,
        }),
      });

      if (!response.ok) throw new Error(`Server status ${response.status}`);
      const result: LessonPlanGenerateResponse = await response.json();
      setPlanData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to generate lesson plan.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateStream = async (requestData: LessonPlanRequest) => {
    setIsLoading(true);
    setError(null);
    setStreamedText('');

    try {
      const response = await fetch('http://localhost:5161/api/v1/lessonplan/generate-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: requestData.query || `${requestData.subject} general lesson for ${requestData.gradeLevel}`,
          grade_level: requestData.gradeLevel,
        }),
      });

      if (!response.ok || !response.body) throw new Error(`Stream error ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const textChunk = line.replace('data: ', '');
            setStreamedText((prev) => prev + textChunk + ' ');
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Stream processing failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (requestData: LessonPlanRequest) => {
    if (generationMode === 'standard') {
      handleStandardGenerate(requestData);
    } else {
      handleGenerateStream(requestData);
    }
  };

  return (
    <main className="min-h-screen bg-linear-to-r from-slate-100 via-indigo-50/40 to-slate-100 py-10 px-4 sm:px-8 max-w-5xl mx-auto">
      {/* Creative Header */}
      <header className="mb-8 text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-100/80 border border-indigo-200 text-indigo-700 text-xs font-extrabold tracking-wide uppercase">
          🚀 Next-Gen RAG Assistant
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight">
          Lesson Plan Generator
        </h1>
        <p className="text-slate-600 max-w-lg mx-auto text-sm sm:text-base font-medium">
          Create, customize, and edit AI-assisted lesson plans for Grades 6–9
        </p>

        {/* Mode Toggle Switch */}
        <div className="inline-flex p-1.5 bg-slate-200/80 backdrop-blur-md rounded-2xl mt-4 border border-slate-300/80">
          <button
            onClick={() => setGenerationMode('standard')}
            className={`px-5 py-2 rounded-xl text-xs font-bold transition-all ${
              generationMode === 'standard'
                ? 'bg-white text-indigo-700 shadow-md'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            📋 Structural Editor
          </button>
          <button
            onClick={() => setGenerationMode('stream')}
            className={`px-5 py-2 rounded-xl text-xs font-bold transition-all ${
              generationMode === 'stream'
                ? 'bg-white text-indigo-700 shadow-md'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ⚡ Real-Time Stream
          </button>
        </div>
      </header>

      {/* Form Input */}
      <LessonPlanForm onSubmit={handleFormSubmit} isLoading={isLoading} />

      {/* Error Alert */}
      {error && (
        <div className="p-4 mb-6 text-red-700 bg-red-50 rounded-xl border border-red-200 shadow-sm text-sm font-semibold">
          ⚠️ {error}
        </div>
      )}

      {/* Outputs */}
      {generationMode === 'standard' && planData && (
        <StructuralEditor initialPlan={planData.lesson_plan} />
      )}

      {generationMode === 'stream' && (streamedText || isLoading) && (
        <div className="bg-slate-900 p-6 rounded-2xl shadow-xl border border-slate-800 text-green-400 font-mono text-sm leading-relaxed whitespace-pre-wrap min-h-55">
          {streamedText}
          {isLoading && <span className="animate-pulse inline-block w-2 h-4 bg-green-400 ml-1">▌</span>}
        </div>
      )}
    </main>
  );
}