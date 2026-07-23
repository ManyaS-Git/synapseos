/**
 * API-specific type definitions.
 */

export interface MemoryCreateRequest {
  content: string;
  memoryType: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface MemoryUpdateRequest {
  content?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  importanceScore?: number;
}

export interface MemorySearchRequest {
  query: string;
  limit?: number;
  memoryType?: string;
  minScore?: number;
}

export interface AgentMessageRequest {
  agentId: string;
  message: string;
  conversationId?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  services: Record<string, string>;
}
