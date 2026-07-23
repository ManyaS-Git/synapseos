/* ── Memory Graph Page ─────────────────────────────────────────────── */

"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useMemoryGraph, useMemories } from "@/hooks/use-memory";
import { Sidebar } from "@/components/sidebar";
import { MEMORY_TYPE_COLORS } from "@/types/memory";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";

export default function MemoryGraphPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const { data: graph, isLoading: loadingGraph } = useMemoryGraph(
    selectedProjectId || undefined
  );
  const { data: memoryList } = useMemories({ page_size: 50 });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };

    const nodeMap = new Map<string, Node>();

    graph.nodes.forEach((gNode) => {
      nodeMap.set(gNode.id, {
        id: gNode.id,
        position: { x: 0, y: 0 },
        data: {
          label: (
            <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-sm max-w-[200px]">
              <div className="flex items-center gap-1.5 mb-0.5">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: MEMORY_TYPE_COLORS[gNode.memory_type || gNode.type] || "#6b7280" }}
                />
                <span className="text-[10px] text-muted-foreground capitalize">
                  {gNode.memory_type || gNode.type}
                </span>
              </div>
              <p className="text-xs font-medium text-foreground truncate">{gNode.label}</p>
            </div>
          ),
          memoryType: gNode.memory_type || gNode.type,
        },
        type: "default",
      });
    });

    const flowEdges: Edge[] = graph.edges.map((gEdge, idx) => ({
      id: `e-${idx}`,
      source: gEdge.source,
      target: gEdge.target,
      label: gEdge.label,
      labelStyle: { fill: "hsl(var(--muted-foreground))", fontSize: 10 },
      labelBgStyle: { fill: "hsl(var(--card))", fillOpacity: 0.9 },
      animated: (gEdge.weight || 0.5) > 0.7,
      style: { stroke: "hsl(var(--border))", strokeWidth: Math.max(1, (gEdge.weight || 0.5) * 3) },
    }));

    return { nodes: Array.from(nodeMap.values()), edges: flowEdges };
  }, [graph]);

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
      <main className="flex-1 overflow-auto flex flex-col">
        <header className="border-b border-border px-8 py-4 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Memory Graph</h1>
            <p className="text-muted-foreground mt-0.5">
              {graph ? `${graph.nodes.length} nodes • ${graph.edges.length} connections` : "Loading graph..."}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground"
            >
              <option value="">All projects</option>
              {memoryList?.memories
                ?.filter((m) => m.project_id)
                .reduce<string[]>((acc, m) => {
                  if (m.project_id && !acc.includes(m.project_id)) acc.push(m.project_id);
                  return acc;
                }, [])
                .map((pid) => (
                  <option key={pid} value={pid}>{pid.slice(0, 8)}...</option>
                ))}
            </select>
          </div>
        </header>

        <div className="flex-1 relative">
          {loadingGraph ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-muted-foreground animate-pulse">Building graph...</p>
            </div>
          ) : nodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-muted-foreground">No memories to display in the graph.</p>
                <button
                  onClick={() => router.push("/memory/create")}
                  className="mt-3 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
                >
                  Create Memory
                </button>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              fitViewOptions={{ padding: 0.3 }}
              minZoom={0.2}
              maxZoom={2}
              className="bg-background"
              onNodeClick={(_, node) => router.push(`/memory/${node.id}`)}
            >
              <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
              <Controls className="!bg-card !border-border !rounded-xl" />
              <MiniMap
                nodeColor={(n) => MEMORY_TYPE_COLORS[n.data.memoryType as string] || "#6b7280"}
                maskColor="hsl(var(--background) / 0.7)"
                className="!bg-card !border-border !rounded-xl"
              />
            </ReactFlow>
          )}
        </div>
      </main>
    </div>
  );
}
