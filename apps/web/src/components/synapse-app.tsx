'use client'

import { useMemo, useState, useRef, useEffect } from 'react'
import type { ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Brain,
  Check,
  ChevronDown,
  CircleDot,
  FileText,
  GitBranch,
  HelpCircle,
  LayoutDashboard,
  Loader2,
  Lock,
  LogOut,
  Menu,
  MessageSquareText,
  Plus,
  Search,
  Send,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAuth, useLogout, useWorkspaces } from '@/hooks/use-auth'
import { useWorkspaceStore } from '@/store'
import {
  useMemories,
  useCreateMemory,
  useDeleteMemory,
  useMemoryGraph,
} from '@/hooks/use-memory'
import { useAgentChat, useAgentApprove, useRAGQuery } from '@/hooks/use-agent'
import { memoryApi } from '@/lib/api'
import type { Memory, GraphNode } from '@/types/memory'
import type { AgentChatResponse, RAGQueryResponse } from '@/types/agent'

export type NavKey = 'Overview' | 'Assistant' | 'Memory' | 'Graph' | 'Documents' | 'Agents' | 'Activity'

interface SynapseAppProps {
  initialTab?: NavKey
}

const navItems: { label: NavKey; icon: typeof LayoutDashboard; badge?: string }[] = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Assistant', icon: MessageSquareText },
  { label: 'Memory', icon: Brain },
  { label: 'Graph', icon: GitBranch },
  { label: 'Documents', icon: FileText },
  { label: 'Agents', icon: Zap },
  { label: 'Activity', icon: Activity },
]

export function SynapseApp({ initialTab = 'Overview' }: SynapseAppProps) {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const logoutMutation = useLogout()
  const { data: workspaces } = useWorkspaces()
  const { currentWorkspace, setCurrentWorkspace } = useWorkspaceStore()

  const [active, setActive] = useState<NavKey>(initialTab)
  const [mobileNav, setMobileNav] = useState(false)
  const [query, setQuery] = useState('')
  const [notice, setNotice] = useState('')
  const [createMemoryOpen, setCreateMemoryOpen] = useState(false)
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)

  // Route protection
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  // Ensure workspace is initialized
  useEffect(() => {
    if (workspaces && workspaces.length > 0 && !currentWorkspace) {
      setCurrentWorkspace(workspaces[0])
    }
  }, [workspaces, currentWorkspace, setCurrentWorkspace])

  // Real backend queries
  const { data: memoriesData, isLoading: memoriesLoading, refetch: refetchMemories } = useMemories({
    page_size: 50,
  })
  const { data: graphData, isLoading: graphLoading } = useMemoryGraph()
  const deleteMemoryMutation = useDeleteMemory()

  // Track pending agent approval sessions across the app
  const [pendingApproval, setPendingApproval] = useState<AgentChatResponse | null>(null)

  const memoriesList = useMemo(() => memoriesData?.memories || [], [memoriesData])

  const filteredMemories = useMemo(() => {
    if (!query.trim()) return memoriesList
    const q = query.toLowerCase()
    return memoriesList.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.content.toLowerCase().includes(q) ||
        m.memory_type.toLowerCase().includes(q) ||
        (m.tags && m.tags.some((t) => t.toLowerCase().includes(q)))
    )
  }, [memoriesList, query])

  const documentMemories = useMemo(
    () => memoriesList.filter((m) => m.memory_type === 'document' || m.source),
    [memoriesList]
  )

  // Memory health calculation (real score based on memory count and tagging)
  const memoryHealthScore = useMemo(() => {
    if (memoriesList.length === 0) return 40
    const taggedCount = memoriesList.filter((m) => m.tags && m.tags.length > 0).length
    const tagRatio = taggedCount / memoriesList.length
    const score = Math.min(98, Math.round(50 + tagRatio * 40 + Math.min(memoriesList.length, 10)))
    return score
  }, [memoriesList])

  function showNotification(msg: string) {
    setNotice(msg)
    setTimeout(() => setNotice(''), 4500)
  }

  function handleQuickAction(text: string) {
    if (text === 'Add memory' || text === 'Create memory') {
      setCreateMemoryOpen(true)
    } else if (text === 'Upload document' || text === 'Choose file') {
      setActive('Documents')
    } else if (text === 'Explore graph' || text === 'Open graph') {
      setActive('Graph')
    } else if (text === 'View all memories') {
      setActive('Memory')
    } else if (text === 'Review pending approval' || text === 'Review request') {
      setActive('Assistant')
    } else {
      setActive('Assistant')
    }
  }

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Brain className="size-8 animate-pulse text-primary" />
          <p className="text-xs text-muted-foreground">Connecting to SynapseOS workspace...</p>
        </div>
      </div>
    )
  }

  const workspaceName = currentWorkspace?.name || (user ? `${user.username}'s workspace` : 'Personal workspace')
  const userInitials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user?.username?.slice(0, 2).toUpperCase() || 'SO'

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Sidebar Navigation */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-[248px] flex-col border-r border-border bg-sidebar px-4 py-5 transition-transform duration-200 lg:translate-x-0',
          mobileNav ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Brand */}
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2.5">
            <span className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Brain className="size-4" />
            </span>
            <span className="font-semibold tracking-[-0.02em]">
              synapse<span className="text-muted-foreground">OS</span>
            </span>
          </div>
          <button
            className="rounded-md p-1.5 text-muted-foreground hover:bg-sidebar-accent lg:hidden"
            onClick={() => setMobileNav(false)}
            aria-label="Close navigation"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Workspace Selector */}
        <div className="mt-8 flex items-center gap-2 rounded-lg border border-sidebar-border bg-sidebar-accent/50 px-3 py-2.5 text-left">
          <div className="grid size-7 place-items-center rounded-md bg-foreground text-xs font-semibold text-background">
            {workspaceName.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium">{workspaceName}</p>
            <p className="truncate text-[10px] text-muted-foreground">
              {currentWorkspace?.description || 'Personal knowledge base'}
            </p>
          </div>
          <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" />
        </div>

        {/* Navigation items */}
        <nav className="mt-8 space-y-1" aria-label="Primary navigation">
          <p className="mb-3 px-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Workspace
          </p>
          {navItems.map(({ label, icon: Icon }) => {
            const hasPendingBadge = label === 'Agents' && pendingApproval
            return (
              <button
                key={label}
                onClick={() => {
                  setActive(label)
                  setMobileNav(false)
                }}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                  active === label
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-sm'
                    : 'text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-foreground'
                )}
              >
                <Icon className="size-4 shrink-0" />
                <span>{label}</span>
                {hasPendingBadge && (
                  <span className="ml-auto rounded-full bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400">
                    1
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer info */}
        <div className="mt-auto space-y-2">
          {/* Memory health widget */}
          <div className="rounded-xl border border-sidebar-border bg-sidebar-accent/30 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                Memory health
              </span>
              <CircleDot className="size-3 text-emerald-500" />
            </div>
            <div className="mb-2 flex items-end justify-between">
              <span className="text-lg font-medium">{memoryHealthScore}%</span>
              <span className="text-[10px] text-muted-foreground">
                {memoriesList.length} indexed
              </span>
            </div>
            <div className="h-1 overflow-hidden rounded-full bg-border">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                style={{ width: `${memoryHealthScore}%` }}
              />
            </div>
          </div>

          <button
            onClick={() => router.push('/settings')}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-foreground"
          >
            <Settings2 className="size-4 shrink-0" />
            Settings
          </button>

          {/* User profile */}
          <div className="flex items-center gap-2 border-t border-sidebar-border px-3 pt-3">
            <div className="grid size-7 place-items-center rounded-full bg-gradient-to-br from-violet-400 to-blue-500 text-xs font-semibold text-white shadow-xs">
              {userInitials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium">{user?.full_name || user?.username || 'User'}</p>
              <p className="truncate text-[10px] text-muted-foreground">{user?.email || 'Authenticated'}</p>
            </div>
            <button
              onClick={() => logoutMutation.mutate()}
              title="Log out"
              className="rounded-md p-1.5 text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
            >
              <LogOut className="size-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {mobileNav && (
        <button
          className="fixed inset-0 z-30 bg-black/20 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileNav(false)}
          aria-label="Close navigation overlay"
        />
      )}

      {/* Main Content Area */}
      <main className="lg:pl-[248px]">
        {/* Sticky Header */}
        <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-border bg-background/90 px-5 backdrop-blur-md sm:px-8">
          <div className="flex items-center gap-3">
            <button
              className="rounded-md p-2 hover:bg-muted lg:hidden"
              onClick={() => setMobileNav(true)}
              aria-label="Open navigation"
            >
              <Menu className="size-5" />
            </button>
            <div>
              <p className="text-xs text-muted-foreground">
                {active === 'Overview'
                  ? new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
                  : `Workspace / ${active}`}
              </p>
              <h1 className="text-sm font-semibold tracking-tight">
                {active === 'Overview'
                  ? `Welcome, ${user?.full_name?.split(' ')[0] || user?.username || 'Pilot'}`
                  : active}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative hidden sm:block">
              <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search workspace..."
                className="h-8 w-48 rounded-md border border-border bg-card pl-8 pr-3 text-xs outline-none focus:w-64 focus:border-foreground/40 transition-all"
              />
            </div>
            <button
              onClick={() => router.push('/settings')}
              className="grid size-8 place-items-center rounded-full bg-muted text-xs font-semibold hover:bg-muted/80"
              aria-label="Open profile settings"
            >
              {userInitials}
            </button>
          </div>
        </header>

        {/* View container */}
        <div className="mx-auto max-w-[1400px] p-5 sm:p-8">
          {notice && (
            <div className="mb-5 flex items-center justify-between gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2.5 text-xs text-blue-800 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 shrink-0" />
                <span>{notice}</span>
              </div>
              <button onClick={() => setNotice('')} className="text-blue-600 hover:text-blue-800">
                <X className="size-3.5" />
              </button>
            </div>
          )}

          {active === 'Overview' && (
            <Overview
              onAction={handleQuickAction}
              memories={filteredMemories}
              totalMemories={memoriesData?.total || memoriesList.length}
              documentCount={documentMemories.length}
              pendingApproval={pendingApproval}
              onSelectMemory={(m) => setSelectedMemory(m)}
            />
          )}

          {active === 'Assistant' && (
            <AssistantView
              pendingApproval={pendingApproval}
              setPendingApproval={setPendingApproval}
              showNotification={showNotification}
            />
          )}

          {active === 'Memory' && (
            <MemoryView
              memories={filteredMemories}
              query={query}
              setQuery={setQuery}
              isLoading={memoriesLoading}
              onAction={handleQuickAction}
              onSelectMemory={(m) => setSelectedMemory(m)}
              onDeleteMemory={(id) => {
                deleteMemoryMutation.mutate(id, {
                  onSuccess: () => showNotification('Memory successfully deleted.'),
                })
              }}
            />
          )}

          {active === 'Graph' && (
            <GraphView
              graphData={graphData}
              isLoading={graphLoading}
              onAction={handleQuickAction}
            />
          )}

          {active === 'Documents' && (
            <DocumentsView
              documentMemories={documentMemories}
              onUploadSuccess={() => {
                refetchMemories()
                showNotification('Document uploaded and indexed successfully into persistent memory.')
              }}
            />
          )}

          {active === 'Agents' && (
            <AgentsView
              pendingApproval={pendingApproval}
              onReview={() => setActive('Assistant')}
              onAction={handleQuickAction}
            />
          )}

          {active === 'Activity' && (
            <ActivityView memories={memoriesList} />
          )}
        </div>
      </main>

      {/* Memory Creation Modal */}
      {createMemoryOpen && (
        <CreateMemoryModal
          onClose={() => setCreateMemoryOpen(false)}
          onSuccess={() => {
            setCreateMemoryOpen(false)
            refetchMemories()
            showNotification('New memory recorded and vectorized successfully.')
          }}
        />
      )}

      {/* Memory Detail Modal */}
      {selectedMemory && (
        <MemoryDetailModal
          memory={selectedMemory}
          onClose={() => setSelectedMemory(null)}
          onDelete={(id) => {
            deleteMemoryMutation.mutate(id, {
              onSuccess: () => {
                setSelectedMemory(null)
                showNotification('Memory deleted.')
              },
            })
          }}
        />
      )}
    </div>
  )
}

function SectionHeading({ eyebrow, title, action }: { eyebrow: string; title: string; action?: ReactNode }) {
  return (
    <div className="mb-5 flex items-end justify-between">
      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {eyebrow}
        </p>
        <h2 className="text-xl font-semibold tracking-[-0.03em]">{title}</h2>
      </div>
      {action}
    </div>
  )
}

function Overview({
  onAction,
  memories,
  totalMemories,
  documentCount,
  pendingApproval,
  onSelectMemory,
}: {
  onAction: (s: string) => void
  memories: Memory[]
  totalMemories: number
  documentCount: number
  pendingApproval: AgentChatResponse | null
  onSelectMemory: (m: Memory) => void
}) {
  return (
    <div className="space-y-8">
      {/* Hero Banner */}
      <section className="relative overflow-hidden rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-xs">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            <Sparkles className="size-3 text-violet-500" /> Your second brain, online
          </div>
          <h2 className="max-w-xl text-3xl font-semibold tracking-[-0.045em] sm:text-4xl text-foreground">
            What would you like to make sense of?
          </h2>
          <p className="mt-3 max-w-lg text-sm leading-6 text-muted-foreground">
            Ask a grounded question, explore persistent memory, or let SynapseOS execute verified multi-step tasks with strict approval gates.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onAction('Ask the assistant')}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-transform hover:-translate-y-0.5"
            >
              Open assistant <ArrowUpRight className="size-4" />
            </button>
            <button
              onClick={() => onAction('Add memory')}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              <Plus className="size-4" /> Add memory
            </button>
          </div>
        </div>
        <div className="pointer-events-none absolute -right-16 -top-24 size-80 rounded-full bg-violet-400/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 right-20 size-32 rounded-full bg-blue-400/10 blur-2xl" />
      </section>

      {/* Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Memories" value={String(totalMemories)} detail="persistent memories" icon={Brain} />
        <Stat label="Documents" value={String(documentCount)} detail="indexed sources" icon={FileText} />
        <Stat
          label="Agent Status"
          value={pendingApproval ? '1 Action' : 'Idle'}
          detail={pendingApproval ? 'Awaiting human approval' : 'Ready for instruction'}
          icon={Zap}
        />
      </div>

      {/* Recent Memories & Needs Your Attention */}
      <div className="grid gap-8 xl:grid-cols-[1.25fr_.75fr]">
        <section>
          <SectionHeading
            eyebrow="Knowledge base"
            title="Recent memories"
            action={
              <button
                onClick={() => onAction('View all memories')}
                className="text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                View all <ArrowUpRight className="ml-1 inline size-3" />
              </button>
            }
          />
          <div className="space-y-3">
            {memories.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center">
                <Brain className="mx-auto size-6 text-muted-foreground" />
                <p className="mt-2 text-sm font-medium">No memories recorded yet</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Create your first thought, reflection, or upload a document to get started.
                </p>
                <Button size="sm" className="mt-4" onClick={() => onAction('Add memory')}>
                  <Plus className="size-3.5 mr-1" /> Create memory
                </Button>
              </div>
            ) : (
              memories.slice(0, 4).map((memory) => (
                <MemoryRow key={memory.id} memory={memory} onClick={() => onSelectMemory(memory)} />
              ))
            )}
          </div>
        </section>

        <section>
          <SectionHeading eyebrow="Needs your attention" title="Pending actions" />
          <div className="space-y-3">
            {pendingApproval ? (
              <div className="rounded-xl border border-amber-300 bg-amber-50/70 p-4 dark:border-amber-900/60 dark:bg-amber-950/30">
                <div className="flex gap-3">
                  <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-amber-500/20 text-amber-700 dark:text-amber-300">
                    <ShieldAlert className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
                      Approval Required: {pendingApproval.plan.goal}
                    </p>
                    <p className="mt-1 text-xs text-amber-800/80 dark:text-amber-300/80">
                      Tool: {pendingApproval.pending_step?.tool_name} requires your confirmation before execution.
                    </p>
                    <button
                      onClick={() => onAction('Review pending approval')}
                      className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-amber-700"
                    >
                      Review action <ArrowUpRight className="size-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card p-4">
                <div className="flex gap-3">
                  <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-emerald-500/10 text-emerald-600">
                    <ShieldCheck className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium">All Clear</p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">
                      No consequential agent operations are currently waiting for human approval.
                    </p>
                  </div>
                </div>
              </div>
            )}
            <ActionCard
              icon={UploadCloud}
              title="Add source documents"
              detail="Upload Markdown, PDF, or text files to ingest and vectorize into RAG retrieval."
              button="Upload"
              onAction={() => onAction('Upload document')}
            />
          </div>
        </section>
      </div>

      {/* Pulse & Graph preview */}
      <div className="grid gap-8 xl:grid-cols-[.95fr_1.05fr]">
        <section>
          <SectionHeading eyebrow="System pulse" title="Knowledge activity" />
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-3xl font-semibold tracking-[-0.04em]">{totalMemories}</p>
                <p className="mt-1 text-xs text-muted-foreground">memories actively vectorized</p>
              </div>
              <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-600">
                Active Qdrant
              </span>
            </div>
            <div className="mt-7 flex h-20 items-end gap-2">
              {[28, 42, 35, 60, 52, 75, 64, 88, 80, 95, 78, 100, 90, 85].map((height, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t-sm bg-primary/10 transition-colors hover:bg-primary/30"
                  style={{ height: `${height}%` }}
                >
                  <div className="h-1/2 w-full rounded-t-sm bg-primary/30" />
                </div>
              ))}
            </div>
            <div className="mt-2 flex justify-between text-[10px] text-muted-foreground">
              <span>Synchronized</span>
              <span>Online</span>
            </div>
          </div>
        </section>

        <section>
          <SectionHeading
            eyebrow="Explore"
            title="Your knowledge graph"
            action={
              <button
                onClick={() => onAction('Explore graph')}
                className="text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                Open graph <ArrowUpRight className="ml-1 inline size-3" />
              </button>
            }
          />
          <div className="relative h-[178px] overflow-hidden rounded-xl border border-border bg-card">
            <GraphLines small />
          </div>
        </section>
      </div>
    </div>
  )
}

function Stat({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string
  value: string
  detail: string
  icon: typeof Brain
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="mb-5 flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <Icon className="size-4 text-muted-foreground" />
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-semibold tracking-[-0.04em]">{value}</span>
        <span className="text-[10px] text-muted-foreground">{detail}</span>
      </div>
    </div>
  )
}

function MemoryRow({ memory, onClick }: { memory: Memory; onClick?: () => void }) {
  const tone =
    memory.memory_type === 'reflection' || memory.memory_type === 'knowledge'
      ? 'violet'
      : memory.memory_type === 'document'
      ? 'emerald'
      : memory.memory_type === 'task' || memory.memory_type === 'project'
      ? 'amber'
      : 'blue'

  const formattedDate = new Date(memory.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })

  return (
    <button
      onClick={onClick}
      className="group flex w-full items-start gap-4 rounded-xl border border-border bg-card p-4 text-left transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-xs"
    >
      <span
        className={cn(
          'mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg',
          tone === 'violet'
            ? 'bg-violet-500/10 text-violet-600'
            : tone === 'emerald'
            ? 'bg-emerald-500/10 text-emerald-600'
            : tone === 'amber'
            ? 'bg-amber-500/10 text-amber-600'
            : 'bg-blue-500/10 text-blue-600'
        )}
      >
        <Brain className="size-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium truncate">{memory.title}</span>
          <span className="shrink-0 text-[10px] text-muted-foreground">{formattedDate}</span>
        </span>
        <span className="mt-1 block truncate text-xs leading-5 text-muted-foreground">
          {memory.summary || memory.content}
        </span>
        <span className="mt-2 inline-flex items-center gap-1.5">
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground capitalize">
            {memory.memory_type}
          </span>
          {memory.tags?.slice(0, 2).map((tag) => (
            <span key={tag} className="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
              #{tag}
            </span>
          ))}
        </span>
      </span>
      <ArrowUpRight className="mt-1 size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
    </button>
  )
}

function ActionCard({
  icon: Icon,
  title,
  detail,
  button,
  onAction,
}: {
  icon: typeof ShieldCheck
  title: string
  detail: string
  button: string
  onAction?: () => void
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex gap-3">
        <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-muted text-foreground">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{title}</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p>
          <button
            onClick={onAction}
            className="mt-3 text-xs font-medium text-foreground underline underline-offset-4 hover:text-primary"
          >
            {button}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Assistant View ─────────────────────────────────────────────────── */

interface ChatHistoryItem {
  id: string
  sender: 'user' | 'assistant'
  text: string
  mode: 'agent' | 'rag'
  agentData?: AgentChatResponse
  ragData?: RAGQueryResponse
}

function AssistantView({
  pendingApproval,
  setPendingApproval,
  showNotification,
}: {
  pendingApproval: AgentChatResponse | null
  setPendingApproval: (resp: AgentChatResponse | null) => void
  showNotification: (msg: string) => void
}) {
  const { currentWorkspace } = useWorkspaceStore()
  const [mode, setMode] = useState<'agent' | 'rag'>('agent')
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState<ChatHistoryItem[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const agentChatMutation = useAgentChat()
  const agentApproveMutation = useAgentApprove()
  const ragQueryMutation = useRAGQuery()

  const isSubmitting = agentChatMutation.isPending || ragQueryMutation.isPending || agentApproveMutation.isPending

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, isSubmitting])

  async function handleSend(customPrompt?: string) {
    const textToSend = customPrompt || message.trim()
    if (!textToSend || !currentWorkspace || isSubmitting) return

    if (!customPrompt) setMessage('')

    const userEntry: ChatHistoryItem = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      mode,
    }
    setHistory((prev) => [...prev, userEntry])

    if (mode === 'agent') {
      try {
        const resp = await agentChatMutation.mutateAsync({
          message: textToSend,
          workspace_id: currentWorkspace.id,
        })

        if (resp.status === 'awaiting_approval') {
          setPendingApproval(resp)
        }

        setHistory((prev) => [
          ...prev,
          {
            id: `agent-${Date.now()}`,
            sender: 'assistant',
            text: resp.message,
            mode: 'agent',
            agentData: resp,
          },
        ])
      } catch (err: unknown) {
        const errorDetail = err instanceof Error ? err.message : 'Agent invocation failed'
        setHistory((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: 'assistant',
            text: `Agent encountered an error: ${errorDetail}`,
            mode: 'agent',
          },
        ])
      }
    } else {
      // RAG Query Mode
      try {
        const resp = await ragQueryMutation.mutateAsync({
          query: textToSend,
          workspace_id: currentWorkspace.id,
        })

        setHistory((prev) => [
          ...prev,
          {
            id: `rag-${Date.now()}`,
            sender: 'assistant',
            text: resp.answer,
            mode: 'rag',
            ragData: resp,
          },
        ])
      } catch (err: unknown) {
        const errorDetail = err instanceof Error ? err.message : 'RAG retrieval failed'
        setHistory((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: 'assistant',
            text: `RAG query error: ${errorDetail}`,
            mode: 'rag',
          },
        ])
      }
    }
  }

  async function handleApproval(sessionId: string, approved: boolean) {
    if (!currentWorkspace) return
    try {
      const resp = await agentApproveMutation.mutateAsync({
        session_id: sessionId,
        approved,
        workspace_id: currentWorkspace.id,
      })

      setPendingApproval(null)
      showNotification(approved ? 'Action approved and executed.' : 'Action rejected.')

      setHistory((prev) => [
        ...prev,
        {
          id: `approve-${Date.now()}`,
          sender: 'assistant',
          text: approved
            ? `Action approved and executed. ${resp.message}`
            : `Action rejected. Execution halted safely.`,
          mode: 'agent',
          agentData: resp,
        },
      ])
    } catch (err: unknown) {
      const errorDetail = err instanceof Error ? err.message : 'Approval handling failed'
      showNotification(`Failed to submit approval: ${errorDetail}`)
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-180px)] max-w-4xl flex-col">
      {/* Top Bar */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Personal copilot
          </p>
          <h2 className="text-2xl font-semibold tracking-[-0.04em]">Assistant</h2>
        </div>
        <div className="flex items-center gap-3">
          {/* Mode Switcher */}
          <div className="flex rounded-lg border border-border bg-card p-1 text-xs">
            <button
              onClick={() => setMode('agent')}
              className={cn(
                'rounded-md px-3 py-1 font-medium transition-colors',
                mode === 'agent'
                  ? 'bg-primary text-primary-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Agent Reasoning
            </button>
            <button
              onClick={() => setMode('rag')}
              className={cn(
                'rounded-md px-3 py-1 font-medium transition-colors',
                mode === 'rag'
                  ? 'bg-primary text-primary-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Grounded RAG
            </button>
          </div>

          <span className="flex items-center gap-2 rounded-full border border-border bg-card px-2.5 py-1 text-[10px] text-muted-foreground">
            <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
            NVIDIA Nemotron · Nebius
          </span>
        </div>
      </div>

      {/* Conversation area */}
      <div className="flex-1 space-y-6 pb-6">
        {pendingApproval && (
          <div className="rounded-xl border border-amber-300 bg-amber-50/90 p-4 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <ShieldAlert className="size-4 shrink-0 text-amber-600 dark:text-amber-400" />
              <span>
                Action Pending Approval: <strong>{pendingApproval.plan.goal}</strong> ({pendingApproval.pending_step?.tool_name})
              </span>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                className="h-8 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={() => handleApproval(pendingApproval.session_id, true)}
                disabled={isSubmitting}
              >
                <Check className="size-3 mr-1" /> Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-8 text-xs border-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40"
                onClick={() => handleApproval(pendingApproval.session_id, false)}
                disabled={isSubmitting}
              >
                <X className="size-3 mr-1" /> Reject
              </Button>
            </div>
          </div>
        )}

        {history.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center py-12 text-center">
            <div className="mb-5 grid size-14 place-items-center rounded-2xl border border-border bg-card shadow-xs">
              <Sparkles className="size-6 text-violet-500" />
            </div>
            <h3 className="text-xl font-semibold tracking-[-0.03em]">Ask anything in your knowledge base</h3>
            <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
              SynapseOS will retrieve relevant context, display evidence citations, execute verified tools, and request your approval for consequential actions.
            </p>
            <div className="mt-8 grid w-full gap-2 sm:grid-cols-3">
              {[
                'What did I decide about the launch?',
                'Summarize my product principles',
                'What is the GPU architecture used?',
              ].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  className="rounded-lg border border-border bg-card p-3 text-left text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          history.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'flex gap-3 rounded-xl p-4 sm:p-5',
                msg.sender === 'user'
                  ? 'bg-muted/50 border border-border ml-8'
                  : 'bg-card border border-border mr-8 shadow-xs'
              )}
            >
              <span
                className={cn(
                  'grid size-8 shrink-0 place-items-center rounded-lg',
                  msg.sender === 'user' ? 'bg-foreground text-background' : 'bg-primary text-primary-foreground'
                )}
              >
                {msg.sender === 'user' ? (
                  <span className="text-xs font-bold">U</span>
                ) : (
                  <Sparkles className="size-4" />
                )}
              </span>
              <div className="min-w-0 flex-1 space-y-3">
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>

                {/* Grounded RAG Citations */}
                {msg.ragData && msg.ragData.citations && msg.ragData.citations.length > 0 && (
                  <div className="mt-3 space-y-2 border-t border-border pt-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      Evidence Citations ({msg.ragData.citations.length})
                    </p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {msg.ragData.citations.map((c) => (
                        <div
                          key={c.citation_index}
                          className="rounded-lg border border-border bg-background/50 p-2.5 text-xs"
                        >
                          <div className="flex items-center justify-between text-[10px] text-muted-foreground mb-1">
                            <span className="font-semibold text-foreground">
                              [{c.citation_index}] {c.title}
                            </span>
                            <span>{Math.round(c.similarity_score * 100)}% match</span>
                          </div>
                          <p className="text-[11px] text-muted-foreground line-clamp-3 italic">
                            &ldquo;{c.excerpt}&rdquo;
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Strict Abstention Guard Alert */}
                {msg.ragData?.is_unsupported && (
                  <div className="mt-2 flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300">
                    <AlertTriangle className="size-4 shrink-0" />
                    <span>
                      Evidence Insufficient: SynapseOS strictly abstained from hallucinating facts not grounded in your memory.
                    </span>
                  </div>
                )}

                {/* Agent Plan Steps */}
                {msg.agentData?.plan && msg.agentData.plan.steps.length > 0 && (
                  <div className="mt-3 space-y-2 border-t border-border pt-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      Execution Plan ({msg.agentData.plan.steps.length} steps)
                    </p>
                    <div className="space-y-1.5">
                      {msg.agentData.plan.steps.map((s) => (
                        <div
                          key={s.step_number}
                          className="flex items-center justify-between rounded-lg border border-border bg-background/50 px-3 py-2 text-xs"
                        >
                          <div className="flex items-center gap-2">
                            {s.status === 'completed' ? (
                              <Check className="size-3.5 text-emerald-500" />
                            ) : s.status === 'awaiting_approval' ? (
                              <Lock className="size-3.5 text-amber-500" />
                            ) : (
                              <CircleDot className="size-3.5 text-muted-foreground" />
                            )}
                            <span className="font-medium">
                              Step {s.step_number}: {s.description}
                            </span>
                          </div>
                          <span className="font-mono text-[10px] text-muted-foreground">
                            {s.tool_name}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Consequential Approval Gate Action */}
                {msg.agentData?.status === 'awaiting_approval' && msg.agentData.pending_step && (
                  <div className="mt-4 rounded-xl border border-amber-300 bg-amber-50/80 p-4 dark:border-amber-900/70 dark:bg-amber-950/30">
                    <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-semibold text-xs uppercase tracking-[0.14em]">
                      <ShieldAlert className="size-4" />
                      Human Approval Required
                    </div>
                    <p className="mt-2 text-sm font-medium text-amber-950 dark:text-amber-100">
                      Tool: <code className="rounded bg-amber-200/50 px-1 py-0.5 text-xs">{msg.agentData.pending_step.tool_name}</code>
                    </p>
                    <p className="mt-1 text-xs text-amber-900/80 dark:text-amber-300/80">
                      {msg.agentData.pending_step.description}
                    </p>
                    <div className="mt-4 flex gap-2">
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        onClick={() => handleApproval(msg.agentData!.session_id, true)}
                        disabled={isSubmitting}
                      >
                        <Check className="size-3.5 mr-1" /> Approve Execution
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40"
                        onClick={() => handleApproval(msg.agentData!.session_id, false)}
                        disabled={isSubmitting}
                      >
                        <X className="size-3.5 mr-1" /> Reject
                      </Button>
                    </div>
                  </div>
                )}

                {/* Reflection Output */}
                {msg.agentData?.reflection && (
                  <div className="mt-3 rounded-lg border border-violet-200 bg-violet-50/50 p-3 text-xs dark:border-violet-900/40 dark:bg-violet-950/20">
                    <p className="font-semibold text-violet-900 dark:text-violet-200 flex items-center gap-1.5">
                      <Brain className="size-3.5" /> Reflection Learned
                    </p>
                    <ul className="mt-1.5 list-disc pl-4 text-violet-800/80 dark:text-violet-300/80 space-y-0.5">
                      {msg.agentData.reflection.lessons_learned.map((lesson, idx) => (
                        <li key={idx}>{lesson}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isSubmitting && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground p-4">
            <Loader2 className="size-4 animate-spin text-primary" />
            <span>Reasoning via NVIDIA Nemotron...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input box */}
      <div className="sticky bottom-0 rounded-xl border border-border bg-card p-3 shadow-md backdrop-blur-md">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder={
            mode === 'agent'
              ? 'Instruct SynapseOS to plan, reason, or execute a task...'
              : 'Search verified context with grounded RAG citations...'
          }
          className="min-h-20 w-full resize-none bg-transparent p-2 text-sm outline-none placeholder:text-muted-foreground"
          aria-label="Message the assistant"
        />
        <div className="flex items-center justify-between border-t border-border pt-3">
          <span className="text-[10px] text-muted-foreground">
            {mode === 'agent' ? 'Autonomous multi-step planning · Approval gates' : 'Grounded answers · Source citations'}
          </span>
          <Button size="sm" onClick={() => handleSend()} disabled={!message.trim() || isSubmitting}>
            {isSubmitting ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <>
                Send <Send className="size-3.5 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

/* ── Memory View ────────────────────────────────────────────────────── */

function MemoryView({
  memories,
  query,
  setQuery,
  isLoading,
  onAction,
  onSelectMemory,
  onDeleteMemory,
}: {
  memories: Memory[]
  query: string
  setQuery: (s: string) => void
  isLoading: boolean
  onAction: (s: string) => void
  onSelectMemory: (m: Memory) => void
  onDeleteMemory: (id: string) => void
}) {
  const [selectedType, setSelectedType] = useState<string>('all')

  const displayedMemories = useMemo(() => {
    if (selectedType === 'all') return memories
    return memories.filter((m) => m.memory_type === selectedType)
  }, [memories, selectedType])

  return (
    <div>
      <SectionHeading
        eyebrow="Knowledge base"
        title="Persistent Memory"
        action={
          <Button size="sm" onClick={() => onAction('Add memory')}>
            <Plus className="size-4 mr-1" /> Add memory
          </Button>
        }
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memories, tags, or content..."
            className="h-10 w-full rounded-lg border border-input bg-card pl-9 pr-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="h-10 rounded-lg border border-input bg-card px-3 text-xs font-medium text-foreground outline-none"
        >
          <option value="all">All types</option>
          <option value="knowledge">Knowledge</option>
          <option value="document">Document</option>
          <option value="conversation">Conversation</option>
          <option value="reflection">Reflection</option>
          <option value="task">Task</option>
          <option value="preference">Preference</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-primary" />
        </div>
      ) : displayedMemories.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center">
          <Search className="mx-auto size-6 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium">No memories found</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Try adjusting your search query or record your first memory.
          </p>
          <Button size="sm" className="mt-4" onClick={() => onAction('Add memory')}>
            <Plus className="size-3.5 mr-1" /> Create memory
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {displayedMemories.map((m) => (
            <div
              key={m.id}
              className="group relative flex flex-col justify-between rounded-xl border border-border bg-card p-5 text-left transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-xs"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground capitalize">
                    {m.memory_type}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {new Date(m.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="mt-2 text-base font-semibold leading-tight line-clamp-1">{m.title}</h3>
                <p className="mt-1.5 text-xs leading-5 text-muted-foreground line-clamp-3">
                  {m.summary || m.content}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                <div className="flex flex-wrap gap-1">
                  {m.tags?.slice(0, 2).map((tag) => (
                    <span key={tag} className="rounded-md border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                      #{tag}
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => onSelectMemory(m)}
                    className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                    title="View details"
                  >
                    <ArrowUpRight className="size-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (confirm(`Delete memory "${m.title}"?`)) onDeleteMemory(m.id)
                    }}
                    className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    title="Delete memory"
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Graph View ─────────────────────────────────────────────────────── */

function GraphView({
  graphData,
  isLoading,
  onAction,
}: {
  graphData?: { nodes: GraphNode[]; edges: unknown[] }
  isLoading: boolean
  onAction: (s: string) => void
}) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const nodes = graphData?.nodes || []

  return (
    <div>
      <SectionHeading
        eyebrow="Connected knowledge"
        title="Knowledge Graph"
        action={
          <div className="flex items-center gap-2">
            <span className="rounded-full border border-border px-2.5 py-1 text-[10px] text-muted-foreground">
              {nodes.length} nodes connected
            </span>
            <Button variant="outline" size="sm" onClick={() => onAction('Add memory')}>
              <Plus className="size-3.5 mr-1" /> Add node
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[1fr_300px]">
        <div className="relative min-h-[520px] overflow-hidden rounded-xl border border-border bg-card">
          {isLoading ? (
            <div className="flex h-[520px] items-center justify-center">
              <Loader2 className="size-6 animate-spin text-primary" />
            </div>
          ) : nodes.length === 0 ? (
            <div className="flex h-[520px] flex-col items-center justify-center p-8 text-center">
              <GitBranch className="size-10 text-muted-foreground/50 mb-3" />
              <p className="text-base font-medium">Knowledge Graph Initializing</p>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground">
                When you create memories or upload documents, SynapseOS extracts semantic entities and establishes knowledge edges.
              </p>
              <Button size="sm" className="mt-4" onClick={() => onAction('Add memory')}>
                Create First Memory
              </Button>
            </div>
          ) : (
            <div className="relative h-[520px] w-full">
              <GraphCanvas
                nodes={nodes}
                onSelect={(node) => setSelectedNode(node)}
                selectedNodeId={selectedNode?.id}
              />
            </div>
          )}
        </div>

        {/* Node Detail Inspector */}
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Selected node
          </p>
          {selectedNode ? (
            <div className="mt-4 space-y-4">
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-lg bg-violet-500/10 text-violet-600">
                  <Brain className="size-4" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{selectedNode.label}</p>
                  <p className="text-[11px] text-muted-foreground capitalize">
                    {selectedNode.memory_type || selectedNode.type}
                  </p>
                </div>
              </div>
              <div className="border-t border-border pt-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {selectedNode.metadata?.content
                    ? String(selectedNode.metadata.content)
                    : 'Node relationship established in semantic memory graph.'}
                </p>
              </div>
            </div>
          ) : (
            <div className="mt-8 text-center text-xs text-muted-foreground">
              <HelpCircle className="mx-auto size-6 mb-2 opacity-50" />
              Click any node in the graph canvas to inspect its semantic connections.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function GraphCanvas({
  nodes,
  onSelect,
  selectedNodeId,
}: {
  nodes: GraphNode[]
  onSelect: (node: GraphNode) => void
  selectedNodeId?: string
}) {
  return (
    <div className="relative h-full w-full overflow-hidden bg-[radial-gradient(circle_at_center,hsl(var(--muted))_0,transparent_60%)]">
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 800 500" aria-label="Knowledge graph visualization">
        {/* Draw mock/radial connection lines */}
        <g stroke="currentColor" strokeOpacity=".18" strokeWidth="1">
          {nodes.slice(0, 10).map((_, i) => {
            const angle = (i / Math.min(nodes.length, 10)) * Math.PI * 2
            const x2 = 400 + Math.cos(angle) * 180
            const y2 = 250 + Math.sin(angle) * 140
            return <line key={i} x1={400} y1={250} x2={x2} y2={y2} />
          })}
        </g>
        {/* Draw Nodes */}
        <g>
          {nodes.slice(0, 10).map((node, i) => {
            const angle = (i / Math.min(nodes.length, 10)) * Math.PI * 2
            const cx = i === 0 ? 400 : 400 + Math.cos(angle) * 180
            const cy = i === 0 ? 250 : 250 + Math.sin(angle) * 140
            const isSelected = node.id === selectedNodeId
            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform hover:scale-110"
                onClick={() => onSelect(node)}
              >
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSelected ? 22 : 16}
                  className={cn(
                    'transition-colors',
                    isSelected
                      ? 'fill-primary stroke-foreground stroke-2'
                      : i === 0
                      ? 'fill-violet-500/20 stroke-violet-500 stroke-2'
                      : 'fill-card stroke-border stroke-2 hover:fill-muted'
                  )}
                />
                <text
                  x={cx}
                  y={cy + 28}
                  textAnchor="middle"
                  className="fill-foreground text-[10px] font-medium"
                >
                  {node.label.length > 14 ? `${node.label.slice(0, 12)}...` : node.label}
                </text>
              </g>
            )
          })}
        </g>
      </svg>
    </div>
  )
}

function GraphLines({ small = false }: { small?: boolean }) {
  return (
    <div
      className={cn(
        'relative h-full w-full overflow-hidden bg-[radial-gradient(circle_at_center,hsl(var(--muted))_0,transparent_55%)]',
        small ? 'min-h-[178px]' : 'min-h-[520px]'
      )}
    >
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 800 500" aria-label="Knowledge graph preview">
        <g stroke="currentColor" strokeOpacity=".16" strokeWidth="1">
          {[
            [400, 250, 205, 130],
            [400, 250, 580, 145],
            [400, 250, 210, 360],
            [400, 250, 590, 350],
            [205, 130, 110, 75],
            [205, 130, 120, 210],
            [580, 145, 685, 90],
            [580, 145, 690, 230],
          ].map(([x1, y1, x2, y2], i) => (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />
          ))}
        </g>
        <g fill="hsl(var(--card))" stroke="currentColor" strokeWidth="1.5">
          {[
            [400, 250, 20],
            [205, 130, 16],
            [580, 145, 16],
            [210, 360, 16],
            [590, 350, 16],
          ].map(([cx, cy, r], i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              className={
                i === 0
                  ? 'fill-violet-500/20 stroke-violet-500'
                  : i % 2
                  ? 'fill-blue-500/10 stroke-blue-500/50'
                  : 'fill-amber-500/10 stroke-amber-500/50'
              }
            />
          ))}
        </g>
      </svg>
    </div>
  )
}

/* ── Documents View ─────────────────────────────────────────────────── */

function DocumentsView({
  documentMemories,
  onUploadSuccess,
}: {
  documentMemories: Memory[]
  onUploadSuccess: () => void
}) {
  const { currentWorkspace } = useWorkspaceStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleFile(file: File) {
    if (!currentWorkspace) return
    setErrorMsg('')
    setUploading(true)
    try {
      await memoryApi.upload(currentWorkspace.id, file, {
        memoryType: 'document',
        tags: 'source,upload',
      })
      onUploadSuccess()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <SectionHeading
        eyebrow="Sources"
        title="Documents & Ingestion"
        action={
          <Button
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? <Loader2 className="size-4 animate-spin mr-1" /> : <UploadCloud className="size-4 mr-1" />}
            Upload document
          </Button>
        }
      />

      {errorMsg && (
        <div className="mb-4 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
          {errorMsg}
        </div>
      )}

      {/* Drag & drop upload area */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.pdf,.json,.csv"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0])
          }
        }}
      />

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragActive(false)
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0])
          }
        }}
        className={cn(
          'mb-8 rounded-xl border border-dashed p-8 text-center transition-colors',
          dragActive
            ? 'border-primary bg-primary/5'
            : 'border-border bg-card hover:border-foreground/30'
        )}
      >
        <UploadCloud className="mx-auto size-8 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium">Drop a document here to ingest and vectorize</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supports Markdown (.md), Text (.txt), PDF (.pdf), JSON (.json), and CSV (.csv)
        </p>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="mt-4 text-xs font-semibold underline underline-offset-4 hover:text-primary"
        >
          {uploading ? 'Ingesting document...' : 'Or choose a file from your computer'}
        </button>
      </div>

      {/* Documents List */}
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border p-4">
          <span className="text-sm font-semibold">Indexed Sources ({documentMemories.length})</span>
          <span className="text-xs text-muted-foreground">FastAPI vector store</span>
        </div>

        {documentMemories.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            No source documents uploaded yet. Ingest your first document above.
          </div>
        ) : (
          documentMemories.map((m) => (
            <div
              key={m.id}
              className="flex items-center gap-3 border-b border-border p-4 last:border-0 hover:bg-muted/30 transition-colors"
            >
              <FileText className="size-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{m.title}</p>
                <p className="text-[10px] text-muted-foreground">
                  Source: {m.source || 'Uploaded document'} · {new Date(m.created_at).toLocaleDateString()}
                </p>
              </div>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600">
                Vectorized
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

/* ── Agents View ────────────────────────────────────────────────────── */

function AgentsView({
  pendingApproval,
  onReview,
  onAction,
}: {
  pendingApproval: AgentChatResponse | null
  onReview: () => void
  onAction: (s: string) => void
}) {
  return (
    <div>
      <SectionHeading
        eyebrow="Bounded automation"
        title="Agents & Approvals"
        action={
          <Button size="sm" onClick={() => onAction('Ask the assistant')}>
            <Plus className="size-4 mr-1" /> New task
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pending approvals section */}
        <div className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Human Approval Gate
          </p>

          {pendingApproval ? (
            <div className="rounded-xl border border-amber-300 bg-amber-50/70 p-5 dark:border-amber-900/60 dark:bg-amber-950/20">
              <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300">
                <ShieldAlert className="size-4" />
                <span className="text-xs font-semibold uppercase tracking-[0.14em]">
                  Awaiting your approval
                </span>
              </div>
              <h3 className="mt-4 text-base font-semibold">{pendingApproval.plan.goal}</h3>
              <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                Step requires consequential tool authorization ({pendingApproval.pending_step?.tool_name}).
              </p>
              <div className="mt-5 flex gap-2">
                <Button size="sm" onClick={onReview}>
                  Review & Approve
                </Button>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card p-6 text-center">
              <ShieldCheck className="mx-auto size-7 text-emerald-500 mb-2" />
              <p className="text-sm font-medium">No actions awaiting approval</p>
              <p className="mt-1 text-xs text-muted-foreground">
                When the agent plans consequential operations, execution halts until authorized.
              </p>
            </div>
          )}
        </div>

        {/* Safety & Architecture Guardrails */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Safety Controls Active
          </p>
          <div className="space-y-3">
            {[
              { title: 'Cross-user approval session isolation', status: 'Enforced' },
              { title: 'SSRF validation on web research tools', status: 'Enforced' },
              { title: 'Workspace tenant resource isolation', status: 'Enforced' },
              { title: 'Automatic post-action reflection engine', status: 'Active' },
            ].map((item) => (
              <div key={item.title} className="flex items-center justify-between text-xs py-1.5 border-b border-border last:border-0">
                <span className="text-muted-foreground">{item.title}</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">{item.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Activity View ──────────────────────────────────────────────────── */

function ActivityView({ memories }: { memories: Memory[] }) {
  return (
    <div>
      <SectionHeading eyebrow="System log" title="Activity & Audit Trail" />
      <div className="rounded-xl border border-border bg-card">
        {memories.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            No activity events recorded yet.
          </div>
        ) : (
          memories.slice(0, 15).map((m) => (
            <div
              key={m.id}
              className="flex items-center gap-4 border-b border-border p-4 last:border-0"
            >
              <span className="grid size-7 shrink-0 place-items-center rounded-full bg-muted">
                <Activity className="size-3.5 text-muted-foreground" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  Memory recorded: &ldquo;{m.title}&rdquo;
                </p>
                <p className="text-[10px] text-muted-foreground capitalize">
                  Type: {m.memory_type} · ID: {m.id.slice(0, 8)}...
                </p>
              </div>
              <span className="text-[10px] text-muted-foreground">
                {new Date(m.created_at).toLocaleDateString()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

/* ── Create Memory Modal ────────────────────────────────────────────── */

function CreateMemoryModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void
  onSuccess: () => void
}) {
  const createMemoryMutation = useCreateMemory()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [memoryType, setMemoryType] = useState('knowledge')
  const [tags, setTags] = useState('')
  const [importance, setImportance] = useState(5)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim() || !content.trim()) return
    setErrorMsg('')

    try {
      await createMemoryMutation.mutateAsync({
        title,
        content,
        memory_type: memoryType,
        tags: tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
        importance_score: importance,
      })
      onSuccess()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to create memory')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-xl animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <h3 className="text-lg font-semibold">Record New Memory</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted text-muted-foreground">
            <X className="size-4" />
          </button>
        </div>

        {errorMsg && (
          <div className="mt-4 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1">Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. GPU Architecture Decisions"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1">Content</label>
            <textarea
              required
              rows={4}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your thought, rule, note, or observation..."
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/50 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">Type</label>
              <select
                value={memoryType}
                onChange={(e) => setMemoryType(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none"
              >
                <option value="knowledge">Knowledge</option>
                <option value="conversation">Conversation</option>
                <option value="document">Document</option>
                <option value="reflection">Reflection</option>
                <option value="preference">Preference</option>
                <option value="task">Task</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">Importance (1-10)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={importance}
                onChange={(e) => setImportance(Number(e.target.value))}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1">Tags (comma-separated)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="gpu, nebius, architecture"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none focus:border-foreground/50"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={createMemoryMutation.isPending}>
              {createMemoryMutation.isPending ? <Loader2 className="size-3.5 animate-spin mr-1" /> : null}
              Save Memory
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ── Memory Detail Modal ────────────────────────────────────────────── */

function MemoryDetailModal({
  memory,
  onClose,
  onDelete,
}: {
  memory: Memory
  onClose: () => void
  onDelete: (id: string) => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-xl animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase capitalize">
              {memory.memory_type}
            </span>
            <span className="text-xs text-muted-foreground">
              {new Date(memory.created_at).toLocaleDateString()}
            </span>
          </div>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted text-muted-foreground">
            <X className="size-4" />
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <h2 className="text-lg font-semibold">{memory.title}</h2>
          <div className="rounded-lg bg-muted/40 p-3 text-xs leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap">
            {memory.content}
          </div>

          {memory.summary && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Summary
              </p>
              <p className="text-xs text-muted-foreground">{memory.summary}</p>
            </div>
          )}

          {memory.tags && memory.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {memory.tags.map((tag) => (
                <span key={tag} className="rounded-md border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
                  #{tag}
                </span>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between border-t border-border pt-4">
            <span className="text-[10px] text-muted-foreground">
              Importance: {memory.importance_score}/10
            </span>
            <div className="flex gap-2">
              <Button
                variant="destructive"
                size="sm"
                onClick={() => {
                  if (confirm(`Delete memory "${memory.title}"?`)) onDelete(memory.id)
                }}
              >
                <Trash2 className="size-3.5 mr-1" /> Delete
              </Button>
              <Button variant="outline" size="sm" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
