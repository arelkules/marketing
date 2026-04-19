"use client";
import { useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import ActivityTimeline from "@/components/crm/ActivityTimeline";
import Link from "next/link";
import { useParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TYPE_STYLES: Record<string, string> = {
  lead:      "bg-yellow-900/50 text-yellow-300",
  student:   "bg-blue-900/50 text-blue-300",
  client:    "bg-purple-900/50 text-purple-300",
  affiliate: "bg-green-900/50 text-green-300",
};

export default function ContactDetail() {
  const { id } = useParams<{ id: string }>();
  const [refresh, setRefresh] = useState(0);
  const [aiText, setAiText] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [logModal, setLogModal] = useState(false);
  const [logForm, setLogForm] = useState({ type: "note", content: "" });
  const [dealModal, setDealModal] = useState(false);
  const [dealForm, setDealForm] = useState({ title: "", amount_ils: 0, product: "course", notes: "" });
  const [saving, setSaving] = useState(false);

  const { data: contact, isLoading } = useSWR(`/crm/contacts/${id}?r=${refresh}`, fetcher);

  const generateAiAction = async () => {
    setAiLoading(true);
    setAiText("");
    const res = await fetch(`${API}/crm/contacts/${id}/ai-action`, { method: "POST" });
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.text) setAiText((prev) => prev + event.text);
        } catch {}
      }
    }
    setAiLoading(false);
  };

  const logActivity = async () => {
    if (!logForm.content.trim()) return;
    setSaving(true);
    await fetch(`${API}/crm/contacts/${id}/activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(logForm),
    });
    setSaving(false);
    setLogModal(false);
    setLogForm({ type: "note", content: "" });
    setRefresh((r) => r + 1);
  };

  const addDeal = async () => {
    if (!dealForm.title.trim()) return;
    setSaving(true);
    await fetch(`${API}/crm/deals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...dealForm, contact_id: id, stage: "new" }),
    });
    setSaving(false);
    setDealModal(false);
    setDealForm({ title: "", amount_ils: 0, product: "course", notes: "" });
    setRefresh((r) => r + 1);
  };

  if (isLoading || !contact) {
    return <div className="p-8 text-gray-500">Loading contact...</div>;
  }

  const tags: string[] = contact.tags || [];

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-5">
      {/* Back */}
      <Link href="/crm" className="text-gray-500 hover:text-white text-sm transition-colors">← Back to CRM</Link>

      {/* Profile header */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-indigo-900/50 flex items-center justify-center text-indigo-300 font-bold text-xl">
              {contact.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">{contact.name}</h1>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_STYLES[contact.type] || "bg-gray-800 text-gray-400"}`}>
                  {contact.type}
                </span>
                <span className="text-gray-500 text-xs">{contact.status}</span>
                {contact.source && <span className="text-gray-500 text-xs">from {contact.source}</span>}
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-white font-bold">
              {contact.total_paid_ils > 0 ? `₪${contact.total_paid_ils.toLocaleString()}` : "₪0"}
            </p>
            <p className="text-gray-500 text-xs">total paid</p>
            <div className="flex items-center gap-1 mt-1 justify-end">
              <div className="h-1.5 w-16 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${contact.lead_score}%` }} />
              </div>
              <span className="text-gray-400 text-xs">{contact.lead_score}/100</span>
            </div>
          </div>
        </div>

        <div className="mt-4 space-y-1.5 text-sm">
          {contact.email && <p className="text-gray-400">✉️ {contact.email}</p>}
          {contact.phone && <p className="text-gray-400">📞 {contact.phone}</p>}
        </div>

        {tags.length > 0 && (
          <div className="flex gap-2 mt-3 flex-wrap">
            {tags.map((t: string) => (
              <span key={t} className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded-full">{t}</span>
            ))}
          </div>
        )}

        {contact.notes && (
          <p className="mt-3 text-gray-500 text-sm italic">{contact.notes}</p>
        )}
      </div>

      {/* AI Suggested Action */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-white font-semibold text-sm flex items-center gap-2">
            <span>🤖</span> AI Suggested Next Action
          </h2>
          <button onClick={generateAiAction} disabled={aiLoading}
            className="text-xs bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-3 py-1.5 rounded-lg transition-colors">
            {aiLoading ? "Thinking..." : "Generate"}
          </button>
        </div>
        {aiText ? (
          <p className="text-gray-200 text-sm leading-relaxed">{aiText}</p>
        ) : aiLoading ? (
          <span className="text-gray-500 text-sm animate-pulse">●●●</span>
        ) : (
          <p className="text-gray-600 text-sm">Click Generate to get a personalized next action for this contact.</p>
        )}
      </div>

      {/* Deals */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-white font-semibold text-sm flex items-center gap-2">
            <span>💼</span> Deals ({contact.deals?.length || 0})
          </h2>
          <button onClick={() => setDealModal(true)} className="text-xs text-indigo-400 hover:text-indigo-300">+ New Deal</button>
        </div>
        {contact.deals?.length > 0 ? (
          <div className="space-y-2">
            {contact.deals.map((d: any) => (
              <div key={d.id} className="flex items-center justify-between bg-gray-800 rounded-xl p-3">
                <div>
                  <p className="text-white text-sm font-medium">{d.title}</p>
                  <p className="text-gray-500 text-xs">{d.product} · {d.stage}</p>
                </div>
                <p className="text-gray-300 text-sm font-medium">₪{d.amount_ils.toLocaleString()}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600 text-sm">No deals yet</p>
        )}
      </div>

      {/* Activity Timeline */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold text-sm flex items-center gap-2">
            <span>📋</span> Activity Timeline
          </h2>
          <button onClick={() => setLogModal(true)} className="text-xs text-indigo-400 hover:text-indigo-300">+ Log Activity</button>
        </div>
        <ActivityTimeline activities={contact.activities || []} />
      </div>

      {/* Log Activity Modal */}
      {logModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-white font-semibold">Log Activity</h3>
            <div>
              <label className="block text-xs text-gray-400 mb-2">Type</label>
              <div className="flex gap-2 flex-wrap">
                {["note", "call", "email", "meeting", "dm", "purchase"].map((t) => (
                  <button key={t} onClick={() => setLogForm({ ...logForm, type: t })}
                    className={`px-3 py-1.5 rounded-lg text-xs capitalize transition-colors ${logForm.type === t ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Notes</label>
              <textarea value={logForm.content} onChange={(e) => setLogForm({ ...logForm, content: e.target.value })} rows={4}
                autoFocus placeholder="What happened?"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 resize-none" />
            </div>
            <div className="flex gap-3">
              <button onClick={logActivity} disabled={saving || !logForm.content.trim()} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold">
                {saving ? "Saving..." : "Save"}
              </button>
              <button onClick={() => setLogModal(false)} className="px-4 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Add Deal Modal */}
      {dealModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-white font-semibold">New Deal</h3>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Title *</label>
              <input value={dealForm.title} onChange={(e) => setDealForm({ ...dealForm, title: e.target.value })}
                placeholder="e.g. גבר ללא מגבלות — Full Course"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Amount (₪)</label>
                <input type="number" value={dealForm.amount_ils} onChange={(e) => setDealForm({ ...dealForm, amount_ils: +e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Product</label>
                <select value={dealForm.product} onChange={(e) => setDealForm({ ...dealForm, product: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none">
                  {["course", "coaching", "affiliate", "other"].map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={addDeal} disabled={saving || !dealForm.title.trim()} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold">
                {saving ? "Saving..." : "Create"}
              </button>
              <button onClick={() => setDealModal(false)} className="px-4 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
