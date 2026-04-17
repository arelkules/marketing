export type AgentType = "copy" | "email" | "video" | "strategy" | "ads";

export interface KnowledgeDocument {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: "pending" | "processing" | "completed" | "error";
  chunk_count: number;
  error_msg?: string;
  created_at: string;
}

export interface GeneratedAsset {
  id: string;
  agent_type: AgentType;
  title: string;
  content: string;
  tags: string[];
  pipeline_stage: string;
  word_count?: number;
  created_at: string;
  updated_at: string;
}

export interface AgentConversation {
  id: string;
  agent_type: AgentType;
  title?: string;
}

export interface DashboardSummary {
  latest_mrr: number;
  arr: number;
  months_to_100m_conservative?: number;
  months_to_100m_expected?: number;
  months_to_100m_aggressive?: number;
  total_assets: number;
  total_documents: number;
}

export interface RevenueSnapshot {
  id: string;
  mrr_usd: number;
  notes?: string;
  recorded_at: string;
}

export interface PipelineBoard {
  ideas: GeneratedAsset[];
  draft: GeneratedAsset[];
  review: GeneratedAsset[];
  published: GeneratedAsset[];
  archived: GeneratedAsset[];
}
