/* ── Agent & RAG Types ─────────────────────────────────────────────── */

export interface AgentStep {
  step_number: number;
  description: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  requires_approval: boolean;
  status: "pending" | "awaiting_approval" | "completed" | "failed" | "skipped";
  output?: Record<string, unknown> | null;
  error?: string | null;
}

export interface AgentPlan {
  goal: string;
  reasoning: string;
  steps: AgentStep[];
  confidence_score: number;
}

export interface ReflectionSummary {
  task_summary: string;
  lessons_learned: string[];
  memory_created_id?: string | null;
  confidence: number;
}

export interface AgentChatRequest {
  message: string;
  workspace_id: string;
  project_id?: string | null;
  allow_auto_consequential?: boolean;
}

export interface AgentChatResponse {
  session_id: string;
  message: string;
  plan: AgentPlan;
  status: "completed" | "awaiting_approval" | "failed";
  pending_step?: AgentStep | null;
  executed_steps: AgentStep[];
  reflection?: ReflectionSummary | null;
  model_used: string;
  latency_ms: number;
}

export interface AgentApprovalRequest {
  session_id: string;
  approved: boolean;
  workspace_id: string;
}

export interface RAGCitation {
  citation_index: number;
  memory_id: string;
  title: string;
  chunk_index: number;
  excerpt: string;
  similarity_score: number;
  memory_type: string;
  source?: string | null;
  source_url?: string | null;
}

export interface RAGQueryRequest {
  query: string;
  workspace_id: string;
  project_id?: string | null;
  top_k?: number;
  min_score?: number;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  citations: RAGCitation[];
  is_unsupported: boolean;
  confidence_score: number;
  model_used: string;
  latency_ms: number;
  provider: string;
}

export interface AgentToolInfo {
  name: string;
  description: string;
  is_consequential: boolean;
  parameters: Record<string, unknown>;
}
