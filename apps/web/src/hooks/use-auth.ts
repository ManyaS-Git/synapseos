/* ── Authentication Hooks ──────────────────────────────────────────── */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi, workspacesApi, projectsApi } from "@/lib/api";
import { useAuthStore } from "@/store";
import { useWorkspaceStore } from "@/store/workspace-store";
import { useProjectStore } from "@/store/project-store";
import type { LoginRequest, RegisterRequest } from "@/types";

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser } =
    useAuthStore();

  const { data: currentUser } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
    enabled: !isLoading,
  });

  useEffect(() => {
    if (!isLoading && currentUser) {
      setUser(currentUser);
    } else if (!isLoading && !currentUser) {
      setUser(null);
    }
  }, [currentUser, isLoading, setUser]);

  return { user, isAuthenticated, isLoading };
}

export function useLogin() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (user) => {
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      router.push("/dashboard");
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: (user) => {
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      router.push("/dashboard");
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const { logout: storeLogout } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      storeLogout();
      queryClient.clear();
      router.push("/login");
    },
  });
}

/* ── Workspace Hooks ──────────────────────────────────────────────── */

export function useWorkspaces() {
  const { setWorkspaces } = useWorkspaceStore();

  return useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const data = await workspacesApi.list();
      setWorkspaces(data);
      return data;
    },
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      workspacesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
  });
}

/* ── Project Hooks ────────────────────────────────────────────────── */

export function useProjects(workspaceId: string | null) {
  const { setProjects } = useProjectStore();

  return useQuery({
    queryKey: ["projects", workspaceId],
    queryFn: async () => {
      if (!workspaceId) return [];
      const data = await projectsApi.list(workspaceId);
      setProjects(data);
      return data;
    },
    enabled: !!workspaceId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      ...data
    }: {
      workspaceId: string;
      name: string;
      description?: string;
      icon?: string;
      color?: string;
    }) => projectsApi.create(workspaceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", variables.workspaceId],
      });
    },
  });
}
