/* ── Authentication API ────────────────────────────────────────────── */

import type {
  LoginRequest,
  RegisterRequest,
  User,
  Workspace,
  Project,
} from "@/types";

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
    request<void>(`/api/v1/workspaces/${id}`, {
      method: "DELETE",
    }),
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
    data: {
      name?: string;
      description?: string;
      icon?: string;
      color?: string;
      archived?: boolean;
    }
  ) =>
    request<Project>(`/api/v1/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    request<void>(`/api/v1/projects/${id}`, {
      method: "DELETE",
    }),
};
