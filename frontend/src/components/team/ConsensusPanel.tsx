"use client";

interface Props {
  content: string;
  onApprove: () => void;
  onCorrect: (correction: string) => void;
  approved: boolean;
}

export default function ConsensusPanel({ content, onApprove, onCorrect, approved }: Props) {
  const handleCorrect = () => {
    const correction = window.prompt("What would you change or add to this consensus?");
    if (correction?.trim()) onCorrect(correction.trim());
  };

  return (
    <div className="rounded-2xl border border-green-700 bg-green-950/30 p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">✅</span>
        <h3 className="text-green-300 font-bold text-lg">Team Consensus</h3>
      </div>

      <div className="text-gray-200 text-sm whitespace-pre-wrap leading-relaxed mb-6">
        {content}
      </div>

      {!approved ? (
        <div className="flex gap-3">
          <button
            onClick={onApprove}
            className="flex-1 bg-green-700 hover:bg-green-600 text-white py-3 rounded-xl font-semibold transition-colors text-sm"
          >
            ✅ Approve & Save to Memory
          </button>
          <button
            onClick={handleCorrect}
            className="px-5 py-3 border border-gray-700 text-gray-400 hover:text-white rounded-xl transition-colors text-sm"
          >
            ✏️ Add Correction
          </button>
        </div>
      ) : (
        <div className="text-center text-green-400 text-sm font-medium py-2">
          ✅ Saved to team memory — advisors will remember this in future sessions
        </div>
      )}
    </div>
  );
}
