/**
 * @synapseos/types — Shared Type Definitions
 *
 * TypeScript types shared across all packages and applications.
 *
 * TODO: Export all shared types:
 * - Memory types
 * - Agent types
 * - Graph types
 * - API types
 * - Configuration types
 */

// ============================================================================
// Memory Types
// ============================================================================

export type MemoryType = 'episodic' | 'semantic' | 'procedural';

export interface Memory {
  id: string;
  userId: string;
  content: string;
  memoryType: MemoryType;
  tags: string[];
  embeddingId?: string;
  importanceScore: number;
  accessCount: number;
  createdAt: string;
  updatedAt: string;
  lastAccessedAt?: string;
  metadata: Record<string, unknown>;
}

export interface MemoryCluster {
  id: string;
  name: string;
  description: string;
  memoryIds: string[];
  createdAt: string;
}

// ============================================================================
// Agent Types
// ============================================================================

export type AgentType =
  | 'executive'
  | 'memory'
  | 'research'
  | 'planning'
  | 'communication'
  | 'coding'
  | 'reflection'
  | 'router';

export type AgentStatus = 'idle' | 'busy' | 'offline' | 'error';

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  description: string;
  capabilities: string[];
}

export interface AgentMessage {
  id: string;
  agentId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

// ============================================================================
// Graph Types
// ============================================================================

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  properties: Record<string, unknown>;
}

// ============================================================================
// API Types
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
  path: string;
}
