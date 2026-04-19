"use client";
import { useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import DealKanban from "@/components/crm/DealKanban";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AddDealForm {
  contact_id: string;
  title: string;
  amount_ils: number;
  stage: string;
  product: string;
  notes: string;
}

const emptyDeal: AddDealForm = {
  contact_id: "", title: "", amount_ils: 0, stage: "new", product: "course", notes: "",
};

export default function DealsPage() {
  const [refresh, setRefresh] = useState(0);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState<AddDealForm>(emptyDeal);
  const [saving, setSaving] = useState(false);

  const { data: deals = {}, isLoading } = useSWR(`/crm/deals?r=${refresh}`, fetcher);
  const { data: contacts = [] } = useSWR(`/crm/contacts`, fetcher);

  const totalWon = (deals["won"] || []).reduce((s: number, d: any) => s + d.amount_ils, 0);
  const totalPipeline = Object.entries(deals)
    .filter(([k]) => !["won", "lost"].includes(k))
    .reduce((s, [, v]: any) => s + v.reduce((ss: number, d: any) => ss + d.amount_ils, 0), 0);

  const addDeal = async () => {
    if (!form.contact_id || !form.title.trim()) return;
    setSaving(true);
    await fetch(`${API}/crm/deals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSaving(false);
    setForm(emptyDeal);
    setShowAdd(false);
    setRefresh((r) => r + 1);
  };

  return (
    <div className="p-6 max-w-full mx-auto">
      <div className="flex items-center justify-between mb-6 max-w-5xl mx-auto">
        <div>
          <div className="flex items-center gap-3">
            <Link href="/crm" className="text-gray-500 hover:text-white text-sm transition-colors">← CRM</Link>
            <h1 className="text-2xl font-bold text-white">Deal Pipeline</h1>
          </div>
          <div className="flex gap-4 mt-1 text-xs text-gray-500">
            <span className="text-green-400">Won: ₪{totalWon.toLocaleString()}</span>
            <span>Pipeline: ₪{totalPipeline.toLocaleString()}</span>
          </div>
        </div>
        <button onClick={() => setShowAdd(true)} className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl font-medium transition-colors">
          + New Deal
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-500 py-8 text-center">Loading deals...</div>
      ) : (
        <DealKanban deals={deals} onMoved={() => setRefresh((r) => r + 1)} />
      )}

      {showAdd && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md space-y-4">
            <h3 className="text-white font-semibold">New Deal</h3>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Contact *</label>
              <select value={form.contact_id} onChange={(e) => setForm({ ...form, contact_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none">
                <option value="">Select contact...</option>
                {contacts.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Deal Title *</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. גבר ללא מגבלות — Full Course"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Amount (₪)</label>
                <input type="number" value={form.amount_ils} onChange={(e) => setForm({ ...form, amount_ils: +e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Product</label>
                <select value={form.product} onChange={(e) => setForm({ ...form, product: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none">
                  {["course", "coaching", "affiliate", "other"].map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Notes</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none resize-none" />
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={addDeal} disabled={saving || !form.contact_id || !form.title.trim()} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold">
                {saving ? "Saving..." : "Create Deal"}
              </button>
              <button onClick={() => setShowAdd(false)} className="px-4 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
