"use client";
import { useState } from "react";
import AdvisorMessage, { AdvisorId } from "@/components/team/AdvisorMessage";
import ConsensusPanel from "@/components/team/ConsensusPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DiscussionMessage {
  advisor: AdvisorId;
  content: string;
  round: number;
}

type Step = "goal" | "questions" | "discussing" | "consensus";

export default function TeamPage() {
  const [step, setStep] = useState<Step>("goal");
  const [goal, setGoal] = useState("");
  const [businessName] = useState("גבר ללא מגבלות");
  const [sessionId, setSessionId] = useState("");
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [messages, setMessages] = useState<DiscussionMessage[]>([]);
  const [consensus, setConsensus] = useState("");
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [discussing, setDiscussing] = useState(false);
  const [currentRound, setCurrentRound] = useState(0);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState("");

  const startSession = async () => {
    if (!goal.trim()) return;
    setLoadingQuestions(true);
    setError("");
    try {
      const res = await fetch(`${API}/team/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, business_name: businessName }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start session");
      setSessionId(data.session_id);
      setQuestions(data.questions);
      setAnswers(Object.fromEntries(data.questions.map((q: string) => [q, ""])));
      setStep("questions");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const startDiscussion = async () => {
    const unanswered = questions.filter((q) => !answers[q]?.trim());
    if (unanswered.length > 0) {
      setError("Please answer all questions before starting the discussion.");
      return;
    }
    setStep("discussing");
    setDiscussing(true);
    setError("");
    setMessages([]);
    setConsensus("");
    setCurrentRound(0);

    const res = await fetch(`${API}/team/discuss`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, answers }),
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
          const event = JSON.parse(line.slice(6));
          if (event.type === "round1_start") setCurrentRound(1);
          else if (event.type === "round2_start") setCurrentRound(2);
          else if (event.type === "advisor_message") {
            setMessages((prev) => [
              ...prev,
              { advisor: event.advisor as AdvisorId, content: event.content, round: event.round },
            ]);
          } else if (event.type === "consensus") {
            setConsensus(event.content);
            setStep("consensus");
          } else if (event.type === "done") {
            setDiscussing(false);
          }
        } catch {}
      }
    }
    setDiscussing(false);
  };

  const approveConsensus = async (correction?: string) => {
    try {
      await fetch(`${API}/team/sessions/${sessionId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correction: correction || null }),
      });
      setApproved(true);
    } catch {}
  };

  const reset = () => {
    setStep("goal");
    setGoal("");
    setSessionId("");
    setQuestions([]);
    setAnswers({});
    setMessages([]);
    setConsensus("");
    setApproved(false);
    setCurrentRound(0);
    setError("");
  };

  const round1 = messages.filter((m) => m.round === 1);
  const round2 = messages.filter((m) => m.round === 2);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <span>🧠</span> Advisory Team
        </h1>
        <p className="text-gray-400 mt-1">
          Hormozi · Tzvika (BWNC) · Jeff Walker · Tony Robbins — your ₪100M advisory board
        </p>
        <p className="text-indigo-400 text-sm mt-0.5">{businessName}</p>
      </div>

      {error && (
        <div className="mb-4 bg-red-950/40 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Step 1: Goal input */}
      {step === "goal" && (
        <div className="space-y-6">
          <div className="bg-indigo-950/40 border border-indigo-800 rounded-2xl p-5">
            <h2 className="text-indigo-300 font-semibold mb-2">🎯 What do you need?</h2>
            <p className="text-gray-400 text-sm">
              Tell the team your goal. They'll ask clarifying questions, then debate and give you a consensus action plan.
            </p>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Your goal for this session:</label>
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. I need a Facebook ad campaign for my course launch next month"
              rows={4}
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-300 focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          <button
            onClick={startSession}
            disabled={!goal.trim() || loadingQuestions}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-3.5 rounded-xl font-semibold transition-colors"
          >
            {loadingQuestions ? "Preparing questions..." : "🚀 Bring in the advisors"}
          </button>
        </div>
      )}

      {/* Step 2: Clarifying questions */}
      {step === "questions" && (
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-1">
              <span>🎯</span>
              <span className="text-white font-semibold">Goal:</span>
            </div>
            <p className="text-gray-300 text-sm">{goal}</p>
          </div>

          <div>
            <h2 className="text-white font-semibold mb-4">
              The team needs a few details before diving in:
            </h2>
            <div className="space-y-5">
              {questions.map((q, i) => (
                <div key={i}>
                  <label className="block text-sm text-indigo-300 mb-2">
                    {i + 1}. {q}
                  </label>
                  <textarea
                    value={answers[q] || ""}
                    onChange={(e) => setAnswers((prev) => ({ ...prev, [q]: e.target.value }))}
                    placeholder="Your answer..."
                    rows={3}
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-300 focus:outline-none focus:border-indigo-500 resize-none"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={startDiscussion}
              disabled={questions.some((q) => !answers[q]?.trim())}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white py-3.5 rounded-xl font-semibold transition-colors"
            >
              💬 Start the Discussion
            </button>
            <button
              onClick={reset}
              className="px-5 py-3 border border-gray-700 text-gray-400 hover:text-white rounded-xl transition-colors text-sm"
            >
              Back
            </button>
          </div>
        </div>
      )}

      {/* Step 3+: Discussion */}
      {(step === "discussing" || step === "consensus") && (
        <div className="space-y-8">
          {/* Goal recap */}
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-4">
            <p className="text-gray-500 text-xs mb-1">Goal</p>
            <p className="text-white text-sm font-medium">{goal}</p>
          </div>

          {/* Round 1 */}
          {(round1.length > 0 || (discussing && currentRound === 1)) && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px flex-1 bg-gray-800" />
                <span className="text-gray-500 text-xs font-medium uppercase tracking-widest">Round 1 — Independent Views</span>
                <div className="h-px flex-1 bg-gray-800" />
              </div>
              <div className="space-y-4">
                {round1.map((m, i) => (
                  <AdvisorMessage key={i} advisor={m.advisor} content={m.content} round={1} />
                ))}
                {discussing && currentRound === 1 && round1.length < 4 && (
                  <AdvisorMessage
                    advisor={["hormozi", "bwnc", "walker", "robbins"][round1.length] as AdvisorId}
                    content=""
                    round={1}
                    isLoading
                  />
                )}
              </div>
            </div>
          )}

          {/* Round 2 */}
          {(round2.length > 0 || (discussing && currentRound === 2)) && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px flex-1 bg-gray-800" />
                <span className="text-gray-500 text-xs font-medium uppercase tracking-widest">Round 2 — Cross-Discussion</span>
                <div className="h-px flex-1 bg-gray-800" />
              </div>
              <div className="space-y-4">
                {round2.map((m, i) => (
                  <AdvisorMessage key={i} advisor={m.advisor} content={m.content} round={2} />
                ))}
                {discussing && currentRound === 2 && round2.length < 4 && (
                  <AdvisorMessage
                    advisor={["hormozi", "bwnc", "walker", "robbins"][round2.length] as AdvisorId}
                    content=""
                    round={2}
                    isLoading
                  />
                )}
              </div>
            </div>
          )}

          {/* Synthesizing indicator */}
          {discussing && currentRound === 2 && round2.length === 4 && !consensus && (
            <div className="flex items-center gap-3 text-green-400 text-sm">
              <span className="animate-pulse">●●●</span>
              <span>Strategic Director synthesizing consensus...</span>
            </div>
          )}

          {/* Consensus */}
          {consensus && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px flex-1 bg-gray-800" />
                <span className="text-gray-500 text-xs font-medium uppercase tracking-widest">Consensus</span>
                <div className="h-px flex-1 bg-gray-800" />
              </div>
              <ConsensusPanel
                content={consensus}
                onApprove={() => approveConsensus()}
                onCorrect={(c) => approveConsensus(c)}
                approved={approved}
              />
            </div>
          )}

          {/* New session button */}
          {step === "consensus" && !discussing && (
            <button
              onClick={reset}
              className="w-full py-3 border border-gray-700 text-gray-400 hover:text-white rounded-xl transition-colors text-sm"
            >
              Start New Session
            </button>
          )}
        </div>
      )}
    </div>
  );
}
