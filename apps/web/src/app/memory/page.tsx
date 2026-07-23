/* ── Memory List Page ──────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useMemories, useDeleteMemory } from "@/hooks/use-memory";
import { useWorkspaceStore } from "@/store";
import { Sidebar } from "@/components/sidebar";
import { MEMORY_TYPE_COLORS } from "@/types/memory";

export default function MemoryListPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { currentWorkspace } = useWorkspaceStore();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const deleteMutation = useDeleteMemory();

  const { data, isLoading: loadingMemories } = useMemories({
    memory_type: typeFilter || undefined,
    page,
    page_size: 20,
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || loadingMemories) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading memories...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  const handleDelete = (id: string) => {
    if (confirm("Delete this memory?")) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <header className="border-b border-border px-8 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Memories</h1>
            <p className="text-muted-foreground mt-1">
              {data?.total || 0} memories in {currentWorkspace?.name}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
              className="px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground"
            >
              <option value="">All types</option>
              <option value="conversation">Conversation</option>
              <option value="knowledge">Knowledge</option>
              <option value="document">Document</option>
              <option value="task">Task</option>
              <option value="project">Project</option>
              <option value="preference">Preference</option>
              <option value="event">Event</option>
              <option value="observation">Observation</option>
            </select>
            <button
              onClick={() => router.push("/memory/create")}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              New Memory
            </button>
          </div>
        </header>

        <div className="px-8 py-6">
          {data?.memories && data.memories.length > 0 ? (
            <>
              <div className="space-y-3">
                {data.memories.map((memory) => (
                  <div
                    key={memory.id}
                    className="bg-card border border-border rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => router.push(`/memory/${memory.id}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: MEMORY_TYPE_COLORS[memory.memory_type] || "#6b7280" }}
                          />
                          <span className="text-xs text-muted-foreground capitalize">
                            {memory.memory_type}
                          </span>
                          {memory.project_id && (
                            <span className="text-xs text-muted-foreground">• Project</span>
                          )}
                        </div>
                        <h3 className="font-medium text-foreground truncate">{memory.title}</h3>
                        <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                          {memory.content}
                        </p>
                        <div className="flex items-center gap-4 mt-2">
                          <span className="text-xs text-muted-foreground">
                            {new Date(memory.created_at).toLocaleDateString()}
                          </span>
                          {memory.tags.length > 0 && (
                            <div className="flex gap-1">
                              {memory.tags.slice(0, 3).map((tag) => (
                                <span key={tag} className="text-xs bg-muted px-1.5 py-0.5 rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                          <span className="text-xs text-muted-foreground">
                            Score: {(memory.importance_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(memory.id); }}
                        className="p-1.5 text-muted-foreground hover:text-destructive rounded-lg hover:bg-muted transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {data.total > 20 && (
                <div className="flex justify-center gap-2 mt-6">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 text-sm border border-border rounded-lg disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1.5 text-sm text-muted-foreground">
                    Page {page} of {Math.ceil(data.total / 20)}
                  </span>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page * 20 >= data.total}
                    className="px-3 py-1.5 text-sm border border-border rounded-lg disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-16">
              <p className="text-muted-foreground">No memories yet. Create your first memory.</p>
              <button
                onClick={() => router.push("/memory/create")}
                className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
              >
                Create Memory
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
