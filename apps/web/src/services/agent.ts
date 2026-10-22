/* ── Agent & RAG Service ────────────────────────────────────────────── */

import { agentApi, ragApi } from "@/lib/api";
import type {
  AgentApprovalRequest,
  AgentChatRequest,
  AgentChatResponse,
  AgentToolInfo,
  RAGQueryRequest,
  RAGQueryResponse,
} from "@/types";

export const agentService = {
  chat: async (req: AgentChatRequest): Promise<AgentChatResponse> => {
    return agentApi.chat(req);
  },

  approveAction: async (req: AgentApprovalRequest): Promise<AgentChatResponse> => {
    return agentApi.approve(req);
  },

  listTools: async (): Promise<AgentToolInfo[]> => {
    return agentApi.tools();
  },

  queryRAG: async (req: RAGQueryRequest): Promise<RAGQueryResponse> => {
    return ragApi.query(req);
  },
};
