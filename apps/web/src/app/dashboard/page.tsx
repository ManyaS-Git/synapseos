/* ── Dashboard Page ────────────────────────────────────────────────── */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { useWorkspaces } from "@/hooks/use-auth";
import { useWorkspaceStore } from "@/store";
import { Sidebar } from "@/components/sidebar";

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { data: workspaces, isLoading: loadingWorkspaces } = useWorkspaces();
  const { setCurrentWorkspace, currentWorkspace } = useWorkspaceStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (workspaces && workspaces.length > 0 && !currentWorkspace) {
      setCurrentWorkspace(workspaces[0]);
    }
  }, [workspaces, currentWorkspace, setCurrentWorkspace]);

  if (isLoading || loadingWorkspaces) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="border-b border-border px-8 py-6">
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back, {user.full_name || user.username}
          </p>
        </header>

        <div className="px-8 py-6 space-y-8">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-card border border-border rounded-xl p-5">
              <p className="text-sm text-muted-foreground">Workspaces</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {workspaces?.length || 0}
              </p>
            </div>
            <div className="bg-card border border-border rounded-xl p-5">
              <p className="text-sm text-muted-foreground">Projects</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {currentWorkspace?.project_count || 0}
              </p>
            </div>
            <div className="bg-card border border-border rounded-xl p-5">
              <p className="text-sm text-muted-foreground">Status</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <p className="text-lg font-medium text-foreground">Active</p>
              </div>
            </div>
          </div>

          {/* Placeholder Cards for Future Features */}
          <div>
            <h2 className="text-lg font-semibold text-foreground mb-4">Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <PlaceholderCard
                title="Memory"
                description="Long-term memory engine for persistent knowledge"
                icon="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                status="Active"
                href="/memory"
              />
              <PlaceholderCard
                title="Agents"
                description="Multi-agent AI system for autonomous tasks"
                icon="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                status="Coming soon"
              />
              <PlaceholderCard
                title="Knowledge Graph"
                description="Structured relationship mapping across all data"
                icon="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                status="Coming soon"
              />
              <PlaceholderCard
                title="RAG"
                description="Retrieval-augmented generation for accurate responses"
                icon="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                status="Coming soon"
              />
              <PlaceholderCard
                title="Reflection"
                description="Self-improving memory optimization and compression"
                icon="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                status="Coming soon"
              />
              <PlaceholderCard
                title="Connectors"
                description="External data ingestion from files, web, and apps"
                icon="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                status="Coming soon"
              />
            </div>
          </div>

          {/* Current Workspace Projects */}
          {currentWorkspace && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Projects in {currentWorkspace.name}
              </h2>
              <div className="bg-card border border-border rounded-xl p-8 text-center">
                <p className="text-muted-foreground">
                  {currentWorkspace.project_count === 0
                    ? "No projects yet. Create your first project to get started."
                    : `${currentWorkspace.project_count} project(s) in this workspace.`}
                </p>
                <button
                  onClick={() => router.push("/projects")}
                  className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  {currentWorkspace.project_count === 0
                    ? "Create Project"
                    : "View Projects"}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function PlaceholderCard({
  title,
  description,
  icon,
  status,
  href,
}: {
  title: string;
  description: string;
  icon: string;
  status: string;
  href?: string;
}) {
  const Wrapper = href ? Link : "div";
  return (
    <Wrapper
      href={href || "#"}
      className={`bg-card border border-border rounded-xl p-5 transition-opacity ${
        href
          ? "hover:shadow-md cursor-pointer opacity-90 hover:opacity-100"
          : "opacity-70 hover:opacity-100 cursor-not-allowed"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
          <svg
            className="w-5 h-5 text-muted-foreground"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d={icon}
            />
          </svg>
        </div>
        <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full text-muted-foreground font-medium">
          {status}
        </span>
      </div>
      <h3 className="font-medium text-foreground mt-3">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1">{description}</p>
    </Wrapper>
  );
}
