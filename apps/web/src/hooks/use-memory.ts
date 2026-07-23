/* ── Memory Hooks ──────────────────────────────────────────────────── */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { memoryApi } from "@/lib/api";
import { useWorkspaceStore } from "@/store";
import type {
  MemoryCreateRequest,
  MemoryUpdateRequest,
} from "@/types/memory";

export function useMemories(params: {
  project_id?: string;
  memory_type?: string;
  tags?: string;
  page?: number;
  page_size?: number;
} = {}) {
  const { currentWorkspace } = useWorkspaceStore();

  return useQuery({
    queryKey: ["memories", currentWorkspace?.id, params],
    queryFn: () =>
      memoryApi.list(currentWorkspace!.id, params),
    enabled: !!currentWorkspace,
  });
}

export function useMemory(id: string | null) {
  return useQuery({
    queryKey: ["memory", id],
    queryFn: () => memoryApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateMemory() {
  const queryClient = useQueryClient();
  const { currentWorkspace } = useWorkspaceStore();

  return useMutation({
    mutationFn: (data: MemoryCreateRequest) =>
      memoryApi.create(currentWorkspace!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
    },
  });
}

export function useUpdateMemory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MemoryUpdateRequest }) =>
      memoryApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
      queryClient.invalidateQueries({ queryKey: ["memory", variables.id] });
    },
  });
}

export function useDeleteMemory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => memoryApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
    },
  });
}

export function useMemorySearch(query: string, enabled = false) {
  const { currentWorkspace } = useWorkspaceStore();

  return useQuery({
    queryKey: ["memorySearch", query, currentWorkspace?.id],
    queryFn: () =>
      memoryApi.search({
        query,
        workspace_id: currentWorkspace!.id,
      }),
    enabled: enabled && !!query && !!currentWorkspace,
  });
}

export function useMemoryGraph(projectId?: string) {
  const { currentWorkspace } = useWorkspaceStore();

  return useQuery({
    queryKey: ["memoryGraph", currentWorkspace?.id, projectId],
    queryFn: () => memoryApi.graph(currentWorkspace!.id, projectId),
    enabled: !!currentWorkspace,
  });
}

export function useRecentMemories(limit = 10) {
  const { currentWorkspace } = useWorkspaceStore();

  return useQuery({
    queryKey: ["recentMemories", currentWorkspace?.id, limit],
    queryFn: () => memoryApi.recent(currentWorkspace!.id, limit),
    enabled: !!currentWorkspace,
  });
}

export function useImportantMemories(limit = 10) {
  const { currentWorkspace } = useWorkspaceStore();

  return useQuery({
    queryKey: ["importantMemories", currentWorkspace?.id, limit],
    queryFn: () => memoryApi.important(currentWorkspace!.id, limit),
    enabled: !!currentWorkspace,
  });
}
