"use client";

export type AdvisorId = "hormozi" | "bwnc" | "walker" | "robbins" | "manager";

interface AdvisorConfig {
  name: string;
  title: string;
  icon: string;
  color: string;
  border: string;
  bg: string;
}

const ADVISORS: Record<AdvisorId, AdvisorConfig> = {
  hormozi: {
    name: "Alex Hormozi",
    title: "Offer & Acquisition",
    icon: "💪",
    color: "text-orange-300",
    border: "border-orange-800",
    bg: "bg-orange-950/30",
  },
  bwnc: {
    name: "Tzvika",
    title: "Positioning & Category",
    icon: "🎯",
    color: "text-blue-300",
    border: "border-blue-800",
    bg: "bg-blue-950/30",
  },
  walker: {
    name: "Jeff Walker",
    title: "Launch Formula",
    icon: "🚀",
    color: "text-purple-300",
    border: "border-purple-800",
    bg: "bg-purple-950/30",
  },
  robbins: {
    name: "Tony Robbins",
    title: "RPM & Peak Performance",
    icon: "🔥",
    color: "text-yellow-300",
    border: "border-yellow-700",
    bg: "bg-yellow-950/20",
  },
  manager: {
    name: "Strategic Director",
    title: "Team Consensus",
    icon: "✅",
    color: "text-green-300",
    border: "border-green-700",
    bg: "bg-green-950/30",
  },
};

interface Props {
  advisor: AdvisorId;
  content: string;
  round?: number;
  isLoading?: boolean;
}

export default function AdvisorMessage({ advisor, content, round, isLoading }: Props) {
  const cfg = ADVISORS[advisor];

  return (
    <div className={`rounded-2xl border p-5 ${cfg.bg} ${cfg.border}`}>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{cfg.icon}</span>
        <div>
          <p className={`font-semibold text-sm ${cfg.color}`}>{cfg.name}</p>
          <p className="text-xs text-gray-500">{cfg.title}{round ? ` · Round ${round}` : ""}</p>
        </div>
      </div>
      {isLoading ? (
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <span className="animate-pulse">●●●</span>
          <span>Thinking...</span>
        </div>
      ) : (
        <div className="text-gray-200 text-sm whitespace-pre-wrap leading-relaxed">{content}</div>
      )}
    </div>
  );
}
