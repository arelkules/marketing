"use client";
import Link from "next/link";

const TYPE_STYLES: Record<string, string> = {
  lead:      "bg-yellow-900/50 text-yellow-300",
  student:   "bg-blue-900/50 text-blue-300",
  client:    "bg-purple-900/50 text-purple-300",
  affiliate: "bg-green-900/50 text-green-300",
};

const SOURCE_ICONS: Record<string, string> = {
  instagram: "📸", facebook: "👥", youtube: "▶️", referral: "🤝", organic: "🌱", ads: "📣",
};

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

interface Props {
  contact: Contact;
  onLogActivity: (id: string) => void;
}

export default function ContactCard({ contact, onLogActivity }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl p-4 flex items-center justify-between transition-colors group">
      <div className="flex items-center gap-4 min-w-0">
        <div className="w-10 h-10 rounded-full bg-indigo-900/50 flex items-center justify-center text-indigo-300 font-bold text-sm shrink-0">
          {contact.name.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-white text-sm font-medium">{contact.name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_STYLES[contact.type] || "bg-gray-800 text-gray-400"}`}>
              {contact.type}
            </span>
            {contact.source && <span className="text-sm" title={contact.source}>{SOURCE_ICONS[contact.source] || "🌐"}</span>}
          </div>
          <p className="text-gray-500 text-xs mt-0.5 truncate">
            {contact.email || contact.phone || "No contact info"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 shrink-0 ml-4">
        <div className="text-right hidden sm:block">
          <p className="text-gray-300 text-sm">
            {contact.total_paid_ils > 0 ? `₪${contact.total_paid_ils.toLocaleString()}` : "—"}
          </p>
          <div className="flex items-center gap-1 justify-end mt-0.5">
            <div className="h-1.5 w-12 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${contact.lead_score}%` }} />
            </div>
            <span className="text-gray-600 text-xs">{contact.lead_score}</span>
          </div>
        </div>

        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onLogActivity(contact.id)}
            className="text-xs text-gray-400 hover:text-white border border-gray-700 hover:border-gray-600 px-2 py-1 rounded-lg transition-colors"
          >
            Log
          </button>
          <Link
            href={`/crm/${contact.id}`}
            className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-900 hover:border-indigo-700 px-2 py-1 rounded-lg transition-colors"
          >
            View
          </Link>
        </div>
      </div>
    </div>
  );
}
