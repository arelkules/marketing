"use client";
import { useState, useRef, useEffect } from "react";
import { useAgentStore } from "@/store/agentStore";
import { streamChat } from "@/lib/api";
import { AGENT_LABELS, AGENT_COLORS } from "@/lib/utils";
import type { AgentType } from "@/lib/types";
import ReactMarkdown from "react-markdown";

const AGENTS: AgentType[] = ["copy", "email", "video", "strategy", "ads"];
const AGENT_ICONS: Record<AgentType, string> = {
  copy: "✍️", email: "📧", video: "🎬", strategy: "📈", ads: "📣"
};

const SUGGESTED_PROMPTS: Record<AgentType, string[]> = {
  copy: ["Write a VSL script for my flagship course", "Create a Grand Slam Offer for my consulting package", "Write 5 headline variations for my landing page", "Write a full sales page for a $5,000 program"],
  email: ["Write a 5-day launch sequence for a new course", "Create a cold subscriber re-engagement sequence", "Write 10 subject line variations for my next broadcast", "Build a 7-email nurture sequence for new leads"],
  video: ["Write a YouTube script: 'How I grew my consulting business to 7 figures'", "Create a 60-second TikTok hook for course creators", "Write a 3-minute VSL for cold Facebook traffic", "Give me 5 YouTube hooks for my niche"],
  strategy: ["Build my value ladder from scratch", "Create a $100M revenue roadmap for my business", "Help me position against my competitors", "Design my offer stack for maximum LTV"],
  ads: ["Write 3 Facebook ad variations for my course launch", "Create Google RSA headlines for my consulting service", "Write a retargeting ad for abandoned checkout", "Create a cold traffic ad for a webinar funnel"],
};

export default function AgentsPage() {
  const { activeAgent, conversationId, messages, isStreaming, setActiveAgent, setConversationId, addMessage, appendToLast, setStreaming, clearConversation } = useAgentStore();
  const [input, setInput] = useState("");
  const [saveModal, setSaveModal] = useState<{ content: string; agentType: AgentType } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || isStreaming) return;
    setInput("");
    setStreaming(true);

    addMessage({ id: crypto.randomUUID(), role: "user", content: msg });
    const assistantId = crypto.randomUUID();
    addMessage({ id: assistantId, role: "assistant", content: "", agentType: activeAgent });

    try {
      await streamChat(
        { message: msg, agent_type: activeAgent, conversation_id: conversationId || undefined },
        (token) => appendToLast(token),
        (meta) => { setConversationId(meta.conversation_id); },
        () => {},
      );
    } catch (e) {
      appendToLast("\n\n[Error: Could not reach the backend. Make sure it is running.]");
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Agent selector */}
      <div className="border-b border-gray-800 bg-gray-900 px-6 py-3">
        <div className="flex items-center gap-2 flex-wrap">
          {AGENTS.map((agent) => (
            <button
              key={agent}
              onClick={() => { setActiveAgent(agent); clearConversation(); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                activeAgent === agent
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
              }`}
            >
              <span>{AGENT_ICONS[agent]}</span>
              {AGENT_LABELS[agent]}
            </button>
          ))}
          {messages.length > 0 && (
            <button onClick={clearConversation} className="ml-auto text-xs text-gray-500 hover:text-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors">
              New chat
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="max-w-2xl mx-auto text-center">
            <div className="text-5xl mb-4">{AGENT_ICONS[activeAgent]}</div>
            <h2 className="text-xl font-semibold text-white mb-2">{AGENT_LABELS[activeAgent]} Agent</h2>
            <p className="text-gray-400 text-sm mb-8">Uses your business knowledge base to generate tailored content.</p>
            <div className="grid grid-cols-1 gap-2 text-left">
              {SUGGESTED_PROMPTS[activeAgent].map((p) => (
                <button key={p} onClick={() => send(p)} className="text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-xl text-sm text-gray-300 hover:text-white transition-colors border border-gray-700">
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-3xl ${msg.role === "user" ? "max-w-xl" : "w-full"}`}>
              {msg.role === "user" ? (
                <div className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm">
                  {msg.content}
                </div>
              ) : (
                <div className="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-sm p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${AGENT_COLORS[msg.agentType || activeAgent]}`}>
                      {AGENT_ICONS[msg.agentType || activeAgent]} {AGENT_LABELS[msg.agentType || activeAgent]}
                    </span>
                  </div>
                  <div className="prose prose-invert prose-sm max-w-none">
                    {msg.content ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      <span className="text-gray-500 animate-pulse">Thinking...</span>
                    )}
                  </div>
                  {msg.content && !isStreaming && i === messages.length - 1 && (
                    <div className="mt-4 pt-3 border-t border-gray-800 flex gap-2">
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(msg.content);
                        }}
                        className="text-xs text-gray-400 hover:text-white px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
                      >
                        Copy
                      </button>
                      <button
                        onClick={() => setSaveModal({ content: msg.content, agentType: msg.agentType || activeAgent })}
                        className="text-xs text-indigo-400 hover:text-indigo-300 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
                      >
                        Save to Library
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 bg-gray-900 px-6 py-4">
        <div className="max-w-4xl mx-auto flex gap-3 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send(); }}
            placeholder={`Ask the ${AGENT_LABELS[activeAgent]} agent...`}
            rows={2}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || isStreaming}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 py-3 rounded-xl font-medium transition-colors text-sm"
          >
            {isStreaming ? "..." : "Send"}
          </button>
        </div>
        <p className="text-center text-xs text-gray-600 mt-2">Cmd+Enter to send</p>
      </div>

      {/* Save modal */}
      {saveModal && <SaveAssetModal {...saveModal} onClose={() => setSaveModal(null)} />}
    </div>
  );
}

function SaveAssetModal({ content, agentType, onClose }: { content: string; agentType: AgentType; onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!title.trim()) return;
    setSaving(true);
    const { apiFetch } = await import("@/lib/api");
    await apiFetch("/assets", {
      method: "POST",
      body: JSON.stringify({
        agent_type: agentType,
        title: title.trim(),
        content,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        pipeline_stage: "draft",
      }),
    });
    setSaving(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-white mb-4">Save to Library</h3>
        <input
          type="text"
          placeholder="Asset title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white text-sm mb-3 focus:outline-none focus:border-indigo-500"
        />
        <input
          type="text"
          placeholder="Tags (comma separated)"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white text-sm mb-4 focus:outline-none focus:border-indigo-500"
        />
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-gray-700 text-gray-400 hover:text-white text-sm transition-colors">Cancel</button>
          <button onClick={save} disabled={!title.trim() || saving} className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium transition-colors">
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
