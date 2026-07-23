/**
 * Memory Service — API client for memory operations.
 *
 * TODO: Implement the following:
 * - getMemories: List all memories with pagination
 * - getMemory: Get a single memory by ID
 * - createMemory: Create a new memory
 * - updateMemory: Update an existing memory
 * - deleteMemory: Delete a memory
 * - searchMemories: Semantic search across memories
 * - getMemoryStats: Get memory statistics
 */

import { apiClient } from '@/lib/api';

// TODO: Define types
// interface Memory { ... }

export const memoryService = {
  // TODO: Implement
  async getAll() {
    return apiClient('/api/v1/memory');
  },

  async getById(id: string) {
    return apiClient(`/api/v1/memory/${id}`);
  },

  async create(data: unknown) {
    return apiClient('/api/v1/memory', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
