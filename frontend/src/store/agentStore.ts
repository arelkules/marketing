import { create } from "zustand";
import type { AgentType } from "@/lib/types";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentType?: AgentType;
}

interface AgentStore {
  activeAgent: AgentType;
  conversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  setActiveAgent: (agent: AgentType) => void;
  setConversationId: (id: string | null) => void;
  addMessage: (msg: Message) => void;
  appendToLast: (text: string) => void;
  setStreaming: (v: boolean) => void;
  clearConversation: () => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  activeAgent: "copy",
  conversationId: null,
  messages: [],
  isStreaming: false,
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  setConversationId: (id) => set({ conversationId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendToLast: (text) =>
    set((s) => {
      const msgs = [...s.messages];
      if (msgs.length && msgs[msgs.length - 1].role === "assistant") {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: msgs[msgs.length - 1].content + text };
      }
      return { messages: msgs };
    }),
  setStreaming: (v) => set({ isStreaming: v }),
  clearConversation: () => set({ messages: [], conversationId: null }),
}));
