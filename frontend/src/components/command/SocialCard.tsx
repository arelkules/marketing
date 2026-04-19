"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PLATFORMS = [
  { id: "instagram", label: "Instagram", icon: "📸" },
  { id: "facebook", label: "Facebook", icon: "👥" },
  { id: "youtube", label: "YouTube", icon: "▶️" },
  { id: "tiktok", label: "TikTok", icon: "🎵" },
  { id: "linkedin", label: "LinkedIn", icon: "💼" },
];

interface SocialData {
  platform: string;
  followers: number;
  posts_count: number;
  avg_engagement_rate: number;
  monthly_reach: number;
}

interface Props {
  data: SocialData[];
  onSaved: () => void;
}

export default function SocialCard({ data, onSaved }: Props) {
  const [open, setOpen] = useState(false);
  const [platform, setPlatform] = useState("instagram");
  const [form, setForm] = useState({ followers: 0, posts_count: 0, avg_engagement_rate: 0, monthly_reach: 0 });
  const [saving, setSaving] = useState(false);

  const openEdit = (p: SocialData) => {
    setPlatform(p.platform);
    setForm({ followers: p.followers, posts_count: p.posts_count, avg_engagement_rate: p.avg_engagement_rate, monthly_reach: p.monthly_reach });
    setOpen(true);
  };

  const save = async () => {
    setSaving(true);
    await fetch(`${API}/command/social`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ platform, ...form }),
    });
    setSaving(false);
    setOpen(false);
    onSaved();
  };

  return (
    <>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold flex items-center gap-2"><span>📱</span> Social Media</h2>
          <button onClick={() => { setPlatform("instagram"); setForm({ followers: 0, posts_count: 0, avg_engagement_rate: 0, monthly_reach: 0 }); setOpen(true); }} className="text-xs text-indigo-400 hover:text-indigo-300">+ Add</button>
        </div>
        {data.length === 0 ? (
          <p className="text-gray-600 text-sm">No platforms added yet</p>
        ) : (
          <div className="space-y-3">
            {data.map((s) => {
              const cfg = PLATFORMS.find((p) => p.id === s.platform);
              return (
                <div key={s.platform} className="flex items-center justify-between group">
                  <div className="flex items-center gap-2">
                    <span>{cfg?.icon || "🌐"}</span>
                    <div>
                      <p className="text-white text-sm font-medium">{s.followers.toLocaleString()}</p>
                      <p className="text-gray-500 text-xs capitalize">{s.platform} · {s.avg_engagement_rate}% eng</p>
                    </div>
                  </div>
                  <button onClick={() => openEdit(s)} className="text-xs text-gray-600 hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">Edit</button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {open && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-white font-semibold">Update Social Metrics</h3>
            <div>
              <label className="block text-xs text-gray-400 mb-2">Platform</label>
              <div className="flex flex-wrap gap-2">
                {PLATFORMS.map((p) => (
                  <button key={p.id} onClick={() => setPlatform(p.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${platform === p.id ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                    {p.icon} {p.label}
                  </button>
                ))}
              </div>
            </div>
            {[
              { key: "followers", label: "Followers" },
              { key: "posts_count", label: "Total Posts" },
              { key: "avg_engagement_rate", label: "Avg Engagement %" },
              { key: "monthly_reach", label: "Monthly Reach" },
            ].map(({ key, label }) => (
              <div key={key}>
                <label className="block text-xs text-gray-400 mb-1">{label}</label>
                <input type="number" value={(form as any)[key]} onChange={(e) => setForm({ ...form, [key]: +e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500" />
              </div>
            ))}
            <div className="flex gap-3 pt-2">
              <button onClick={save} disabled={saving} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold">
                {saving ? "Saving..." : "Save"}
              </button>
              <button onClick={() => setOpen(false)} className="px-4 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
