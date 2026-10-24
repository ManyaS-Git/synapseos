/* ── SynapseOS Clerk & Auth Provider ─────────────────────────────────── */

"use client";

import React, { useEffect } from "react";
import { ClerkProvider, useAuth as useClerkAuth } from "@clerk/nextjs";
import { setClerkTokenGetter } from "@/lib/api";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "";
const isClerkConfigured = !!publishableKey;

function ClerkAuthBridge({ children }: { children: React.ReactNode }) {
  const { isLoaded, getToken } = useClerkAuth();

  useEffect(() => {
    if (isLoaded) {
      setClerkTokenGetter(getToken);
    }
  }, [isLoaded, getToken]);

  return <>{children}</>;
}

export function SynapseAuthProvider({ children }: { children: React.ReactNode }) {
  if (!isClerkConfigured) {
    return <>{children}</>;
  }

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      appearance={{
        variables: {
          colorPrimary: "#6366f1",
          colorBackground: "#09090b",
          colorInputBackground: "#18181b",
          colorInputText: "#fafafa",
          colorText: "#fafafa",
          colorTextSecondary: "#a1a1aa",
          colorNeutral: "#fafafa",
          colorTextOnPrimaryBackground: "#ffffff",
          borderRadius: "0.75rem",
        },
        elements: {
          rootBox: "w-full max-w-md mx-auto",
          card: "border border-border/80 bg-card shadow-2xl backdrop-blur-xl text-foreground",
          headerTitle: "text-foreground font-semibold tracking-tight text-xl text-center",
          headerSubtitle: "text-muted-foreground text-xs text-center",
          socialButtonsBlockButton:
            "bg-secondary/60 border border-border text-foreground hover:bg-secondary transition-all duration-200",
          formButtonPrimary:
            "bg-primary text-primary-foreground font-medium hover:bg-primary/90 shadow-sm transition-all duration-200",
          formFieldInput:
            "bg-background border border-border text-foreground rounded-lg focus:ring-2 focus:ring-primary/40",
          footerActionLink: "text-primary hover:text-primary/80 font-medium",
          dividerLine: "bg-border",
          dividerText: "text-muted-foreground text-xs",
        },
      }}
    >
      <ClerkAuthBridge>{children}</ClerkAuthBridge>
    </ClerkProvider>
  );
}
