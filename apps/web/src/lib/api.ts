/* ── API Client ────────────────────────────────────────────────────── */

import type {
  LoginRequest,
  RegisterRequest,
  User,
  Workspace,
  Project,
} from "@/types";
import type {
  Memory,
  MemoryCreateRequest,
  MemoryListResponse,
  MemorySearchResponse,
  MemoryUpdateRequest,
  GraphData,
} from "@/types/memory";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(res.status, body.detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/* ── Auth ─────────────────────────────────────────────────────────── */

export const authApi = {
  register: (data: RegisterRequest) =>
    request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginRequest) =>
    request<User>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  logout: () =>
    request<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    }),

  me: () => request<User>("/api/v1/auth/me"),
};

/* ── Users ────────────────────────────────────────────────────────── */

export const usersApi = {
  getProfile: () => request<User>("/api/v1/users/me"),
  updateProfile: (data: { full_name?: string; avatar_url?: string }) =>
    request<User>("/api/v1/users/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};

/* ── Workspaces ───────────────────────────────────────────────────── */

export const workspacesApi = {
  list: () => request<Workspace[]>("/api/v1/workspaces"),
  create: (data: { name: string; description?: string }) =>
    request<Workspace>("/api/v1/workspaces", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  get: (id: string) => request<Workspace>(`/api/v1/workspaces/${id}`),
  update: (id: string, data: { name?: string; description?: string }) =>
    request<Workspace>(`/api/v1/workspaces/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/api/v1/workspaces/${id}`, { method: "DELETE" }),
};

/* ── Projects ─────────────────────────────────────────────────────── */

export const projectsApi = {
  list: (workspaceId: string, includeArchived = false) =>
    request<Project[]>(
      `/api/v1/projects?workspace_id=${workspaceId}&include_archived=${includeArchived}`
    ),
  create: (
    workspaceId: string,
    data: { name: string; description?: string; icon?: string; color?: string }
  ) =>
    request<Project>(`/api/v1/projects?workspace_id=${workspaceId}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  get: (id: string) => request<Project>(`/api/v1/projects/${id}`),
  update: (
    id: string,
    data: { name?: string; description?: string; icon?: string; color?: string; archived?: boolean }
  ) =>
    request<Project>(`/api/v1/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/api/v1/projects/${id}`, { method: "DELETE" }),
};

/* ── Memory ───────────────────────────────────────────────────────── */

export const memoryApi = {
  create: (workspaceId: string, data: MemoryCreateRequest) =>
    request<Memory>(`/api/v1/memory?workspace_id=${workspaceId}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  upload: async (
    workspaceId: string,
    file: File,
    options?: { projectId?: string; memoryType?: string; tags?: string }
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("workspace_id", workspaceId);
    if (options?.projectId) formData.append("project_id", options.projectId);
    if (options?.memoryType) formData.append("memory_type", options.memoryType);
    if (options?.tags) formData.append("tags", options.tags);

    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const response = await fetch(`${API_BASE}/api/v1/memory/upload`, {
      method: "POST",
      credentials: "include",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to upload document");
    }
    return response.json() as Promise<Memory>;
  },

  list: (
    workspaceId: string,
    params: {
      project_id?: string;
      memory_type?: string;
      tags?: string;
      page?: number;
      page_size?: number;
    } = {}
  ) => {
    const query = new URLSearchParams({ workspace_id: workspaceId });
    if (params.project_id) query.set("project_id", params.project_id);
    if (params.memory_type) query.set("memory_type", params.memory_type);
    if (params.tags) query.set("tags", params.tags);
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));
    return request<MemoryListResponse>(`/api/v1/memory?${query}`);
  },

  get: (id: string) => request<Memory>(`/api/v1/memory/${id}`),

  update: (id: string, data: MemoryUpdateRequest) =>
    request<Memory>(`/api/v1/memory/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    request<void>(`/api/v1/memory/${id}`, { method: "DELETE" }),

  search: (data: {
    query: string;
    workspace_id: string;
    project_id?: string;
    memory_type?: string;
    tags?: string[];
    top_k?: number;
    min_importance?: number;
  }) =>
    request<MemorySearchResponse>("/api/v1/memory/search", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  recent: (workspaceId: string, limit = 10) =>
    request<Memory[]>(`/api/v1/memory/recent?workspace_id=${workspaceId}&limit=${limit}`),

  important: (workspaceId: string, limit = 10) =>
    request<Memory[]>(`/api/v1/memory/important?workspace_id=${workspaceId}&limit=${limit}`),

  graph: (workspaceId: string, projectId?: string) => {
    const query = new URLSearchParams({ workspace_id: workspaceId });
    if (projectId) query.set("project_id", projectId);
    return request<GraphData>(`/api/v1/memory/graph?${query}`);
  },
};

/* ── Agent ────────────────────────────────────────────────────────── */

export const agentApi = {
  chat: (data: {
    message: string;
    workspace_id: string;
    project_id?: string | null;
    allow_auto_consequential?: boolean;
  }) =>
    request<import("@/types").AgentChatResponse>("/api/v1/agent/chat", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  approve: (data: {
    session_id: string;
    approved: boolean;
    workspace_id: string;
  }) =>
    request<import("@/types").AgentChatResponse>("/api/v1/agent/approve", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  tools: () =>
    request<import("@/types").AgentToolInfo[]>("/api/v1/agent/tools"),
};

/* ── RAG ──────────────────────────────────────────────────────────── */

export const ragApi = {
  query: (data: {
    query: string;
    workspace_id: string;
    project_id?: string | null;
    top_k?: number;
    min_score?: number;
  }) =>
    request<import("@/types").RAGQueryResponse>("/api/v1/rag/query", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

