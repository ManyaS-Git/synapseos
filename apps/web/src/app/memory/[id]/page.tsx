/* ── Memory Detail Page ────────────────────────────────────────────── */

"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useMemory, useDeleteMemory } from "@/hooks/use-memory";
import { Sidebar } from "@/components/sidebar";
import { MEMORY_TYPE_COLORS } from "@/types/memory";

export default function MemoryDetailPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const memoryId = params.id as string;
  const { data: memory, isLoading: loadingMemory } = useMemory(memoryId);
  const deleteMutation = useDeleteMemory();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || loadingMemory) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading memory...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user || !memory) return null;

  const handleDelete = () => {
    if (confirm("Delete this memory?")) {
      deleteMutation.mutate(memory.id, {
        onSuccess: () => router.push("/memory"),
      });
    }
  };

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <header className="border-b border-border px-8 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="p-1.5 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{memory.title}</h1>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: MEMORY_TYPE_COLORS[memory.memory_type] || "#6b7280" }}
                />
                <span className="text-sm text-muted-foreground capitalize">{memory.memory_type}</span>
              </div>
            </div>
          </div>
          <button
            onClick={handleDelete}
            className="px-4 py-2 text-sm text-destructive border border-destructive/30 rounded-lg hover:bg-destructive/10 transition-colors"
          >
            Delete
          </button>
        </header>

        <div className="px-8 py-6 max-w-3xl space-y-6">
          {/* Content */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-sm font-medium text-muted-foreground mb-3">Content</h2>
            <div className="text-foreground whitespace-pre-wrap leading-relaxed">
              {memory.content}
            </div>
          </div>

          {/* Summary */}
          {memory.summary && (
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-sm font-medium text-muted-foreground mb-3">Summary</h2>
              <p className="text-foreground">{memory.summary}</p>
            </div>
          )}

          {/* Metadata */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-sm font-medium text-muted-foreground mb-3">Metadata</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Importance</span>
                <div className="flex items-center gap-2 mt-1">
                  <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${memory.importance_score * 100}%` }}
                    />
                  </div>
                  <span className="text-foreground">{(memory.importance_score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div>
                <span className="text-muted-foreground">Confidence</span>
                <p className="text-foreground mt-1">{(memory.confidence * 100).toFixed(0)}%</p>
              </div>
              <div>
                <span className="text-muted-foreground">Accessed</span>
                <p className="text-foreground mt-1">{memory.access_count} times</p>
              </div>
              <div>
                <span className="text-muted-foreground">Status</span>
                <p className="text-foreground mt-1 capitalize">{memory.status}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Created</span>
                <p className="text-foreground mt-1">
                  {new Date(memory.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Updated</span>
                <p className="text-foreground mt-1">
                  {new Date(memory.updated_at).toLocaleString()}
                </p>
              </div>
              {memory.source && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">Source</span>
                  <p className="text-foreground mt-1">{memory.source}</p>
                </div>
              )}
            </div>
          </div>

          {/* Tags */}
          {memory.tags.length > 0 && (
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-sm font-medium text-muted-foreground mb-3">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {memory.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2.5 py-1 bg-muted text-foreground text-sm rounded-lg"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
