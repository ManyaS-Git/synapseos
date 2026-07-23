/* ── Memory Types ──────────────────────────────────────────────────── */

export interface Memory {
  id: string;
  owner_id: string;
  workspace_id: string;
  project_id: string | null;
  title: string;
  content: string;
  summary: string | null;
  embedding_id: string | null;
  memory_type: string;
  source: string | null;
  source_url: string | null;
  metadata_json: Record<string, unknown> | null;
  importance_score: number;
  confidence: number;
  status: string;
  access_count: number;
  created_at: string;
  updated_at: string;
  accessed_at: string | null;
  tags: string[];
}

export interface MemorySearchResult {
  memory: Memory;
  score: number;
  chunk_content: string | null;
}

export interface MemoryListResponse {
  memories: Memory[];
  total: number;
  page: number;
  page_size: number;
}

export interface MemorySearchResponse {
  results: MemorySearchResult[];
  query: string;
  total: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  memory_type?: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface MemoryCreateRequest {
  title: string;
  content: string;
  summary?: string;
  memory_type?: string;
  project_id?: string;
  source?: string;
  tags?: string[];
  importance_score?: number;
  chunking_strategy?: string;
}

export interface MemoryUpdateRequest {
  title?: string;
  content?: string;
  summary?: string;
  memory_type?: string;
  source?: string;
  tags?: string[];
  importance_score?: number;
  status?: string;
}

/* ── Memory Type Options ──────────────────────────────────────────── */

export const MEMORY_TYPES = [
  { value: "conversation", label: "Conversation" },
  { value: "knowledge", label: "Knowledge" },
  { value: "document", label: "Document" },
  { value: "task", label: "Task" },
  { value: "project", label: "Project" },
  { value: "preference", label: "Preference" },
  { value: "event", label: "Event" },
  { value: "observation", label: "Observation" },
] as const;

export const MEMORY_TYPE_COLORS: Record<string, string> = {
  conversation: "#3b82f6",
  knowledge: "#8b5cf6",
  document: "#10b981",
  task: "#f59e0b",
  project: "#6366f1",
  preference: "#ec4899",
  event: "#ef4444",
  observation: "#06b6d4",
};
