import { formatCurrency } from "@/lib/utils";

const MILESTONES = [
  { arr: 100_000, label: "$100K ARR", focus: "Nail one offer. Do things that don't scale. Talk to every customer." },
  { arr: 1_000_000, label: "$1M ARR", focus: "One proven offer, one avatar. Build your first repeatable funnel." },
  { arr: 5_000_000, label: "$5M ARR", focus: "Systematize delivery. Hire for fulfillment. First paid traffic channel." },
  { arr: 10_000_000, label: "$10M ARR", focus: "Second offer. Team building. Organic flywheel + paid at scale." },
  { arr: 50_000_000, label: "$50M ARR", focus: "Horizontal expansion or deeper monetization. Continuity revenue." },
  { arr: 100_000_000, label: "$100M ARR", focus: "Category leader. Multiple offers. Self-sustaining growth engine." },
];

export default function GoalMilestones({ currentArr }: { currentArr: number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
      <h2 className="text-lg font-semibold text-white mb-4">$100M Milestones</h2>
      <div className="space-y-3">
        {MILESTONES.map((m) => {
          const reached = currentArr >= m.arr;
          const isCurrent = !reached && currentArr >= m.arr / 10;
          return (
            <div key={m.arr} className={`flex items-start gap-4 p-4 rounded-xl border transition-all ${
              reached ? "bg-green-950/30 border-green-800" : isCurrent ? "bg-indigo-950/30 border-indigo-800" : "border-gray-800"
            }`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm shrink-0 mt-0.5 ${
                reached ? "bg-green-500 text-white" : isCurrent ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-500"
              }`}>
                {reached ? "✓" : isCurrent ? "→" : "○"}
              </div>
              <div>
                <p className={`font-semibold ${reached ? "text-green-400" : isCurrent ? "text-indigo-300" : "text-gray-400"}`}>{m.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{m.focus}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
