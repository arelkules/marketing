"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Legend } from "recharts";
import { formatCurrency } from "@/lib/utils";

function buildData(currentMrr: number, months: number) {
  const data = [];
  for (let i = 0; i <= months; i++) {
    const conservative = currentMrr * Math.pow(1.20, i) * 12;
    const expected = currentMrr * Math.pow(1.35, i) * 12;
    const aggressive = currentMrr * Math.pow(1.50, i) * 12;
    data.push({
      month: i,
      label: i % 6 === 0 ? `Mo ${i}` : "",
      conservative: Math.round(conservative),
      expected: Math.round(expected),
      aggressive: Math.round(aggressive),
    });
    if (aggressive >= 100_000_000) break;
  }
  return data;
}

const fmt = (v: number) => formatCurrency(v, true);

export default function RevenueChart({ currentMrr }: { currentMrr: number }) {
  const data = buildData(currentMrr || 1000, 60);

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="gc" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#facc15" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#facc15" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="ge" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="label" tick={{ fill: "#6b7280", fontSize: 11 }} />
        <YAxis tickFormatter={fmt} tick={{ fill: "#6b7280", fontSize: 11 }} width={55} />
        <Tooltip
          contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "8px" }}
          formatter={(v: number, name: string) => [fmt(v), name]}
        />
        <ReferenceLine y={100_000_000} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "$100M", fill: "#ef4444", fontSize: 11 }} />
        <Legend wrapperStyle={{ color: "#9ca3af", fontSize: 12 }} />
        <Area type="monotone" dataKey="conservative" name="Conservative (20%)" stroke="#facc15" fill="url(#gc)" strokeWidth={1.5} dot={false} />
        <Area type="monotone" dataKey="expected" name="Expected (35%)" stroke="#60a5fa" fill="url(#ge)" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="aggressive" name="Aggressive (50%)" stroke="#34d399" fill="url(#ga)" strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
