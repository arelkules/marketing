"use client";
import { useState, useCallback } from "react";
import useSWR from "swr";
import FinancialCard from "@/components/command/FinancialCard";
import SocialCard from "@/components/command/SocialCard";
import VisionPanel from "@/components/command/VisionPanel";
import NextStepsPanel from "@/components/command/NextStepsPanel";
import { fetcher } from "@/lib/api";

const GOAL_ILS = 100_000_000;
const PHASES: Record<string, { label: string; color: string }> = {
  seed:     { label: "SEED",     color: "bg-yellow-900 text-yellow-300" },
  build:    { label: "BUILD",    color: "bg-blue-900 text-blue-300" },
  launch:   { label: "LAUNCH",   color: "bg-purple-900 text-purple-300" },
  scale:    { label: "SCALE",    color: "bg-green-900 text-green-300" },
  dominate: { label: "DOMINATE", color: "bg-red-900 text-red-300" },
};

function fmt(n: number) {
  if (n >= 1_000_000) return `₪${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `₪${(n / 1_000).toFixed(1)}K`;
  return `₪${n.toLocaleString()}`;
}

function monthsTo100M(mrr: number) {
  const calc = (r: number) => {
    if (mrr <= 0) return 999;
    let m = mrr, months = 0;
    while (m * 12 < GOAL_ILS && months < 360) { m *= (1 + r); months++; }
    return months;
  };
  return { conservative: calc(0.20), expected: calc(0.35), aggressive: calc(0.50) };
}

export default function CommandCenter() {
  const [refresh, setRefresh] = useState(0);
  const onSaved = useCallback(() => setRefresh((r) => r + 1), []);

  const { data, isLoading } = useSWR(`/command/overview?r=${refresh}`, fetcher, { refreshInterval: 0 });

  if (isLoading || !data) {
    return (
      <div className="p-8 flex items-center gap-3 text-gray-500">
        <span className="animate-pulse">●●●</span> Loading Command Center...
      </div>
    );
  }

  const { profile, financials, social, next_steps, progress_pct } = data;
  const phase = PHASES[profile.current_phase] || PHASES.build;
  const months = monthsTo100M(financials.mrr_ils);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{profile.business_name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${phase.color}`}>{phase.label}</span>
              <span className="text-gray-500 text-sm">Goal: ₪100M ARR</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-white">{progress_pct}%</p>
            <p className="text-gray-500 text-xs">of ₪100M</p>
          </div>
        </div>

        <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-3">
          <div
            className="h-full bg-gradient-to-r from-indigo-600 to-purple-500 rounded-full transition-all"
            style={{ width: `${Math.min(progress_pct, 100)}%` }}
          />
        </div>

        <div className="grid grid-cols-3 gap-4 mt-4">
          {[
            { label: "Conservative (20%/mo)", months: months.conservative, color: "text-gray-400" },
            { label: "Expected (35%/mo)", months: months.expected, color: "text-indigo-400" },
            { label: "Aggressive (50%/mo)", months: months.aggressive, color: "text-green-400" },
          ].map(({ label, months: m, color }) => (
            <div key={label} className="text-center">
              <p className={`text-xl font-bold ${color}`}>{m >= 999 ? "∞" : m}</p>
              <p className="text-gray-600 text-xs mt-0.5">{label}</p>
            </div>
          ))}
        </div>
        <p className="text-center text-gray-600 text-xs mt-1">months to ₪100M ARR · current MRR: {fmt(financials.mrr_ils)}</p>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FinancialCard data={financials} onSaved={onSaved} />
        <SocialCard data={social} onSaved={onSaved} />
        <VisionPanel
          vision={profile.vision || ""}
          goals={profile.goals || []}
          phase={profile.current_phase || "build"}
          onSaved={onSaved}
        />
      </div>

      {/* AI Next Steps */}
      <NextStepsPanel
        content={next_steps?.content || null}
        stepId={next_steps?.id || null}
        onGenerated={onSaved}
      />

      {/* Quick navigation */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { href: "/team",      icon: "🧠", label: "Advisory Team",   desc: "Get strategic advice" },
          { href: "/crm",       icon: "👥", label: "CRM",             desc: "Manage contacts" },
          { href: "/agents",    icon: "🤖", label: "AI Agents",       desc: "Create content" },
          { href: "/knowledge", icon: "📚", label: "Knowledge Base",  desc: "Upload documents" },
        ].map(({ href, icon, label, desc }) => (
          <a key={href} href={href} className="bg-gray-900 border border-gray-800 hover:border-indigo-700 rounded-xl p-4 transition-colors group">
            <div className="text-2xl mb-2">{icon}</div>
            <p className="text-white text-sm font-medium group-hover:text-indigo-300 transition-colors">{label}</p>
            <p className="text-gray-600 text-xs mt-0.5">{desc}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
