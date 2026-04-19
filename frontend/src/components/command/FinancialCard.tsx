"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Fin {
  mrr_ils: number;
  arr_ils: number;
  revenue_ils: number;
  expenses_ils: number;
  net_profit_ils: number;
  active_students: number;
  new_customers: number;
  avg_order_value: number;
  month?: string;
}

interface Props {
  data: Fin;
  onSaved: () => void;
}

function fmt(n: number) {
  if (n >= 1_000_000) return `₪${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `₪${(n / 1_000).toFixed(1)}K`;
  return `₪${n.toLocaleString()}`;
}

export default function FinancialCard({ data, onSaved }: Props) {
  const [open, setOpen] = useState(false);
  const now = new Date();
  const defaultMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  const [form, setForm] = useState({
    month: defaultMonth,
    mrr_ils: data.mrr_ils || 0,
    revenue_ils: data.revenue_ils || 0,
    expenses_ils: data.expenses_ils || 0,
    active_students: data.active_students || 0,
    new_customers: data.new_customers || 0,
    avg_order_value: data.avg_order_value || 0,
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    await fetch(`${API}/command/financial`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSaving(false);
    setOpen(false);
    onSaved();
  };

  return (
    <>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold flex items-center gap-2"><span>💰</span> Financials</h2>
          <button onClick={() => setOpen(true)} className="text-xs text-indigo-400 hover:text-indigo-300">Update</button>
        </div>
        <div className="space-y-2">
          <Row label="MRR" value={fmt(data.mrr_ils)} highlight />
          <Row label="ARR" value={fmt(data.arr_ils)} />
          <Row label="Revenue" value={fmt(data.revenue_ils)} />
          <Row label="Net Profit" value={fmt(data.net_profit_ils)} color={data.net_profit_ils >= 0 ? "text-green-400" : "text-red-400"} />
          <div className="border-t border-gray-800 my-2" />
          <Row label="Students" value={data.active_students.toLocaleString()} />
          <Row label="New customers" value={data.new_customers.toLocaleString()} />
          <Row label="Avg order" value={fmt(data.avg_order_value)} />
        </div>
      </div>

      {open && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md space-y-4">
            <h3 className="text-white font-semibold">Update Financials</h3>
            <Field label="Month (YYYY-MM)" value={form.month} onChange={(v) => setForm({ ...form, month: v })} />
            <Field label="MRR (₪)" type="number" value={form.mrr_ils} onChange={(v) => setForm({ ...form, mrr_ils: +v })} />
            <Field label="Total Revenue (₪)" type="number" value={form.revenue_ils} onChange={(v) => setForm({ ...form, revenue_ils: +v })} />
            <Field label="Total Expenses (₪)" type="number" value={form.expenses_ils} onChange={(v) => setForm({ ...form, expenses_ils: +v })} />
            <Field label="Active Students" type="number" value={form.active_students} onChange={(v) => setForm({ ...form, active_students: +v })} />
            <Field label="New Customers" type="number" value={form.new_customers} onChange={(v) => setForm({ ...form, new_customers: +v })} />
            <Field label="Avg Order Value (₪)" type="number" value={form.avg_order_value} onChange={(v) => setForm({ ...form, avg_order_value: +v })} />
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

function Row({ label, value, highlight, color }: { label: string; value: string; highlight?: boolean; color?: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-500 text-sm">{label}</span>
      <span className={`text-sm font-medium ${color || (highlight ? "text-white text-base" : "text-gray-300")}`}>{value}</span>
    </div>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: any; onChange: (v: string) => void; type?: string }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
      />
    </div>
  );
}
