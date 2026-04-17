"use client";
import { useState, useEffect } from "react";
import useSWR from "swr";
import { apiFetch, fetcher } from "@/lib/api";
import type { DashboardSummary, RevenueSnapshot } from "@/lib/types";
import { formatCurrency, formatMonths } from "@/lib/utils";
import RevenueChart from "@/components/dashboard/RevenueChart";
import GoalMilestones from "@/components/dashboard/GoalMilestones";

export default function DashboardPage() {
  const { data: summary, mutate } = useSWR<DashboardSummary>("/metrics/dashboard", fetcher);
  const [mrr, setMrr] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (summary?.latest_mrr) setMrr(String(summary.latest_mrr));
  }, [summary?.latest_mrr]);

  const saveMrr = async () => {
    const val = parseFloat(mrr);
    if (isNaN(val)) return;
    setSaving(true);
    await apiFetch("/metrics/revenue", { method: "POST", body: JSON.stringify({ mrr_usd: val }) });
    await mutate();
    setSaving(false);
  };

  const arr = (summary?.latest_mrr || 0) * 12;
  const progress = Math.min(100, (arr / 100_000_000) * 100);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">$100M Dashboard</h1>
        <p className="text-gray-400 mt-1">Track your revenue journey and business health</p>
      </div>

      {/* MRR Input */}
      <div className="bg-gray-900 rounded-2xl p-6 mb-6 border border-gray-800">
        <label className="block text-sm text-gray-400 mb-2">Current Monthly Recurring Revenue (MRR)</label>
        <div className="flex gap-3 items-center">
          <div className="relative flex-1 max-w-xs">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 font-medium">$</span>
            <input
              type="number"
              value={mrr}
              onChange={(e) => setMrr(e.target.value)}
              placeholder="0"
              className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-8 pr-4 py-3 text-white text-xl font-bold focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            onClick={saveMrr}
            disabled={saving}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-5 py-3 rounded-xl font-medium transition-colors"
          >
            {saving ? "Saving..." : "Update"}
          </button>
          {arr > 0 && (
            <div className="text-gray-300">
              <span className="text-gray-500 text-sm">ARR: </span>
              <span className="font-bold text-green-400 text-lg">{formatCurrency(arr, true)}</span>
            </div>
          )}
        </div>

        {/* Progress to $100M */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1.5">
            <span>{formatCurrency(arr, true)} ARR</span>
            <span>$100M target</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-green-400 rounded-full transition-all duration-700"
              style={{ width: `${Math.max(0.5, progress)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{progress.toFixed(4)}% of the way there</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        {[
          { label: "Conservative path", value: formatMonths(summary?.months_to_100m_conservative), sub: "20% MoM growth", color: "text-yellow-400" },
          { label: "Expected path", value: formatMonths(summary?.months_to_100m_expected), sub: "35% MoM growth", color: "text-blue-400" },
          { label: "Aggressive path", value: formatMonths(summary?.months_to_100m_aggressive), sub: "50% MoM growth", color: "text-green-400" },
          { label: "Total assets saved", value: String(summary?.total_assets || 0), sub: "copy, scripts, emails", color: "text-purple-400" },
          { label: "Knowledge docs", value: String(summary?.total_documents || 0), sub: "ingested files", color: "text-indigo-400" },
          { label: "ARR", value: formatCurrency(arr, true), sub: "annualized", color: "text-emerald-400" },
        ].map((m) => (
          <div key={m.label} className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">{m.label}</p>
            <p className={`text-2xl font-bold ${m.color}`}>{m.value}</p>
            <p className="text-xs text-gray-600 mt-0.5">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Revenue Projection Chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Revenue Projection to $100M ARR</h2>
        <RevenueChart currentMrr={summary?.latest_mrr || 0} />
      </div>

      {/* Milestones */}
      <GoalMilestones currentArr={arr} />
    </div>
  );
}
