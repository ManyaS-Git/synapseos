/* ── Projects Page ─────────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useProjects, useCreateProject } from "@/hooks/use-auth";
import { useWorkspaceStore } from "@/store";
import { Sidebar } from "@/components/sidebar";

export default function ProjectsPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { currentWorkspace } = useWorkspaceStore();
  const { data: projects, isLoading: loadingProjects } = useProjects(
    currentWorkspace?.id || null
  );
  const createProjectMutation = useCreateProject();
  const router = useRouter();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", color: "#6366f1" });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || loadingProjects) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  const handleCreate = () => {
    if (!form.name.trim() || !currentWorkspace) return;
    createProjectMutation.mutate(
      {
        workspaceId: currentWorkspace.id,
        name: form.name,
        description: form.description || undefined,
        color: form.color,
      },
      {
        onSuccess: () => {
          setShowCreate(false);
          setForm({ name: "", description: "", color: "#6366f1" });
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <header className="border-b border-border px-8 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Projects</h1>
            <p className="text-muted-foreground mt-1">
              {currentWorkspace?.name || "No workspace selected"}
            </p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            New Project
          </button>
        </header>

        <div className="px-8 py-6">
          {/* Create Modal */}
          {showCreate && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md shadow-xl">
                <h2 className="text-lg font-semibold text-foreground mb-4">
                  Create Project
                </h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1.5">
                      Name
                    </label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, name: e.target.value }))
                      }
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                      placeholder="My Project"
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1.5">
                      Description
                    </label>
                    <textarea
                      value={form.description}
                      onChange={(e) =>
                        setForm((prev) => ({
                          ...prev,
                          description: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none"
                      placeholder="Optional description"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1.5">
                      Color
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={form.color}
                        onChange={(e) =>
                          setForm((prev) => ({ ...prev, color: e.target.value }))
                        }
                        className="w-8 h-8 rounded cursor-pointer border-0"
                      />
                      <span className="text-sm text-muted-foreground">{form.color}</span>
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      onClick={() => setShowCreate(false)}
                      className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleCreate}
                      disabled={!form.name.trim() || createProjectMutation.isPending}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                      {createProjectMutation.isPending ? "Creating..." : "Create"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Projects Grid */}
          {projects && projects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <div
                  key={project.id}
                  className="bg-card border border-border rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-medium"
                      style={{ backgroundColor: project.color || "#6366f1" }}
                    >
                      {project.name[0]?.toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-medium text-foreground">{project.name}</h3>
                      {project.description && (
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {project.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">
                    Created {new Date(project.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <p className="text-muted-foreground">
                No projects yet. Create your first project to get started.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
