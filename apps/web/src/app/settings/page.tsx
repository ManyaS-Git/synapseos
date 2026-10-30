/* ── Settings Page ─────────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useUpdateProfile, useHealthReady } from "@/hooks/use-auth";
import { Sidebar } from "@/components/sidebar";

export default function SettingsPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const updateProfileMutation = useUpdateProfile();
  const { data: healthReady, isLoading: healthLoading } = useHealthReady();
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState("");

  useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name);
    }
  }, [user?.full_name]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSuccess(false);
    setProfileError("");
    try {
      await updateProfileMutation.mutateAsync({
        full_name: fullName.trim(),
      });
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 4000);
    } catch (err: unknown) {
      setProfileError(err instanceof Error ? err.message : "Failed to update profile");
    }
  };

  // Extract live provider status from healthReady probe
  const nebiusService = healthReady?.services?.nebius_token_factory as
    | { status?: string; configured?: boolean; model?: string; provider?: string }
    | undefined;
  const isNebiusConfigured = Boolean(nebiusService?.configured);
  const isNebiusHealthy = nebiusService?.status === "healthy";
  const storageMode = (healthReady as unknown as { storage_mode?: string })?.storage_mode || "local_embedded";

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <header className="border-b border-border px-8 py-6">
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground mt-1">Manage your account and operational configuration</p>
        </header>

        <div className="px-8 py-6 max-w-2xl space-y-6">
          {/* Profile Section */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Profile</h2>
            {profileSuccess && (
              <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                Profile updated successfully and persisted to database.
              </div>
            )}
            {profileError && (
              <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-xs text-destructive font-medium">
                {profileError}
              </div>
            )}
            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Username
                </label>
                <input
                  type="text"
                  value={user.username}
                  disabled
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-muted-foreground"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-muted-foreground"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                  placeholder="Your full name"
                />
              </div>
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={updateProfileMutation.isPending}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-xs font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {updateProfileMutation.isPending ? "Saving..." : "Save Profile"}
                </button>
              </div>
            </form>
          </div>

          {/* Nebius × NVIDIA Inference Engine */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Inference Engine (Nebius Token Factory)</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Powered by NVIDIA open models hosted on high-throughput Nebius infrastructure.
                </p>
              </div>
              {healthLoading ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                  Probing...
                </span>
              ) : isNebiusHealthy && isNebiusConfigured ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Nebius AI
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  Simulation Mode (Offline Fallback)
                </span>
              )}
            </div>

            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between text-xs py-2 px-3 rounded-lg border border-border bg-background">
                <span className="text-muted-foreground">Active Storage Layer</span>
                <span className="font-semibold text-foreground">
                  {storageMode === "distributed"
                    ? "Distributed (PostgreSQL + Qdrant + Neo4j)"
                    : "Local Embedded (SQLite + Local Vector Index)"}
                </span>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Active Model
                </label>
                <select
                  defaultValue={nebiusService?.model || "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF">
                    nvidia/Llama-3.1-Nemotron-70B-Instruct-HF (Active)
                  </option>
                  <option value="nvidia/nemotron-4-340b-instruct">
                    nvidia/nemotron-4-340b-instruct (Nebius Token Factory)
                  </option>
                  <option value="nvidia/llama-3.1-nemotron-70b-instruct">
                    nvidia/llama-3.1-nemotron-70b-instruct (Nebius Token Factory)
                  </option>
                  <option value="local/ollama-fallback">
                    Local Ollama (Offline Fallback)
                  </option>
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  NVIDIA Nemotron models provide exceptional instruction following and structured JSON tool planning.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  API Endpoint Base URL
                </label>
                <input
                  type="text"
                  value="https://api.tokenfactory.nebius.com/v1/"
                  disabled
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-muted-foreground font-mono text-xs"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Inference Routing Strategy
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="border-2 border-primary bg-primary/5 rounded-lg p-3 cursor-pointer">
                    <p className="text-sm font-semibold text-foreground">Hybrid Cloud (Recommended)</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Local memory & vector embeddings, Nebius for complex Nemotron reasoning.
                    </p>
                  </div>
                  <div className="border border-border bg-card rounded-lg p-3 cursor-pointer hover:border-primary/50">
                    <p className="text-sm font-semibold text-foreground">Local-First Only</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      All embeddings and inference stay entirely offline via local Ollama.
                    </p>
                  </div>
                  <div className="border border-border bg-card rounded-lg p-3 cursor-pointer hover:border-primary/50">
                    <p className="text-sm font-semibold text-foreground">Cloud Accelerated</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Maximum performance using Nebius GPU nodes for all workloads.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Privacy & Data Governance */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Privacy & Zero-Leakage Controls</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                SynapseOS adheres to strict local-first ownership boundaries.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-start justify-between gap-4 p-3 border border-border rounded-lg bg-background">
                <div>
                  <p className="text-sm font-medium text-foreground">Client-Side Redaction</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Filter credentials, personal phone numbers, and keys before sending context to external APIs.
                  </p>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
              </div>

              <div className="flex items-start justify-between gap-4 p-3 border border-border rounded-lg bg-background">
                <div>
                  <p className="text-sm font-medium text-foreground">Zero Prompt Logging</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Server logs record model latency and token counts only; raw user prompts are never written to disk or logs.
                  </p>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  disabled
                  className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary opacity-80"
                />
              </div>

              <div className="flex items-start justify-between gap-4 p-3 border border-border rounded-lg bg-background">
                <div>
                  <p className="text-sm font-medium text-foreground">Human-in-the-Loop Action Approvals</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Require explicit confirmation before creating resources, sending outbound requests, or modifying files.
                  </p>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  disabled
                  className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary opacity-80"
                />
              </div>
            </div>
          </div>

          {/* Account Info */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Account</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Member since</span>
                <span className="text-foreground">
                  {new Date(user.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last login</span>
                <span className="text-foreground">
                  {user.last_login
                    ? new Date(user.last_login).toLocaleString()
                    : "First login"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Email verified</span>
                <span className="text-foreground">
                  {user.email_verified ? "Yes" : "No"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
