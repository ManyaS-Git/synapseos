/* ── Root Page — SynapseOS Marketing Landing Page ─────────────────────── */

"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { Navigation } from "@/components/landing/navigation";
import { HeroSection } from "@/components/landing/hero-section";
import { FeaturesSection } from "@/components/landing/features-section";
import { HowItWorksSection } from "@/components/landing/how-it-works-section";
import { DevelopersSection } from "@/components/landing/developers-section";
import { InfrastructureSection } from "@/components/landing/infrastructure-section";
import { IntegrationsSection } from "@/components/landing/integrations-section";
import { MetricsSection } from "@/components/landing/metrics-section";
import { PricingSection } from "@/components/landing/pricing-section";
import { SecuritySection } from "@/components/landing/security-section";
import { TestimonialsSection } from "@/components/landing/testimonials-section";
import { CtaSection } from "@/components/landing/cta-section";
import { FooterSection } from "@/components/landing/footer-section";
import { ArrowRight, Sparkles } from "lucide-react";

export default function HomePage() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-foreground selection:text-background">
      {isAuthenticated && (
        <aside aria-label="Authenticated session" className="bg-primary/10 border-b border-primary/20 py-2.5 px-4 text-center text-xs font-medium text-foreground sticky top-0 z-50 backdrop-blur-md flex items-center justify-center gap-2">
          <Sparkles className="size-3.5 text-primary" />
          <span>Signed in as <strong>{user?.full_name || user?.username}</strong></span>
          <Link
            href="/dashboard"
            className="ml-2 inline-flex items-center gap-1 underline underline-offset-4 font-semibold text-primary hover:text-primary/80"
          >
            Go to SynapseOS Dashboard <ArrowRight className="size-3" />
          </Link>
        </aside>
      )}

      <Navigation />
      <main id="main-content">
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <DevelopersSection />
        <InfrastructureSection />
        <IntegrationsSection />
        <MetricsSection />
        <PricingSection />
        <SecuritySection />
        <TestimonialsSection />
        <CtaSection />
      </main>
      <FooterSection />
    </div>
  );
}
