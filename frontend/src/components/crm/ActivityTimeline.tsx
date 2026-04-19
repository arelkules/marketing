"use client";

const TYPE_ICONS: Record<string, string> = {
  note: "📝", call: "📞", email: "✉️", meeting: "🤝", dm: "💬", purchase: "💳",
};

interface Activity {
  id: string;
  type: string;
  content: string;
  created_at: string;
}

interface Props {
  activities: Activity[];
}

export default function ActivityTimeline({ activities }: Props) {
  if (activities.length === 0) {
    return <p className="text-gray-600 text-sm py-4 text-center">No activity yet</p>;
  }

  return (
    <div className="space-y-3">
      {activities.map((a) => (
        <div key={a.id} className="flex gap-3">
          <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-sm shrink-0 mt-0.5">
            {TYPE_ICONS[a.type] || "●"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-gray-300 text-sm leading-relaxed">{a.content}</p>
            <p className="text-gray-600 text-xs mt-1">
              {a.type} · {new Date(a.created_at).toLocaleDateString("he-IL", { day: "numeric", month: "short", year: "numeric" })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
