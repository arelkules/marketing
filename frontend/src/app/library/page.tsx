"use client";
import { useState } from "react";
import useSWR from "swr";
import { apiFetch, fetcher } from "@/lib/api";
import type { GeneratedAsset } from "@/lib/types";
import { AGENT_LABELS, AGENT_COLORS, STAGE_LABELS, formatDate } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

const AGENT_FILTERS = ["all", "copy", "email", "video", "strategy", "ads"];
const STAGE_FILTERS = ["all", "draft", "review", "published", "archived"];

export default function LibraryPage() {
  const [agentFilter, setAgentFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");
  const [selected, setSelected] = useState<GeneratedAsset | null>(null);

  const params = new URLSearchParams();
  if (agentFilter !== "all") params.set("agent_type", agentFilter);
  if (stageFilter !== "all") params.set("pipeline_stage", stageFilter);

  const { data: assets, mutate } = useSWR<GeneratedAsset[]>(`/assets?${params}`, fetcher);

  const deleteAsset = async (id: string) => {
    await apiFetch(`/assets/${id}`, { method: "DELETE" });
    mutate();
    if (selected?.id === id) setSelected(null);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Asset Library</h1>
        <p className="text-gray-400 mt-1">{assets?.length || 0} saved assets</p>
      </div>

      {/* Filters */}
      <div className="flex gap-6 mb-6">
        <div>
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">Agent</p>
          <div className="flex gap-1.5 flex-wrap">
            {AGENT_FILTERS.map((f) => (
              <button key={f} onClick={() => setAgentFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${agentFilter === f ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                {f === "all" ? "All" : AGENT_LABELS[f]}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">Stage</p>
          <div className="flex gap-1.5 flex-wrap">
            {STAGE_FILTERS.map((f) => (
              <button key={f} onClick={() => setStageFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${stageFilter === f ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                {f === "all" ? "All" : STAGE_LABELS[f]}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {(assets || []).map((asset) => (
          <div key={asset.id} onClick={() => setSelected(asset)} className="bg-gray-900 border border-gray-800 hover:border-gray-600 rounded-2xl p-5 cursor-pointer transition-all group">
            <div className="flex items-start justify-between mb-3">
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${AGENT_COLORS[asset.agent_type]}`}>
                {AGENT_LABELS[asset.agent_type]}
              </span>
              <span className="text-xs text-gray-500">{formatDate(asset.created_at)}</span>
            </div>
            <h3 className="font-semibold text-white text-sm mb-2 line-clamp-2">{asset.title}</h3>
            <p className="text-gray-500 text-xs line-clamp-3 leading-relaxed">{asset.content.slice(0, 150)}...</p>
            <div className="mt-3 flex items-center justify-between">
              <span className={`text-xs px-2 py-0.5 rounded-full border ${
                asset.pipeline_stage === "published" ? "border-green-700 text-green-400" : "border-gray-700 text-gray-500"
              }`}>
                {STAGE_LABELS[asset.pipeline_stage] || asset.pipeline_stage}
              </span>
              <span className="text-xs text-gray-600">{asset.word_count} words</span>
            </div>
          </div>
        ))}
        {assets?.length === 0 && (
          <div className="col-span-3 text-center py-20 text-gray-600">
            <p className="text-4xl mb-3">📁</p>
            <p>No assets yet. Generate content in the Agents tab and save it here.</p>
          </div>
        )}
      </div>

      {selected && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setSelected(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b border-gray-800">
              <div>
                <h3 className="font-bold text-white text-lg">{selected.title}</h3>
                <div className="flex gap-2 mt-1">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full ${AGENT_COLORS[selected.agent_type]}`}>{AGENT_LABELS[selected.agent_type]}</span>
                  {selected.tags.map((t) => <span key={t} className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full">{t}</span>)}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => { navigator.clipboard.writeText(selected.content); }} className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors">Copy</button>
                <button onClick={() => { deleteAsset(selected.id); }} className="text-xs px-3 py-1.5 bg-red-900/40 hover:bg-red-900/60 text-red-400 rounded-lg transition-colors">Delete</button>
                <button onClick={() => setSelected(null)} className="text-xs px-3 py-1.5 bg-gray-800 text-gray-400 rounded-lg transition-colors">Close</button>
              </div>
            </div>
            <div className="overflow-y-auto p-5 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{selected.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
