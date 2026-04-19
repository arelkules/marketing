"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PHASES = ["seed", "build", "launch", "scale", "dominate"];

interface Props {
  vision: string;
  goals: string[];
  phase: string;
  onSaved: () => void;
}

export default function VisionPanel({ vision, goals, phase, onSaved }: Props) {
  const [editing, setEditing] = useState(false);
  const [draftVision, setDraftVision] = useState(vision);
  const [draftGoals, setDraftGoals] = useState(goals.join("\n"));
  const [draftPhase, setDraftPhase] = useState(phase || "build");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    await fetch(`${API}/command/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        vision: draftVision,
        goals: draftGoals.split("\n").filter(Boolean),
        current_phase: draftPhase,
      }),
    });
    setSaving(false);
    setEditing(false);
    onSaved();
  };

  if (!editing) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-white font-semibold flex items-center gap-2">
            <span>🎯</span> Vision & Goals
          </h2>
          <button
            onClick={() => { setDraftVision(vision); setDraftGoals(goals.join("\n")); setDraftPhase(phase); setEditing(true); }}
            className="text-xs text-indigo-400 hover:text-indigo-300"
          >
            Edit
          </button>
        </div>
        {vision ? (
          <p className="text-gray-300 text-sm italic mb-3">"{vision}"</p>
        ) : (
          <p className="text-gray-600 text-sm italic mb-3">No vision set yet — click Edit to define your big dream</p>
        )}
        {goals.length > 0 && (
          <ul className="space-y-1">
            {goals.map((g, i) => (
              <li key={i} className="text-gray-400 text-sm flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">▸</span> {g}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-indigo-700 rounded-2xl p-5 space-y-4">
      <h2 className="text-white font-semibold">Edit Vision & Goals</h2>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Your big vision (1-2 sentences)</label>
        <textarea
          value={draftVision}
          onChange={(e) => setDraftVision(e.target.value)}
          rows={3}
          placeholder="e.g. To become the #1 men's personal development brand in Israel, helping 100,000 men become limitless..."
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 resize-none"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Annual goals (one per line)</label>
        <textarea
          value={draftGoals}
          onChange={(e) => setDraftGoals(e.target.value)}
          rows={4}
          placeholder="Reach ₪1M MRR by December 2026&#10;Launch 3 new courses&#10;Build 100K Instagram followers"
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 resize-none"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-2">Current business phase</label>
        <div className="flex gap-2 flex-wrap">
          {PHASES.map((p) => (
            <button
              key={p}
              onClick={() => setDraftPhase(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                draftPhase === p ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>
      <div className="flex gap-3">
        <button onClick={save} disabled={saving} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold transition-colors">
          {saving ? "Saving..." : "Save"}
        </button>
        <button onClick={() => setEditing(false)} className="px-4 py-2.5 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm transition-colors">
          Cancel
        </button>
      </div>
    </div>
  );
}
