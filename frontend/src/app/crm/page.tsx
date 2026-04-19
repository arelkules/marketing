"use client";
import { useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import ContactCard from "@/components/crm/ContactCard";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TYPES = ["all", "lead", "student", "client", "affiliate"];

interface Contact {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  type: string;
  status: string;
  source?: string;
  tags: string[];
  total_paid_ils: number;
  lead_score: number;
}

interface AddForm {
  name: string; phone: string; email: string; type: string;
  source: string; notes: string; lead_score: number;
}

const emptyForm: AddForm = { name: "", phone: "", email: "", type: "lead", source: "", notes: "", lead_score: 0 };

export default function CRMPage() {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState<AddForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [logModal, setLogModal] = useState<string | null>(null);
  const [logForm, setLogForm] = useState({ type: "note", content: "" });
  const [refresh, setRefresh] = useState(0);

  const params = new URLSearchParams();
  if (filter !== "all") params.set("type", filter);
  if (search) params.set("search", search);
  const { data: contacts = [], isLoading } = useSWR<Contact[]>(
    `/crm/contacts?${params}&r=${refresh}`, fetcher
  );
  const { data: stats } = useSWR(`/crm/stats?r=${refresh}`, fetcher);

  const addContact = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    await fetch(`${API}/crm/contacts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, tags: [] }),
    });
    setSaving(false);
    setForm(emptyForm);
    setShowAdd(false);
    setRefresh((r) => r + 1);
  };

  const logActivity = async () => {
    if (!logModal || !logForm.content.trim()) return;
    await fetch(`${API}/crm/contacts/${logModal}/activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(logForm),
    });
    setLogModal(null);
    setLogForm({ type: "note", content: "" });
    setRefresh((r) => r + 1);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>👥</span> CRM
          </h1>
          {stats && (
            <div className="flex gap-4 mt-1 text-xs text-gray-500">
              <span>{stats.by_type.lead} leads</span>
              <span>{stats.by_type.student} students</span>
              <span>{stats.by_type.client} clients</span>
              <span>{stats.by_type.affiliate} affiliates</span>
              {stats.total_revenue_ils > 0 && (
                <span className="text-green-400">₪{stats.total_revenue_ils.toLocaleString()} total revenue</span>
              )}
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Link href="/crm/deals" className="text-sm border border-gray-700 text-gray-400 hover:text-white px-3 py-2 rounded-xl transition-colors">
            Deal Pipeline
          </Link>
          <button
            onClick={() => setShowAdd(true)}
            className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl font-medium transition-colors"
          >
            + Add Contact
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, email, phone..."
          className="flex-1 min-w-48 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
        />
        <div className="flex gap-1">
          {TYPES.map((t) => (
            <button key={t} onClick={() => setFilter(t)}
              className={`px-3 py-2 rounded-xl text-xs font-medium capitalize transition-colors ${filter === t ? "bg-indigo-600 text-white" : "bg-gray-900 border border-gray-700 text-gray-400 hover:text-white"}`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Contact list */}
      {isLoading ? (
        <div className="text-gray-500 py-8 text-center">Loading contacts...</div>
      ) : contacts.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-2">No contacts yet</p>
          <p className="text-gray-600 text-sm">Add your first lead or student to get started</p>
          <button onClick={() => setShowAdd(true)} className="mt-4 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl text-sm font-medium">
            Add Contact
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {contacts.map((c) => (
            <ContactCard key={c.id} contact={c} onLogActivity={(id) => { setLogModal(id); setLogForm({ type: "note", content: "" }); }} />
          ))}
        </div>
      )}

      {/* Add Contact Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-white font-semibold">Add Contact</h3>
            {[
              { key: "name", label: "Name *" },
              { key: "phone", label: "Phone" },
              { key: "email", label: "Email" },
            ].map(({ key, label }) => (
              <div key={key}>
                <label className="block text-xs text-gray-400 mb-1">{label}</label>
                <input value={(form as any)[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500" />
              </div>
            ))}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Type</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none">
                  {["lead", "student", "client", "affiliate"].map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Source</label>
                <select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none">
                  <option value="">Unknown</option>
                  {["instagram", "facebook", "youtube", "referral", "organic", "ads"].map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Lead Score (0-100)</label>
              <input type="number" min={0} max={100} value={form.lead_score} onChange={(e) => setForm({ ...form, lead_score: +e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Notes</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none resize-none" />
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={addContact} disabled={saving || !form.name.trim()} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold">
                {saving ? "Saving..." : "Add Contact"}
              </button>
              <button onClick={() => setShowAdd(false)} className="px-4 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}

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
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${logForm.type === t ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Notes</label>
              <textarea value={logForm.content} onChange={(e) => setLogForm({ ...logForm, content: e.target.value })} rows={4}
                placeholder="What happened?" autoFocus
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 resize-none" />
            </div>
            <div className="flex gap-3">
              <button onClick={logActivity} disabled={!logForm.content.trim()} className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-2.5 rounded-xl text-sm font-semibold">
                Save
              </button>
              <button onClick={() => setLogModal(null)} className="px-4 border border-gray-700 text-gray-400 hover:text-white rounded-xl text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
