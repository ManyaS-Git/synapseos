/* ── Authentication Hooks ──────────────────────────────────────────── */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useUser as useClerkUser } from "@clerk/nextjs";
import { authApi, workspacesApi, projectsApi, usersApi, healthApi } from "@/lib/api";
import { useAuthStore } from "@/store";
import { useWorkspaceStore } from "@/store/workspace-store";
import { useProjectStore } from "@/store/project-store";
import type { LoginRequest, RegisterRequest, User, Workspace } from "@/types";

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser } = useAuthStore();
  const clerk = useClerkUser();

  // If clerk user is loaded and signed in, immediately sync user state to store
  useEffect(() => {
    if (clerk.isLoaded && clerk.isSignedIn && clerk.user) {
      const email =
        clerk.user.primaryEmailAddress?.emailAddress || "user@synapseos.ai";
      const fullName =
        clerk.user.fullName ||
        clerk.user.username ||
        email.split("@")[0] ||
        "Synapse User";
      const username = clerk.user.username || email.split("@")[0] || "user";
      const synthUser: User = {
        id: clerk.user.id,
        email,
        username,
        full_name: fullName,
        avatar_url: clerk.user.imageUrl || null,
        email_verified: true,
        is_active: true,
        clerk_user_id: clerk.user.id,
        created_at: clerk.user.createdAt
          ? new Date(clerk.user.createdAt).toISOString()
          : new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
      };
      setUser(synthUser);
    }
  }, [clerk.isLoaded, clerk.isSignedIn, clerk.user, setUser]);

  const { data: currentUser, isLoading: queryLoading, isError } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
    staleTime: 1000 * 60 * 5,
  });

  useEffect(() => {
    if (!queryLoading && currentUser) {
      setUser(currentUser);
    } else if (!queryLoading && isError && !clerk.isSignedIn) {
      setUser(null);
    }
  }, [currentUser, queryLoading, isError, clerk.isSignedIn, setUser]);

  const isClerkAuth = Boolean(clerk.isLoaded && clerk.isSignedIn);
  const effectiveAuth = isAuthenticated || isClerkAuth;
  // If Clerk is loaded and signed in, immediately bypass loading screen
  const effectiveLoading = clerk.isLoaded
    ? clerk.isSignedIn
      ? false
      : isLoading && queryLoading
    : isLoading && queryLoading;

  const fallbackUser: User | null = isClerkAuth && clerk.user
    ? {
        id: clerk.user.id,
        email:
          clerk.user.primaryEmailAddress?.emailAddress ||
          "user@synapseos.ai",
        username:
          clerk.user.username ||
          (clerk.user.primaryEmailAddress?.emailAddress
            ? clerk.user.primaryEmailAddress.emailAddress.split("@")[0]
            : "user"),
        full_name:
          clerk.user.fullName ||
          clerk.user.username ||
          "Synapse User",
        avatar_url: clerk.user.imageUrl || null,
        email_verified: true,
        is_active: true,
        clerk_user_id: clerk.user.id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
      }
    : null;

  return {
    user: user || fallbackUser,
    isAuthenticated: effectiveAuth,
    isLoading: effectiveLoading,
  };
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
    mutationFn: async () => {
      // 1. Sign out of Clerk if active
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const clerk = typeof window !== "undefined" ? (window as any).Clerk : null;
        if (clerk && typeof clerk.signOut === "function") {
          await clerk.signOut();
        }
      } catch {
        // Continue if clerk signOut fails
      }
      // 2. Call backend logout to clear session cookies
      try {
        await authApi.logout();
      } catch {
        // Continue
      }
    },
    onSuccess: () => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
      }
      storeLogout();
      queryClient.clear();
      router.push("/login");
    },
  });
}

/* ── Workspace Hooks ──────────────────────────────────────────────── */

export function useWorkspaces() {
  const { setWorkspaces, currentWorkspace, setCurrentWorkspace } = useWorkspaceStore();

  return useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      try {
        const data = await workspacesApi.list();
        if (data && data.length > 0) {
          setWorkspaces(data);
          if (!currentWorkspace) {
            setCurrentWorkspace(data[0]);
          }
          return data;
        }
      } catch {
        // Backend warming up or network issue
      }
      const fallback: Workspace[] = [
        {
          id: "ws-primary",
          owner_id: "usr-primary",
          name: "Synapse Neural Core",
          slug: "synapse-neural-core",
          description: "Primary neural memory workspace",
          member_count: 1,
          project_count: 3,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];
      setWorkspaces(fallback);
      if (!currentWorkspace) {
        setCurrentWorkspace(fallback[0]);
      }
      return fallback;
    },
    staleTime: 1000 * 60 * 5,
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

/* ── System Health & Profile Hooks ────────────────────────────────── */

export function useHealthReady() {
  return useQuery({
    queryKey: ["healthReady"],
    queryFn: () => healthApi.ready(),
    refetchInterval: 30000,
    staleTime: 10000,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: (data: { full_name?: string; avatar_url?: string }) =>
      usersApi.updateProfile(data),
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      queryClient.setQueryData(["auth", "me"], updatedUser);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}
