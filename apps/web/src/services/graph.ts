/**
 * Graph Service — API client for knowledge graph operations.
 *
 * TODO: Implement the following:
 * - getNodes: Get graph nodes
 * - getEdges: Get graph edges
 * - searchGraph: Search the knowledge graph
 * - getNodeDetails: Get detailed node information
 */

import { apiClient } from '@/lib/api';

export const graphService = {
  async getNodes(filters?: Record<string, unknown>) {
    return apiClient('/api/v1/graph/nodes');
  },

  async getEdges(nodeId: string) {
    return apiClient(`/api/v1/graph/nodes/${nodeId}/edges`);
  },

  async search(query: string) {
    return apiClient(`/api/v1/graph/search?q=${encodeURIComponent(query)}`);
  },
};
