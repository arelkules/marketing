"use client";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STAGES = [
  { id: "new",         label: "New",          color: "border-gray-700" },
  { id: "qualified",   label: "Qualified",    color: "border-blue-800" },
  { id: "proposal",    label: "Proposal",     color: "border-purple-800" },
  { id: "negotiation", label: "Negotiation",  color: "border-yellow-800" },
  { id: "won",         label: "Won ✅",        color: "border-green-700" },
  { id: "lost",        label: "Lost",         color: "border-red-900" },
];

interface Deal {
  id: string;
  contact_id: string;
  title: string;
  amount_ils: number;
  stage: string;
  product: string;
}

interface Props {
  deals: Record<string, Deal[]>;
  onMoved: () => void;
}

export default function DealKanban({ deals, onMoved }: Props) {
  const moveStage = async (dealId: string, stage: string) => {
    await fetch(`${API}/crm/deals/${dealId}/stage`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage }),
    });
    onMoved();
  };

  return (
    <div className="flex gap-3 overflow-x-auto pb-4">
      {STAGES.map((stage) => {
        const stagDeals = deals[stage.id] || [];
        const total = stagDeals.reduce((sum, d) => sum + d.amount_ils, 0);
        return (
          <div key={stage.id} className={`flex-shrink-0 w-52 bg-gray-900 border ${stage.color} rounded-xl p-3`}>
            <div className="mb-3">
              <p className="text-white text-xs font-semibold">{stage.label}</p>
              <p className="text-gray-500 text-xs">{stagDeals.length} deals · {total > 0 ? `₪${(total / 1000).toFixed(0)}K` : "₪0"}</p>
            </div>
            <div className="space-y-2">
              {stagDeals.map((d) => (
                <div key={d.id} className="bg-gray-800 rounded-lg p-3 group">
                  <p className="text-white text-xs font-medium leading-tight">{d.title}</p>
                  <p className="text-gray-400 text-xs mt-1">₪{d.amount_ils.toLocaleString()}</p>
                  <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity flex-wrap">
                    {STAGES.filter((s) => s.id !== stage.id).map((s) => (
                      <button
                        key={s.id}
                        onClick={() => moveStage(d.id, s.id)}
                        className="text-xs text-gray-500 hover:text-white"
                        title={`Move to ${s.label}`}
                      >
                        → {s.label.replace(" ✅", "")}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
