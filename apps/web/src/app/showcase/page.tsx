/* ── SynapseOS Showcase / Live Screenshot Capture Page ──────────────── */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore, useWorkspaceStore } from "@/store";
import { SynapseApp, type NavKey } from "@/components/synapse-app";
import { healthApi, agentApi } from "@/lib/api";
import type { User, Workspace } from "@/types";
import type { Memory, GraphData } from "@/types/memory";
import type { AgentChatResponse } from "@/types/agent";

const mockUser: User = {
  id: "usr_manya_sharma",
  email: "manya@synapseos.ai",
  username: "manyasharma",
  full_name: "Manya Sharma",
  avatar_url: null,
  email_verified: true,
  is_active: true,
  created_at: "2026-10-24T00:00:00Z",
  updated_at: "2026-10-24T00:00:00Z",
  last_login: "2026-10-24T18:00:00Z",
};

const mockWorkspace: Workspace = {
  id: "ws_personal_vault",
  owner_id: "usr_manya_sharma",
  name: "Personal AI Vault",
  slug: "personal-vault",
  description: "Zero-leakage encrypted local memory vault with Nebius inference",
  created_at: "2026-10-24T00:00:00Z",
  updated_at: "2026-10-24T00:00:00Z",
  member_count: 1,
  project_count: 3,
};

const mockMemories: Memory[] = [
  {
    id: "mem_1",
    owner_id: "usr_manya_sharma",
    workspace_id: "ws_personal_vault",
    project_id: "proj_1",
    title: "Quarterly Strategic Architecture Plan",
    content: "Core architectural tenets: 1. Local-first encrypted memory persistence across restarts. 2. Evidence-backed RAG with strict abstention guard. 3. Bounded agent execution requiring explicit human confirmation for consequential actions.",
    summary: "Architectural strategy prioritizing privacy-first multi-modal memory and bounded execution.",
    embedding_id: "emb_1",
    memory_type: "document",
    source: "local_upload",
    source_url: null,
    metadata_json: { chunk_count: 8, confidence: 0.99 },
    importance_score: 0.96,
    confidence: 1.0,
    status: "verified",
    access_count: 18,
    created_at: "2026-10-24T10:15:00Z",
    updated_at: "2026-10-24T10:15:00Z",
    accessed_at: "2026-10-24T18:30:00Z",
    tags: ["architecture", "security", "privacy", "rag"],
  },
  {
    id: "mem_2",
    owner_id: "usr_manya_sharma",
    workspace_id: "ws_personal_vault",
    project_id: "proj_1",
    title: "Nebius Token Factory & NVIDIA Nemotron Integration",
    content: "Integrated high-throughput NVIDIA Nemotron-4-340B-Instruct on Nebius GPU infrastructure for structured Pydantic plan decomposition with tool selection.",
    summary: "Inference connectivity benchmarks and parameter specs for Nemotron models.",
    embedding_id: "emb_2",
    memory_type: "concept",
    source: "agent_synthesis",
    source_url: null,
    metadata_json: { model: "nvidia/nemotron-4-340b-instruct" },
    importance_score: 0.94,
    confidence: 0.98,
    status: "active",
    access_count: 26,
    created_at: "2026-10-24T11:20:00Z",
    updated_at: "2026-10-24T11:20:00Z",
    accessed_at: "2026-10-24T18:45:00Z",
    tags: ["nebius", "nvidia", "nemotron", "llm"],
  },
  {
    id: "mem_3",
    owner_id: "usr_manya_sharma",
    workspace_id: "ws_personal_vault",
    project_id: "proj_2",
    title: "SSRF Hardening and Consequential Tool Guardrails",
    content: "Strict outbound request validation blocks RFC1918 private IP subnets, loopback interfaces (127.0.0.1), and cloud metadata endpoints (169.254.169.254).",
    summary: "Network security policies preventing SSRF and cross-tenant leakage.",
    embedding_id: "emb_3",
    memory_type: "rule",
    source: "security_audit",
    source_url: null,
    metadata_json: { rfc1918_blocked: true, metadata_blocked: true },
    importance_score: 0.91,
    confidence: 1.0,
    status: "enforced",
    access_count: 12,
    created_at: "2026-10-24T12:05:00Z",
    updated_at: "2026-10-24T12:05:00Z",
    accessed_at: "2026-10-24T17:10:00Z",
    tags: ["security", "guardrails", "ssrf"],
  },
  {
    id: "mem_4",
    owner_id: "usr_manya_sharma",
    workspace_id: "ws_personal_vault",
    project_id: "proj_3",
    title: "Personal Coding Preferences & Agent Workflow",
    content: "Developer prefers dark mode, GitHub flow branching, clean commit messages, typed TypeScript interfaces, and pytest unit testing harnesses.",
    summary: "User coding preferences remembered by the personal OS.",
    embedding_id: "emb_4",
    memory_type: "preference",
    source: "user_input",
    source_url: null,
    metadata_json: {},
    importance_score: 0.88,
    confidence: 0.95,
    status: "active",
    access_count: 35,
    created_at: "2026-10-24T13:00:00Z",
    updated_at: "2026-10-24T13:00:00Z",
    accessed_at: "2026-10-24T19:00:00Z",
    tags: ["preferences", "workflow"],
  },
  {
    id: "mem_5",
    owner_id: "usr_manya_sharma",
    workspace_id: "ws_personal_vault",
    project_id: "proj_1",
    title: "Multi-Modal Document Parsing Specs",
    content: "Handles PDF, Markdown, JSON, and CSV inputs with chunk overlap window of 200 tokens and SHA-256 integrity hashing.",
    summary: "Specifications for document ingestion and chunking pipeline.",
    embedding_id: "emb_5",
    memory_type: "document",
    source: "local_upload",
    source_url: null,
    metadata_json: {},
    importance_score: 0.86,
    confidence: 0.97,
    status: "verified",
    access_count: 19,
    created_at: "2026-10-24T14:30:00Z",
    updated_at: "2026-10-24T14:30:00Z",
    accessed_at: "2026-10-24T19:15:00Z",
    tags: ["ingestion", "documents", "rag"],
  },
];

const mockGraph: GraphData = {
  nodes: [
    { id: "node_1", label: "Strategic Architecture", type: "document", memory_type: "document" },
    { id: "node_2", label: "Nebius Inference", type: "concept", memory_type: "concept" },
    { id: "node_3", label: "SSRF Guardrails", type: "rule", memory_type: "rule" },
    { id: "node_4", label: "User Preferences", type: "preference", memory_type: "preference" },
    { id: "node_5", label: "NVIDIA Nemotron 340B", type: "concept", memory_type: "concept" },
    { id: "node_6", label: "Grounded RAG Engine", type: "system", memory_type: "system" },
    { id: "node_7", label: "Human Approval Gate", type: "rule", memory_type: "rule" },
    { id: "node_8", label: "Multi-Modal Ingest", type: "document", memory_type: "document" },
  ],
  edges: [
    { id: "e1", source: "node_1", target: "node_6", label: "grounds" },
    { id: "e2", source: "node_2", target: "node_5", label: "hosts" },
    { id: "e3", source: "node_5", target: "node_7", label: "submits_plan" },
    { id: "e4", source: "node_3", target: "node_7", label: "enforces" },
    { id: "e5", source: "node_4", target: "node_6", label: "personalizes" },
    { id: "e6", source: "node_8", target: "node_1", label: "ingested_into" },
    { id: "e7", source: "node_6", target: "node_2", label: "synthesizes_with" },
  ],
};

const mockPendingApproval: AgentChatResponse = {
  session_id: "sess_approval_894",
  status: "awaiting_approval",
  message: "I have decomposed your instruction into 3 steps. Step 2 requires creating guardrails.json in workspace storage. Human approval is required.",
  plan: {
    goal: "Deploy production guardrails and configure workspace policies",
    reasoning: "Step 1 retrieves memory rules. Step 2 creates the guardrail configuration file. Step 3 logs the audit trail.",
    confidence_score: 0.98,
    steps: [
      { step_number: 1, description: "Retrieve active security rules", tool_name: "memory_retrieve", tool_args: { query: "security policies" }, requires_approval: false, status: "completed" },
      { step_number: 2, description: "Write guardrails policy configuration", tool_name: "workspace_file_create", tool_args: { path: "guardrails.json" }, requires_approval: true, status: "awaiting_approval" },
      { step_number: 3, description: "Record verification in persistent memory", tool_name: "memory_record", tool_args: { title: "Policy Update" }, requires_approval: false, status: "pending" }
    ],
  },
  pending_step: {
    step_number: 2,
    description: "Write guardrails policy configuration",
    tool_name: "workspace_file_create",
    tool_args: { path: "guardrails.json" },
    requires_approval: true,
    status: "awaiting_approval"
  },
  executed_steps: [
    { step_number: 1, description: "Retrieve active security rules", tool_name: "memory_retrieve", tool_args: { query: "security policies" }, requires_approval: false, status: "completed" }
  ],
  model_used: "nvidia/nemotron-3-8b",
  latency_ms: 312
};

export default function ShowcasePage() {
  const searchParams = useSearchParams();
  const rawTab = searchParams.get("tab") || "Overview";
  const tab = (["Overview", "Assistant", "Memory", "Graph", "Documents", "Agents", "Activity"].includes(rawTab)
    ? rawTab
    : "Overview") as NavKey;

  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();
  const { setCurrentWorkspace, setWorkspaces } = useWorkspaceStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Override health probe to healthy
    healthApi.check = async () => ({ status: "healthy", name: "SynapseOS" });

    // Override agentApi.chat for showcase interaction
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (agentApi as any).chat = async () => mockPendingApproval;

    // 1. Synchronously seed stores
    setUser(mockUser);
    setCurrentWorkspace(mockWorkspace);
    setWorkspaces([mockWorkspace]);

    // 2. Synchronously seed TanStack Query cache
    queryClient.setQueryData(["auth", "me"], mockUser);
    queryClient.setQueryData(["workspaces"], [mockWorkspace]);
    queryClient.setQueryData(
      ["memories", mockWorkspace.id, { page_size: 50 }],
      { memories: mockMemories, total: mockMemories.length, page: 1, page_size: 50 }
    );
    queryClient.setQueryData(["memoryGraph", mockWorkspace.id, undefined], mockGraph);
    queryClient.setQueryData(["recentMemories", mockWorkspace.id, 10], mockMemories.slice(0, 5));
    queryClient.setQueryData(["importantMemories", mockWorkspace.id, 10], mockMemories.slice(0, 5));

    setReady(true);
  }, [queryClient, setUser, setCurrentWorkspace, setWorkspaces]);

  if (!ready) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <p className="text-xs text-muted-foreground animate-pulse">Rendering SynapseOS Showcase...</p>
      </div>
    );
  }

  return (
    <div>
      <aside
        aria-label="Showcase mode notice"
        className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 text-center text-xs font-medium text-amber-900 dark:text-amber-200 sticky top-0 z-50 backdrop-blur-md flex items-center justify-center gap-2"
      >
        <span className="font-semibold uppercase tracking-wider text-[10px] bg-amber-500/20 px-2 py-0.5 rounded">
          Preview Mode
        </span>
        <span>
          Displaying sample demonstration dataset. To interact with your real memories and live inference,{" "}
          <Link
            href="/dashboard"
            className="underline underline-offset-4 font-semibold text-primary hover:text-primary/80"
          >
            open your Dashboard
          </Link>
          .
        </span>
      </aside>
      <SynapseApp initialTab={tab} />
    </div>
  );
}
