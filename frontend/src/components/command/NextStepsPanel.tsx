"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Props {
  content: string | null;
  stepId: string | null;
  onGenerated: () => void;
}

export default function NextStepsPanel({ content, stepId, onGenerated }: Props) {
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [currentId, setCurrentId] = useState<string | null>(stepId);
  const [marking, setMarking] = useState(false);
  const [done, setDone] = useState(false);

  const generate = async () => {
    setStreaming(true);
    setStreamText("");
    setDone(false);

    const res = await fetch(`${API}/command/generate-next-steps`, { method: "POST" });
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done: streamDone, value } = await reader.read();
      if (streamDone) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "token") setStreamText((prev) => prev + event.text);
          if (event.type === "done") { setCurrentId(event.id); onGenerated(); }
        } catch {}
      }
    }
    setStreaming(false);
  };

  const markDone = async () => {
    if (!currentId) return;
    setMarking(true);
    await fetch(`${API}/command/next-steps/${currentId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "done" }),
    });
    setMarking(false);
    setDone(true);
  };

  const displayContent = streamText || content;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-semibold flex items-center gap-2">
          <span>🤖</span> AI Next Steps — This Week
        </h2>
        <button
          onClick={generate}
          disabled={streaming}
          className="text-xs bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-3 py-1.5 rounded-lg transition-colors"
        >
          {streaming ? "Generating..." : "Generate New"}
        </button>
      </div>

      {streaming && !streamText && (
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <span className="animate-pulse">●●●</span>
          <span>Analyzing your business data...</span>
        </div>
      )}

      {displayContent ? (
        <>
          <div className="text-gray-200 text-sm whitespace-pre-wrap leading-relaxed">
            {displayContent}
          </div>
          {!streaming && currentId && !done && (
            <button
              onClick={markDone}
              disabled={marking}
              className="mt-4 text-xs text-green-400 hover:text-green-300 border border-green-900 px-3 py-1.5 rounded-lg transition-colors"
            >
              {marking ? "Saving..." : "✅ Mark as Done"}
            </button>
          )}
          {done && <p className="mt-3 text-green-400 text-xs">✅ Marked as done</p>}
        </>
      ) : (
        !streaming && (
          <p className="text-gray-600 text-sm">
            No action plan yet. Update your financials and social metrics, then click Generate New.
          </p>
        )
      )}
    </div>
  );
}
