/* ── Memory Search Page ────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useMemorySearch } from "@/hooks/use-memory";
import { Sidebar } from "@/components/sidebar";
import { MEMORY_TYPE_COLORS } from "@/types/memory";

export default function MemorySearchPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const { data, isLoading: searching } = useMemorySearch(debouncedQuery, debouncedQuery.length > 2);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 400);
    return () => clearTimeout(timer);
  }, [query]);

  if (isLoading) {
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
        <header className="border-b border-border px-8 py-6">
          <h1 className="text-2xl font-bold text-foreground">Search Memories</h1>
          <p className="text-muted-foreground mt-1">Semantic search across all your memories</p>
        </header>

        <div className="px-8 py-6 max-w-3xl">
          <div className="relative mb-6">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-lg"
              placeholder="Search memories by meaning..."
              autoFocus
            />
            {searching && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
              </div>
            )}
          </div>

          {debouncedQuery.length > 2 && !searching && data && (
            <div>
              <p className="text-sm text-muted-foreground mb-4">
                {data.results.length} result{data.results.length !== 1 ? "s" : ""} found
              </p>

              {data.results.length > 0 ? (
                <div className="space-y-3">
                  {data.results.map((result) => (
                    <div
                      key={result.memory.id}
                      className="bg-card border border-border rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => router.push(`/memory/${result.memory.id}`)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: MEMORY_TYPE_COLORS[result.memory.memory_type] || "#6b7280" }}
                            />
                            <span className="text-xs text-muted-foreground capitalize">
                              {result.memory.memory_type}
                            </span>
                            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                              {(result.score * 100).toFixed(0)}% match
                            </span>
                          </div>
                          <h3 className="font-medium text-foreground">{result.memory.title}</h3>
                          {result.chunk_content && (
                            <p className="text-sm text-muted-foreground line-clamp-2 mt-1 font-mono bg-muted/50 px-2 py-1 rounded">
                              {result.chunk_content}
                            </p>
                          )}
                          {!result.chunk_content && (
                            <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                              {result.memory.content}
                            </p>
                          )}
                          {result.memory.tags.length > 0 && (
                            <div className="flex gap-1 mt-2">
                              {result.memory.tags.slice(0, 5).map((tag) => (
                                <span key={tag} className="text-xs bg-muted px-1.5 py-0.5 rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16">
                  <p className="text-muted-foreground">No memories match your search.</p>
                </div>
              )}
            </div>
          )}

          {debouncedQuery.length <= 2 && (
            <div className="text-center py-16">
              <p className="text-muted-foreground">Type at least 3 characters to search.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
