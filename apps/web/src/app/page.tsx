/* ── Root Page — Landing / Redirect ────────────────────────────────── */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground animate-pulse">Loading SynapseOS...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-2xl">
          <div className="w-16 h-16 rounded-2xl bg-primary mx-auto flex items-center justify-center mb-6">
            <span className="text-primary-foreground font-bold text-3xl">S</span>
          </div>
          <h1 className="text-5xl font-bold text-foreground mb-4">SynapseOS</h1>
          <p className="text-xl text-muted-foreground mb-8">
            A Privacy-First AI Operating System
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/login"
              className="px-6 py-3 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="px-6 py-3 border border-border text-foreground font-medium rounded-lg hover:bg-muted transition-colors"
            >
              Create account
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-8 py-6 text-center">
        <p className="text-sm text-muted-foreground">
          SynapseOS v0.1.0 — In Active Development
        </p>
      </footer>
    </div>
  );
}
