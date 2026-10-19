"use client";

import React from "react";
import { PedagogicalActivityOption } from "@/types/lessonPlan";

interface ActivitySelectionStepProps {
  activityOptions: PedagogicalActivityOption[];
  selectedOptionId: string;
  setSelectedOptionId: (id: string) => void;
  customStrategy: string;
  setCustomStrategy: (val: string) => void;
  discoveredTopic: string;
  studentCount: number;
  periods: number;
  isLoading: boolean;
  onBack: () => void;
  onProceed: () => void;
}

export default function ActivitySelectionStep({
  activityOptions,
  selectedOptionId,
  setSelectedOptionId,
  customStrategy,
  setCustomStrategy,
  discoveredTopic,
  studentCount,
  periods,
  isLoading,
  onBack,
  onProceed,
}: ActivitySelectionStepProps) {
  // Check if a valid strategy is selected (either an AI card or custom text)
  const isCustomActive = customStrategy.trim().length > 0;
  const canProceed = isCustomActive || selectedOptionId.length > 0;

  return (
    <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6 animate-in fade-in duration-200">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-4 gap-2">
        <div>
          <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200 uppercase tracking-wide">
            Step 2 of 3
          </span>
          <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 mt-1">
            Choose Student-Centered Activity Strategy
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Topic: <span className="font-semibold text-slate-700">{discoveredTopic}</span> |{" "}
            Class Size: <span className="font-semibold text-slate-700">{studentCount} Students</span> |{" "}
            Duration: <span className="font-semibold text-slate-700">{periods} x 40m Periods</span>
          </p>
        </div>

        <button
          type="button"
          onClick={onBack}
          className="text-xs font-bold text-slate-500 hover:text-slate-800 underline transition-colors"
        >
          ← Edit Class Constraints
        </button>
      </div>

      {/* 3 AI Generated Interactive Cards */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
          Recommended Pedagogical Strategies (Select One):
        </label>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">
          {activityOptions.map((opt, index) => {
            const isSelected = selectedOptionId === opt.id && !isCustomActive;

            return (
              <div
                key={opt.id}
                onClick={() => {
                  setSelectedOptionId(opt.id);
                  setCustomStrategy(""); // Clear custom input when AI card is picked
                }}
                className={`relative cursor-pointer rounded-2xl p-5 border-2 transition-all flex flex-col justify-between select-none ${
                  isSelected
                    ? "border-emerald-600 bg-emerald-50/40 shadow-md ring-2 ring-emerald-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50 bg-white"
                }`}
              >
                {/* Top: Badges & Radio Indicator */}
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                      {opt.pedagogy_type}
                    </span>

                    <div className="flex items-center">
                      <input
                        type="radio"
                        name="activity_card_selector"
                        checked={isSelected}
                        onChange={() => {
                          setSelectedOptionId(opt.id);
                          setCustomStrategy("");
                        }}
                        className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                      />
                    </div>
                  </div>

                  <h3 className="font-extrabold text-slate-900 text-sm sm:text-base leading-snug mb-2">
                    {opt.title}
                  </h3>

                  <p className="text-xs text-slate-600 leading-relaxed mb-4">
                    {opt.description}
                  </p>
                </div>

                {/* Bottom: Dynamic Logistics & 5m Creative Assessment Breakdown */}
                <div className="pt-3 border-t border-slate-100 text-[11px] space-y-2.5">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/60">
                    <strong className="text-slate-700 block font-bold mb-0.5">
                      👥 Class Grouping ({studentCount} students):
                    </strong>
                    <span className="text-slate-600">{opt.student_grouping}</span>
                  </div>

                  {opt.required_materials && opt.required_materials.length > 0 && (
                    <div className="text-slate-600">
                      <strong className="text-slate-700 font-bold">📦 Materials: </strong>
                      {opt.required_materials.join(", ")}
                    </div>
                  )}

                  <div className="bg-emerald-50/80 p-2.5 rounded-lg border border-emerald-200 text-emerald-950">
                    <strong className="text-emerald-900 block font-bold mb-0.5">
                      ⚡ 5m Creative Assessment:
                    </strong>
                    <span className="italic leading-snug">
                      "{opt.creative_assessment_preview}"
                    </span>
                  </div>
                </div>

                {/* Selected Indicator Pill */}
                {isSelected && (
                  <span className="absolute -top-2.5 right-4 bg-emerald-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full shadow-xs">
                    Selected
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Divider */}
      <div className="relative flex py-2 items-center">
        <div className="flex-grow border-t border-slate-200"></div>
        <span className="flex-shrink mx-4 text-[11px] font-bold uppercase tracking-wider text-slate-400 bg-white px-2">
          Or Provide Your Own Custom Idea
        </span>
        <div className="flex-grow border-t border-slate-200"></div>
      </div>

      {/* Custom Strategy Textarea */}
      <div className={`p-4 rounded-xl border-2 transition-all ${isCustomActive ? "border-emerald-600 bg-emerald-50/30" : "border-slate-200 bg-slate-50/40"}`}>
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            Custom Activity Strategy / Practical Idea (Overrides AI options above):
          </label>
          {isCustomActive && (
            <span className="text-[10px] font-extrabold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
              Custom Active
            </span>
          )}
        </div>

        <textarea
          rows={3}
          placeholder="e.g., Bring actual utility bills (water/electricity) to the classroom; divide 35 students into 7 household teams to verify concession rates, with a 2-line rhyming feedback at the end..."
          value={customStrategy}
          onChange={(e) => setCustomStrategy(e.target.value)}
          className="w-full rounded-lg border border-slate-300 p-3 text-xs leading-relaxed focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-white placeholder:text-slate-400"
        />

        <p className="text-[11px] text-slate-500 mt-1.5">
          {isCustomActive
            ? "✓ Your custom strategy will be prioritized during prompt construction."
            : "Typing here will automatically switch the generator to use your custom pedagogical approach."}
        </p>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2.5 text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors"
        >
          ← Back to Constraints
        </button>

        <button
          type="button"
          disabled={isLoading || !canProceed}
          onClick={onProceed}
          className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all shadow-sm hover:shadow disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2.5 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              Generating {periods} x 40m Sequential Plans...
            </>
          ) : (
            `Generate Sequential Plans (${periods} Periods) →`
          )}
        </button>
      </div>
    </div>
  );
}