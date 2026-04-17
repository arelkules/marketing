"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/agents", label: "AI Agents", icon: "🤖" },
  { href: "/library", label: "Asset Library", icon: "📁" },
  { href: "/pipeline", label: "Pipeline", icon: "🗂️" },
  { href: "/knowledge", label: "Knowledge Base", icon: "🧠" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="p-5 border-b border-gray-800">
        <h1 className="font-bold text-lg text-white leading-tight">Marketing AI</h1>
        <p className="text-xs text-gray-400 mt-0.5">$100M Dashboard</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {NAV.map(({ href, label, icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-indigo-600 text-white font-medium"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`}
            >
              <span className="text-base">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        <p>Powered by Claude</p>
      </div>
    </aside>
  );
}
