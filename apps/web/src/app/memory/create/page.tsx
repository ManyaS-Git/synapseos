/* ── Create Memory Page ────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useCreateMemory } from "@/hooks/use-memory";
import { useProjectStore } from "@/store";
import { Sidebar } from "@/components/sidebar";
import { MEMORY_TYPES } from "@/types/memory";

export default function CreateMemoryPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { projects } = useProjectStore();
  const router = useRouter();
  const createMutation = useCreateMemory();

  const [form, setForm] = useState({
    title: "",
    content: "",
    summary: "",
    memory_type: "knowledge",
    project_id: "",
    source: "",
    tags: "",
    importance_score: 0.5,
    chunking_strategy: "recursive",
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) return;

    createMutation.mutate(
      {
        title: form.title,
        content: form.content,
        summary: form.summary || undefined,
        memory_type: form.memory_type,
        project_id: form.project_id || undefined,
        source: form.source || undefined,
        tags: form.tags ? form.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
        importance_score: form.importance_score,
        chunking_strategy: form.chunking_strategy,
      },
      {
        onSuccess: (memory) => {
          router.push(`/memory/${memory.id}`);
        },
      }
    );
  };

  const update = (field: string, value: string | number) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <header className="border-b border-border px-8 py-6">
          <h1 className="text-2xl font-bold text-foreground">Create Memory</h1>
          <p className="text-muted-foreground mt-1">Add a new memory to your workspace</p>
        </header>

        <div className="px-8 py-6 max-w-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Title</label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => update("title", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                placeholder="Memory title"
                required
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Content</label>
              <textarea
                value={form.content}
                onChange={(e) => update("content", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none font-mono"
                placeholder="Write your memory content here..."
                rows={10}
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                {form.content.length} characters
              </p>
            </div>

            {/* Summary */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Summary <span className="text-muted-foreground">(optional)</span>
              </label>
              <textarea
                value={form.summary}
                onChange={(e) => update("summary", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none"
                placeholder="Brief summary"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Memory Type */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">Type</label>
                <select
                  value={form.memory_type}
                  onChange={(e) => update("memory_type", e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {MEMORY_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              {/* Project */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Project <span className="text-muted-foreground">(optional)</span>
                </label>
                <select
                  value={form.project_id}
                  onChange={(e) => update("project_id", e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="">No project</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Source */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Source <span className="text-muted-foreground">(optional)</span>
                </label>
                <input
                  type="text"
                  value={form.source}
                  onChange={(e) => update("source", e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="e.g. meeting notes, article"
                />
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Tags <span className="text-muted-foreground">(comma-separated)</span>
                </label>
                <input
                  type="text"
                  value={form.tags}
                  onChange={(e) => update("tags", e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="python, architecture, api"
                />
              </div>
            </div>

            {/* Importance Score */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Importance: {(form.importance_score * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={form.importance_score}
                onChange={(e) => update("importance_score", parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Low</span>
                <span>High</span>
              </div>
            </div>

            {/* Chunking Strategy */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Chunking Strategy</label>
              <select
                value={form.chunking_strategy}
                onChange={(e) => update("chunking_strategy", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="recursive">Recursive (Recommended)</option>
                <option value="paragraph">Paragraph</option>
                <option value="sentence">Sentence</option>
              </select>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t border-border">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!form.title.trim() || !form.content.trim() || createMutation.isPending}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {createMutation.isPending ? "Creating..." : "Create Memory"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
