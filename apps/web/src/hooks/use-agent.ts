/* ── Agent & RAG React Query Hooks ─────────────────────────────────── */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { agentService } from "@/services/agent";
import type {
  AgentApprovalRequest,
  AgentChatRequest,
  RAGQueryRequest,
} from "@/types";

export function useAgentTools() {
  return useQuery({
    queryKey: ["agent-tools"],
    queryFn: () => agentService.listTools(),
    staleTime: 1000 * 60 * 10,
  });
}

export function useAgentChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: AgentChatRequest) => agentService.chat(req),
    onSuccess: () => {
      // Refresh memories and projects when agent executes actions
      queryClient.invalidateQueries({ queryKey: ["memories"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useAgentApprove() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: AgentApprovalRequest) => agentService.approveAction(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useRAGQuery() {
  return useMutation({
    mutationFn: (req: RAGQueryRequest) => agentService.queryRAG(req),
  });
}
