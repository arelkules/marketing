export function formatCurrency(amount: number, compact = false): string {
  if (compact) {
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
    if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(amount);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatMonths(months?: number | null): string {
  if (!months) return "—";
  const years = Math.floor(months / 12);
  const rem = Math.round(months % 12);
  if (years === 0) return `${rem}mo`;
  if (rem === 0) return `${years}yr`;
  return `${years}yr ${rem}mo`;
}

export const AGENT_LABELS: Record<string, string> = {
  copy: "Copy & VSL",
  email: "Email Sequences",
  video: "Video Scripts",
  strategy: "Strategy",
  ads: "Ad Copy",
};

export const AGENT_COLORS: Record<string, string> = {
  copy: "bg-purple-100 text-purple-800",
  email: "bg-blue-100 text-blue-800",
  video: "bg-red-100 text-red-800",
  strategy: "bg-green-100 text-green-800",
  ads: "bg-orange-100 text-orange-800",
};

export const STAGE_LABELS: Record<string, string> = {
  ideas: "Ideas",
  draft: "Draft",
  review: "In Review",
  published: "Published",
  archived: "Archived",
};
