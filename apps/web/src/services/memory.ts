/* ── Memory Service ────────────────────────────────────────────────── */

import { memoryApi } from "@/lib/api";

export const memoryService = {
  getAll: (workspaceId: string, params?: { project_id?: string; memory_type?: string; page?: number; page_size?: number }) =>
    memoryApi.list(workspaceId, params),

  getById: (id: string) => memoryApi.get(id),

  create: (workspaceId: string, data: Parameters<typeof memoryApi.create>[1]) =>
    memoryApi.create(workspaceId, data),

  update: (id: string, data: Parameters<typeof memoryApi.update>[1]) =>
    memoryApi.update(id, data),

  delete: (id: string) => memoryApi.delete(id),

  search: (data: Parameters<typeof memoryApi.search>[0]) =>
    memoryApi.search(data),

  recent: (workspaceId: string, limit?: number) =>
    memoryApi.recent(workspaceId, limit),

  important: (workspaceId: string, limit?: number) =>
    memoryApi.important(workspaceId, limit),

  graph: (workspaceId: string, projectId?: string) =>
    memoryApi.graph(workspaceId, projectId),
};
