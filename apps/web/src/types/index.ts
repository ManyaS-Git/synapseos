/* ── Identity & Workspace Types ────────────────────────────────────── */

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface Workspace {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  member_count: number;
  project_count: number;
}

export interface WorkspaceMember {
  user_id: string;
  username: string;
  email: string;
  full_name: string | null;
  role: "owner" | "admin" | "member";
  joined_at: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

/* ── API Types ────────────────────────────────────────────────────── */

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

/* ── Auth Types ───────────────────────────────────────────────────── */

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/* ── Health Types ─────────────────────────────────────────────────── */

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  check_duration_ms: number;
  services: Record<string, ServiceHealth>;
}

export interface ServiceHealth {
  status: "healthy" | "unhealthy" | "unavailable";
  host?: string;
  port?: number;
  uri?: string;
  url?: string;
  error?: string;
}

export interface RootResponse {
  name: string;
  version: string;
  docs: string;
  status: string;
}

/* ── Graph Types ──────────────────────────────────────────────────── */

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

/* ── Re-export Memory Types ───────────────────────────────────────── */
export type {
  GraphData,
  GraphNode as MemoryGraphNode,
  Memory,
  MemoryListResponse,
  MemorySearchResponse,
  MemorySearchResult,
} from "./memory";

export { MEMORY_TYPES, MEMORY_TYPE_COLORS } from "./memory";
