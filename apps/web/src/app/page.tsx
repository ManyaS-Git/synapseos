'use client';

import { useEffect, useState } from 'react';

interface HealthStatus {
  status: string;
  services?: Record<string, { status: string; error?: string }>;
  version?: string;
  environment?: string;
  check_duration_ms?: number;
}

interface ServiceInfo {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unavailable' | 'unknown';
}

const STACK = [
  { name: 'Next.js 14', category: 'Frontend' },
  { name: 'TypeScript', category: 'Frontend' },
  { name: 'Tailwind CSS', category: 'Frontend' },
  { name: 'shadcn/ui', category: 'Frontend' },
  { name: 'Zustand', category: 'State' },
  { name: 'TanStack Query', category: 'Data' },
  { name: 'React Flow', category: 'Visualization' },
  { name: 'FastAPI', category: 'Backend' },
  { name: 'Python 3.12', category: 'Backend' },
  { name: 'PostgreSQL', category: 'Database' },
  { name: 'Qdrant', category: 'Vector DB' },
  { name: 'Neo4j', category: 'Graph DB' },
  { name: 'Redis', category: 'Cache' },
  { name: 'Ollama', category: 'LLM' },
  { name: 'Docker', category: 'Infrastructure' },
];

const ROADMAP = [
  { phase: 'Phase 1', title: 'Foundation', status: 'in-progress' },
  { phase: 'Phase 2', title: 'Memory & Knowledge', status: 'planned' },
  { phase: 'Phase 3', title: 'Intelligence', status: 'planned' },
  { phase: 'Phase 4', title: 'Interface', status: 'planned' },
  { phase: 'Phase 5', title: 'Polish & Scale', status: 'planned' },
];

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    healthy: 'bg-emerald-500',
    alive: 'bg-emerald-500',
    ready: 'bg-emerald-500',
    degraded: 'bg-amber-500',
    unhealthy: 'bg-red-500',
    unavailable: 'bg-gray-400',
    unknown: 'bg-gray-400',
  };
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${colors[status] || colors.unknown}`}
    />
  );
}

function RoadmapItem({
  phase,
  title,
  status,
}: {
  phase: string;
  title: string;
  status: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border/50 bg-card/50 p-3">
      <div className="flex-shrink-0 text-xs font-medium text-muted-foreground">
        {phase}
      </div>
      <div className="flex-1">
        <div className="text-sm font-medium">{title}</div>
      </div>
      <div className="flex-shrink-0">
        {status === 'in-progress' ? (
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            In Progress
          </span>
        ) : (
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            Planned
          </span>
        )}
      </div>
    </div>
  );
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    async function fetchHealth() {
      try {
        const res = await fetch(`${apiUrl}/health/ready`, {
          signal: AbortSignal.timeout(5000),
        });
        const data = await res.json();
        setHealth(data);
      } catch {
        setHealth({ status: 'unavailable' });
      } finally {
        setLoading(false);
      }
    }

    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const services: ServiceInfo[] = health?.services
    ? Object.entries(health.services).map(([name, info]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        status: (info.status || 'unknown') as ServiceInfo['status'],
      }))
    : [
        { name: 'PostgreSQL', status: 'unknown' },
        { name: 'Redis', status: 'unknown' },
        { name: 'Neo4j', status: 'unknown' },
        { name: 'Qdrant', status: 'unknown' },
        { name: 'Ollama', status: 'unknown' },
      ];

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-5xl px-6 py-16">
        {/* Header */}
        <div className="mb-16 text-center">
          <div className="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10">
            <span className="text-3xl font-bold text-primary">S</span>
          </div>
          <h1 className="text-5xl font-bold tracking-tight">SynapseOS</h1>
          <p className="mt-3 text-lg text-muted-foreground">
            A Privacy-First AI Operating System
          </p>
          <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1">
            <span className="inline-block h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
            <span className="text-sm font-medium text-amber-600 dark:text-amber-400">
              Currently in Active Development
            </span>
          </div>
        </div>

        {/* Status Banner */}
        <div className="mb-12 rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusDot status={health?.status || 'unknown'} />
              <div>
                <h2 className="text-sm font-semibold">
                  System Status:{' '}
                  {loading ? 'Checking...' : health?.status || 'unavailable'}
                </h2>
                {health?.version && (
                  <p className="text-xs text-muted-foreground">
                    v{health.version} | {health.environment}
                  </p>
                )}
              </div>
            </div>
            {health?.check_duration_ms !== undefined && (
              <span className="text-xs text-muted-foreground">
                {health.check_duration_ms}ms
              </span>
            )}
          </div>

          {/* Services */}
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
            {services.map((svc) => (
              <div
                key={svc.name}
                className="flex items-center gap-2 rounded-lg border border-border/50 bg-background/50 px-3 py-2"
              >
                <StatusDot status={svc.status} />
                <span className="text-xs font-medium">{svc.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mb-12">
          <h2 className="mb-4 text-xl font-bold">Technology Stack</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
            {STACK.map((item) => (
              <div
                key={item.name}
                className="rounded-lg border border-border/50 bg-card/50 px-3 py-2"
              >
                <div className="text-sm font-medium">{item.name}</div>
                <div className="text-xs text-muted-foreground">{item.category}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Roadmap */}
        <div className="mb-12">
          <h2 className="mb-4 text-xl font-bold">Development Roadmap</h2>
          <div className="space-y-2">
            {ROADMAP.map((item) => (
              <RoadmapItem key={item.phase} {...item} />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t pt-8 text-center text-sm text-muted-foreground">
          <p>SynapseOS &mdash; Built with care by the community</p>
          <p className="mt-1">
            <span className="font-medium">Apache License 2.0</span> | Open Source
          </p>
        </div>
      </div>
    </div>
  );
}
