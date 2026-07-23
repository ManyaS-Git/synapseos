/**
 * Custom hook for agent operations.
 *
 * TODO: Implement:
 * - useAgents: Query hook for agent list
 * - useAgentStatus: Query hook for agent status
 * - useSendMessage: Mutation hook for sending messages
 */

import { useQuery } from '@tanstack/react-query';
import { agentService } from '@/services/agent';

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => agentService.list(),
  });
}
