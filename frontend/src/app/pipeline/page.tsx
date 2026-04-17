"use client";
import useSWR from "swr";
import { apiFetch, fetcher } from "@/lib/api";
import type { PipelineBoard, GeneratedAsset } from "@/lib/types";
import { AGENT_LABELS, AGENT_COLORS, STAGE_LABELS, formatDate } from "@/lib/utils";

const STAGES = ["ideas", "draft", "review", "published"] as const;
const STAGE_COLORS: Record<string, string> = {
  ideas: "border-t-gray-500",
  draft: "border-t-yellow-500",
  review: "border-t-blue-500",
  published: "border-t-green-500",
};

export default function PipelinePage() {
  const { data: board, mutate } = useSWR<PipelineBoard>("/pipeline", fetcher);

  const moveStage = async (assetId: string, stage: string) => {
    await apiFetch(`/pipeline/${assetId}/stage?stage=${stage}`, { method: "PATCH" });
    mutate();
  };

  return (
    <div className="p-8 min-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Content Pipeline</h1>
        <p className="text-gray-400 mt-1">Track your content from idea to published</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        {STAGES.map((stage) => {
          const items = board?.[stage] || [];
          return (
            <div key={stage} className={`bg-gray-900 border border-gray-800 border-t-2 ${STAGE_COLORS[stage]} rounded-2xl p-4`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-white">{STAGE_LABELS[stage]}</h2>
                <span className="bg-gray-800 text-gray-400 text-xs px-2 py-1 rounded-full">{items.length}</span>
              </div>
              <div className="space-y-3">
                {items.map((asset) => (
                  <PipelineCard key={asset.id} asset={asset} currentStage={stage} onMove={moveStage} />
                ))}
                {items.length === 0 && (
                  <p className="text-gray-600 text-xs text-center py-8">No items</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PipelineCard({ asset, currentStage, onMove }: { asset: GeneratedAsset; currentStage: string; onMove: (id: string, stage: string) => void }) {
  const stages = ["ideas", "draft", "review", "published", "archived"];
  const currentIdx = stages.indexOf(currentStage);

  return (
    <div className="bg-gray-800 rounded-xl p-3 border border-gray-700 hover:border-gray-600 transition-colors">
      <span className={`text-xs px-2 py-0.5 rounded-full ${AGENT_COLORS[asset.agent_type]}`}>{AGENT_LABELS[asset.agent_type]}</span>
      <p className="text-sm text-white font-medium mt-2 line-clamp-2">{asset.title}</p>
      <p className="text-xs text-gray-500 mt-1">{formatDate(asset.created_at)} · {asset.word_count} words</p>
      <div className="flex gap-1 mt-2">
        {currentIdx > 0 && (
          <button onClick={() => onMove(asset.id, stages[currentIdx - 1])} className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors">← Back</button>
        )}
        {currentIdx < stages.length - 1 && (
          <button onClick={() => onMove(asset.id, stages[currentIdx + 1])} className="text-xs px-2 py-1 bg-indigo-900/50 hover:bg-indigo-800/50 text-indigo-300 rounded-lg transition-colors">Next →</button>
        )}
      </div>
    </div>
  );
}
