"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

interface NotebookInfo {
  id: string;
  title: string;
}

type Step = "install" | "cookies" | "select" | "syncing" | "done";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NotebookLMPage() {
  const [step, setStep] = useState<Step>("install");
  const [cookiesJson, setCookiesJson] = useState("");
  const [cookiesError, setCookiesError] = useState("");
  const [notebooks, setNotebooks] = useState<NotebookInfo[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [syncLog, setSyncLog] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const connect = async () => {
    setCookiesError("");
    let cookies: object[];
    try {
      cookies = JSON.parse(cookiesJson);
      if (!Array.isArray(cookies)) throw new Error("Must be an array");
    } catch {
      setCookiesError("Invalid JSON — paste the full cookie array exported from EditThisCookie");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch<{ notebooks: NotebookInfo[] }>("/notebooklm/list", {
        method: "POST",
        body: JSON.stringify({ cookies }),
      });
      setNotebooks(data.notebooks);
      setSelected(new Set(data.notebooks.map((n) => n.id)));
      setStep("select");
    } catch (e: any) {
      setCookiesError(e.message || "Failed to connect. Check your cookies.");
    } finally {
      setLoading(false);
    }
  };

  const startSync = async () => {
    let cookies: object[];
    try { cookies = JSON.parse(cookiesJson); } catch { return; }
    const notebookIds = Array.from(selected);
    setStep("syncing");
    setSyncLog(["Starting sync..."]);

    const res = await fetch(`${API}/notebooklm/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookies, notebook_ids: notebookIds }),
    });

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6));
          const msg: string = data.message || "";
          setSyncLog((prev) => [...prev, msg]);
          if (msg.startsWith("DONE:")) setStep("done");
        } catch {}
      }
    }
    setStep("done");
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <span>🔗</span> NotebookLM Sync
        </h1>
        <p className="text-gray-400 mt-1">
          חבר את ה-NotebookLM שלך — הסוכנים יקבלו גישה לכל הידע שלך
        </p>
      </div>

      {/* Step 0: Installation */}
      {step === "install" && (
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-5">
            <h2 className="text-white font-semibold mb-4">📦 התקנה</h2>
            <p className="text-gray-400 text-sm mb-4">
              לפני שמתחילים, ודא שחבילת <code className="text-indigo-300 bg-indigo-950/50 px-1.5 py-0.5 rounded">notebooklm-py</code> מותקנת על המחשב שלך.
            </p>

            <div className="space-y-4">
              <div>
                <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">התקנה בסיסית</p>
                <pre className="bg-black/50 border border-gray-800 rounded-xl px-4 py-3 text-sm text-green-300 font-mono overflow-x-auto">
                  pip install notebooklm-py
                </pre>
              </div>

              <div>
                <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">עם תמיכה בהתחברות דרך הדפדפן (נדרש בפעם הראשונה)</p>
                <pre className="bg-black/50 border border-gray-800 rounded-xl px-4 py-3 text-sm text-green-300 font-mono overflow-x-auto">
{`pip install "notebooklm-py[browser]"
playwright install chromium`}
                </pre>
              </div>
            </div>
          </div>

          <button
            onClick={() => setStep("cookies")}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-3.5 rounded-xl font-semibold transition-colors"
          >
            המשך ←
          </button>
        </div>
      )}

      {/* Step 1: Cookies */}
      {step === "cookies" && (
        <div className="space-y-6">
          <div className="bg-indigo-950/40 border border-indigo-800 rounded-2xl p-5">
            <h2 className="text-indigo-300 font-semibold mb-3">📋 איך מוציאים cookies?</h2>
            <ol className="text-gray-300 text-sm space-y-2 list-decimal list-inside">
              <li>פתח Chrome ועבור ל-<strong>notebooklm.google.com</strong></li>
              <li>ודא שאתה מחובר עם חשבון Google שלך</li>
              <li>התקן את תוסף Chrome: <strong>"EditThisCookie"</strong></li>
              <li>לחץ על האייקון של התוסף בזמן שאתה על NotebookLM</li>
              <li>לחץ על <strong>Export</strong> (האייקון של החץ) — מעתיק JSON ללוח</li>
              <li>הדבק כאן 👇</li>
            </ol>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">הדבק כאן את ה-Cookies JSON:</label>
            <textarea
              value={cookiesJson}
              onChange={(e) => setCookiesJson(e.target.value)}
              placeholder='[{"name": "SID", "value": "...", "domain": ".google.com", ...}]'
              rows={8}
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-300 font-mono focus:outline-none focus:border-indigo-500 resize-none"
            />
            {cookiesError && <p className="text-red-400 text-sm mt-2">{cookiesError}</p>}
          </div>

          <button
            onClick={connect}
            disabled={!cookiesJson.trim() || loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-3.5 rounded-xl font-semibold transition-colors"
          >
            {loading ? "מתחבר ל-NotebookLM..." : "🔌 התחבר"}
          </button>
        </div>
      )}

      {/* Step 2: Select notebooks */}
      {step === "select" && (
        <div className="space-y-6">
          <div className="bg-green-950/30 border border-green-800 rounded-2xl p-4 text-green-300 text-sm">
            ✅ התחברת בהצלחה! נמצאו <strong>{notebooks.length}</strong> מחברות
          </div>

          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-white font-semibold">בחר מחברות לייבוא:</h2>
              <button
                onClick={() =>
                  selected.size === notebooks.length
                    ? setSelected(new Set())
                    : setSelected(new Set(notebooks.map((n) => n.id)))
                }
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                {selected.size === notebooks.length ? "בטל הכל" : "בחר הכל"}
              </button>
            </div>
            <div className="space-y-2">
              {notebooks.map((nb) => (
                <label
                  key={nb.id}
                  className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                    selected.has(nb.id)
                      ? "bg-indigo-900/30 border-indigo-600"
                      : "bg-gray-900 border-gray-800 hover:border-gray-600"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selected.has(nb.id)}
                    onChange={(e) => {
                      const next = new Set(selected);
                      e.target.checked ? next.add(nb.id) : next.delete(nb.id);
                      setSelected(next);
                    }}
                    className="w-4 h-4 accent-indigo-500"
                  />
                  <span className="text-white text-sm font-medium">{nb.title}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={startSync}
            disabled={selected.size === 0}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-3.5 rounded-xl font-semibold transition-colors"
          >
            🚀 ייבא {selected.size} מחברות ל-Knowledge Base
          </button>
        </div>
      )}

      {/* Step 3: Syncing */}
      {(step === "syncing" || step === "done") && (
        <div className="space-y-4">
          <div className={`border rounded-2xl p-5 ${step === "done" ? "bg-green-950/30 border-green-800" : "bg-gray-900 border-gray-800"}`}>
            <h2 className="text-white font-semibold mb-4">
              {step === "done" ? "✅ ייבוא הושלם!" : "⏳ מייבא..."}
            </h2>
            <div className="space-y-1.5 font-mono text-sm max-h-72 overflow-y-auto">
              {syncLog.filter((m) => !m.startsWith("DONE:")).map((msg, i) => (
                <p
                  key={i}
                  className={
                    msg.startsWith("✅") ? "text-green-400" :
                    msg.startsWith("✗") || msg.startsWith("ERROR") ? "text-red-400" :
                    msg.startsWith("⚠") ? "text-yellow-400" :
                    "text-gray-300"
                  }
                >
                  {msg}
                </p>
              ))}
            </div>
          </div>

          {step === "done" && (
            <div className="flex gap-3">
              <a
                href="/agents"
                className="flex-1 text-center bg-indigo-600 hover:bg-indigo-500 text-white py-3 rounded-xl font-semibold transition-colors"
              >
                💬 דבר עם הסוכנים עכשיו
              </a>
              <button
                onClick={() => { setStep("cookies"); setSyncLog([]); }}
                className="px-5 py-3 border border-gray-700 text-gray-400 hover:text-white rounded-xl transition-colors text-sm"
              >
                סנכרון נוסף
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
