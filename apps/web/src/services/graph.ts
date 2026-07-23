/* ── Graph Service ─────────────────────────────────────────────────── */

import { memoryApi } from "@/lib/api";

export const graphService = {
  getGraph: (workspaceId: string, projectId?: string) =>
    memoryApi.graph(workspaceId, projectId),
};
