/**
 * Agent Service — API client for agent operations.
 *
 * TODO: Implement the following:
 * - sendMessage: Send a message to an agent
 * - getAgentStatus: Get agent status
 * - listAgents: List all available agents
 * - streamResponse: Stream agent responses via WebSocket
 */

import { apiClient } from '@/lib/api';

export const agentService = {
  async sendMessage(agentId: string, message: string) {
    return apiClient('/api/v1/agents/message', {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, message }),
    });
  },

  async getStatus(agentId: string) {
    return apiClient(`/api/v1/agents/${agentId}/status`);
  },

  async list() {
    return apiClient('/api/v1/agents');
  },
};
