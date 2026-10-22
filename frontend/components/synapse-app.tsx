'use client'

import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import {
  Activity,
  ArrowUpRight,
  Brain,
  Check,
  ChevronDown,
  CircleDot,
  Command,
  FileText,
  GitBranch,
  LayoutDashboard,
  Library,
  Menu,
  MessageSquareText,
  MoreHorizontal,
  Plus,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type NavKey = 'Overview' | 'Assistant' | 'Memory' | 'Graph' | 'Documents' | 'Agents' | 'Activity'

const navItems: { label: NavKey; icon: typeof LayoutDashboard }[] = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Assistant', icon: MessageSquareText },
  { label: 'Memory', icon: Brain },
  { label: 'Graph', icon: GitBranch },
  { label: 'Documents', icon: FileText },
  { label: 'Agents', icon: Zap },
  { label: 'Activity', icon: Activity },
]

const memories = [
  { title: 'Product principles', preview: 'A small set of durable rules for how the team makes decisions.', tag: 'Reflection', time: '2m ago', tone: 'violet' },
  { title: 'Q4 launch notes', preview: 'The launch sequence should preserve a quiet beta before public access.', tag: 'Note', time: 'Yesterday', tone: 'amber' },
  { title: 'Maya prefers concise updates', preview: 'Keep status reports focused on decisions, blockers, and next steps.', tag: 'Preference', time: 'Oct 18', tone: 'blue' },
]

export function SynapseApp() {
  const [active, setActive] = useState<NavKey>('Overview')
  const [mobileNav, setMobileNav] = useState(false)
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState('')
  const [sent, setSent] = useState(false)
  const [notice, setNotice] = useState('')

  const filteredMemories = useMemo(() => memories.filter((item) =>
    `${item.title} ${item.preview} ${item.tag}`.toLowerCase().includes(query.toLowerCase())), [query])

  function submitMessage() {
    if (!message.trim()) return
    setSent(true)
    setMessage('')
    setTimeout(() => setSent(false), 3500)
  }

  function quickAction(text: string) {
    setActive(text === 'Add memory' ? 'Memory' : text === 'Upload document' ? 'Documents' : 'Assistant')
    setNotice(`${text} is ready to connect to your FastAPI workspace.`)
    setTimeout(() => setNotice(''), 4000)
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside className={cn('fixed inset-y-0 left-0 z-40 flex w-[248px] flex-col border-r border-border bg-sidebar px-4 py-5 transition-transform lg:translate-x-0', mobileNav ? 'translate-x-0' : '-translate-x-full')}>
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2.5">
            <span className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground"><Brain className="size-4" /></span>
            <span className="font-semibold tracking-[-0.02em]">synapse<span className="text-muted-foreground">OS</span></span>
          </div>
          <button className="rounded-md p-1.5 text-muted-foreground hover:bg-sidebar-accent lg:hidden" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X className="size-4" /></button>
        </div>
        <div className="mt-8 flex items-center gap-2 rounded-lg border border-sidebar-border bg-sidebar-accent/50 px-3 py-2.5 text-left">
          <div className="grid size-7 place-items-center rounded-md bg-foreground text-xs font-semibold text-background">M</div>
          <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium">Maya&apos;s workspace</p><p className="text-[10px] text-muted-foreground">Personal knowledge base</p></div>
          <ChevronDown className="size-3.5 text-muted-foreground" />
        </div>
        <nav className="mt-8 space-y-1" aria-label="Primary navigation">
          <p className="mb-3 px-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">Workspace</p>
          {navItems.map(({ label, icon: Icon }) => <button key={label} onClick={() => { setActive(label); setMobileNav(false) }} className={cn('flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors', active === label ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-sm' : 'text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-foreground')}><Icon className="size-4" /><span>{label}</span>{label === 'Agents' && <span className="ml-auto rounded-full bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-600">2</span>}</button>)}
        </nav>
        <div className="mt-auto space-y-1">
          <div className="mb-4 rounded-xl border border-sidebar-border bg-sidebar-accent/30 p-3"><div className="mb-2 flex items-center justify-between"><span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Memory health</span><CircleDot className="size-3 text-emerald-500" /></div><div className="mb-2 flex items-end justify-between"><span className="text-lg font-medium">84%</span><span className="text-[10px] text-muted-foreground">well organized</span></div><div className="h-1 overflow-hidden rounded-full bg-border"><div className="h-full w-[84%] rounded-full bg-emerald-500" /></div></div>
          <button onClick={() => setNotice('Settings are available once the backend configuration is connected.')} className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-foreground"><Settings2 className="size-4" />Settings</button>
          <div className="flex items-center gap-2 border-t border-sidebar-border px-3 pt-4"><div className="grid size-7 place-items-center rounded-full bg-gradient-to-br from-violet-300 to-blue-400 text-xs font-semibold text-white">MC</div><div className="flex-1"><p className="text-xs font-medium">Maya Chen</p><p className="text-[10px] text-muted-foreground">Free workspace</p></div><MoreHorizontal className="size-4 text-muted-foreground" /></div>
        </div>
      </aside>
      {mobileNav && <button className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={() => setMobileNav(false)} aria-label="Close navigation overlay" />}

      <main className="lg:pl-[248px]">
        <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-border bg-background/90 px-5 backdrop-blur-md sm:px-8">
          <div className="flex items-center gap-3"><button className="rounded-md p-2 hover:bg-muted lg:hidden" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu className="size-5" /></button><div><p className="text-xs text-muted-foreground">{active === 'Overview' ? 'Tuesday, October 21, 2026' : 'Workspace / ' + active}</p><h1 className="text-sm font-semibold tracking-tight">{active === 'Overview' ? 'Good morning, Maya' : active}</h1></div></div>
          <div className="flex items-center gap-2"><button className="hidden items-center gap-2 rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted sm:flex"><Search className="size-3.5" />Search<span className="ml-3 rounded border border-border px-1.5 py-0.5 font-mono text-[10px]">⌘ K</span></button><button className="grid size-8 place-items-center rounded-full bg-muted text-xs font-semibold" aria-label="Open profile">MC</button></div>
        </header>

        <div className="mx-auto max-w-[1400px] p-5 sm:p-8">
          {notice && <div className="mb-5 flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2.5 text-xs text-blue-800 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200"><ShieldCheck className="size-4" />{notice}</div>}
          {active === 'Overview' && <Overview onAction={quickAction} filteredMemories={filteredMemories} query={query} setQuery={setQuery} />}
          {active === 'Assistant' && <Assistant message={message} setMessage={setMessage} onSubmit={submitMessage} sent={sent} />}
          {active === 'Memory' && <MemoryView memories={filteredMemories} query={query} setQuery={setQuery} onAction={quickAction} />}
          {active === 'Graph' && <GraphView />}
          {active === 'Documents' && <DocumentsView onAction={quickAction} />}
          {active === 'Agents' && <AgentsView onAction={quickAction} />}
          {active === 'Activity' && <ActivityView />}
        </div>
      </main>
    </div>
  )
}

function SectionHeading({ eyebrow, title, action }: { eyebrow: string; title: string; action?: ReactNode }) { return <div className="mb-5 flex items-end justify-between"><div><p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p><h2 className="text-xl font-semibold tracking-[-0.03em]">{title}</h2></div>{action}</div> }

function Overview({ onAction, filteredMemories, query, setQuery }: { onAction: (s: string) => void; filteredMemories: typeof memories; query: string; setQuery: (s: string) => void }) {
 return <div className="space-y-8"><section className="relative overflow-hidden rounded-2xl border border-border bg-card p-6 sm:p-8"><div className="relative z-10 max-w-2xl"><div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground"><Sparkles className="size-3 text-violet-500" /> Your second brain, online</div><h2 className="max-w-xl text-3xl font-semibold tracking-[-0.045em] sm:text-4xl">What would you like to make sense of?</h2><p className="mt-3 max-w-lg text-sm leading-6 text-muted-foreground">Ask a question, explore a memory, or let SynapseOS help you move a thought forward.</p><button onClick={() => onAction('Ask the assistant')} className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-transform hover:-translate-y-0.5">Open assistant <ArrowUpRight className="size-4" /></button></div><div className="pointer-events-none absolute -right-16 -top-24 size-80 rounded-full bg-violet-400/10 blur-3xl" /><div className="pointer-events-none absolute bottom-0 right-20 size-32 rounded-full bg-blue-400/10 blur-2xl" /></section>
 <div className="grid gap-4 sm:grid-cols-3"><Stat label="Memories" value="128" detail="+12 this month" icon={Brain} /><Stat label="Documents" value="24" detail="3 processing" icon={FileText} /><Stat label="Agent runs" value="07" detail="2 awaiting review" icon={Zap} /></div>
 <div className="grid gap-8 xl:grid-cols-[1.25fr_.75fr]"><section><SectionHeading eyebrow="Knowledge base" title="Recent memories" action={<button onClick={() => onAction('View all memories')} className="text-xs font-medium text-muted-foreground hover:text-foreground">View all <ArrowUpRight className="ml-1 inline size-3" /></button>} /><div className="space-y-3">{filteredMemories.map((memory) => <MemoryRow key={memory.title} memory={memory} />)}</div></section><section><SectionHeading eyebrow="Needs your attention" title="Pending actions" /><div className="space-y-3"><ActionCard icon={ShieldCheck} title="Review calendar draft" detail="Agent wants to prepare your weekly focus blocks" button="Review" /><ActionCard icon={UploadCloud} title="Finish importing notes" detail="Q4 research.md is ready to be indexed" button="Inspect" /></div></section></div>
 <div className="grid gap-8 xl:grid-cols-[.95fr_1.05fr]"><section><SectionHeading eyebrow="System pulse" title="Knowledge activity" /><div className="rounded-xl border border-border bg-card p-5"><div className="flex items-start justify-between"><div><p className="text-3xl font-semibold tracking-[-0.04em]">18</p><p className="mt-1 text-xs text-muted-foreground">retrievals this week</p></div><span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-600">+24%</span></div><div className="mt-7 flex h-20 items-end gap-2">{[24,38,32,54,48,68,58,84,72,92,74,100,88,76].map((height, i) => <div key={i} className="flex-1 rounded-t-sm bg-primary/10 transition-colors hover:bg-primary/30" style={{ height: `${height}%` }}><div className="h-1/2 w-full rounded-t-sm bg-primary/30" /></div>)}</div><div className="mt-2 flex justify-between text-[10px] text-muted-foreground"><span>Oct 08</span><span>Today</span></div></div></section><section><SectionHeading eyebrow="Explore" title="Your knowledge graph" action={<button onClick={() => onAction('Explore graph')} className="text-xs font-medium text-muted-foreground hover:text-foreground">Open graph <ArrowUpRight className="ml-1 inline size-3" /></button>} /><div className="relative h-[178px] overflow-hidden rounded-xl border border-border bg-card"><GraphMini /></div></section></div></div>
}

function Stat({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: typeof Brain }) { return <div className="rounded-xl border border-border bg-card p-4"><div className="mb-5 flex items-center justify-between"><span className="text-xs text-muted-foreground">{label}</span><Icon className="size-4 text-muted-foreground" /></div><div className="flex items-end justify-between"><span className="text-2xl font-semibold tracking-[-0.04em]">{value}</span><span className="text-[10px] text-muted-foreground">{detail}</span></div></div> }
function MemoryRow({ memory }: { memory: typeof memories[number] }) { return <button className="group flex w-full items-start gap-4 rounded-xl border border-border bg-card p-4 text-left transition-all hover:-translate-y-0.5 hover:border-foreground/20 hover:shadow-sm"><span className={cn('mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg', memory.tone === 'violet' ? 'bg-violet-500/10 text-violet-600' : memory.tone === 'amber' ? 'bg-amber-500/10 text-amber-600' : 'bg-blue-500/10 text-blue-600')}><Brain className="size-4" /></span><span className="min-w-0 flex-1"><span className="flex items-center justify-between gap-3"><span className="text-sm font-medium">{memory.title}</span><span className="shrink-0 text-[10px] text-muted-foreground">{memory.time}</span></span><span className="mt-1 block truncate text-xs leading-5 text-muted-foreground">{memory.preview}</span><span className="mt-2 inline-flex rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">{memory.tag}</span></span><ArrowUpRight className="mt-1 size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" /></button> }
function ActionCard({ icon: Icon, title, detail, button }: { icon: typeof ShieldCheck; title: string; detail: string; button: string }) { return <div className="rounded-xl border border-border bg-card p-4"><div className="flex gap-3"><span className="grid size-8 shrink-0 place-items-center rounded-lg bg-amber-500/10 text-amber-600"><Icon className="size-4" /></span><div className="min-w-0"><p className="text-sm font-medium">{title}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p><button className="mt-3 text-xs font-medium underline underline-offset-4">{button}</button></div></div></div> }

function Assistant({ message, setMessage, onSubmit, sent }: { message: string; setMessage: (s: string) => void; onSubmit: () => void; sent: boolean }) { return <div className="mx-auto flex min-h-[calc(100vh-180px)] max-w-4xl flex-col"><div className="mb-8 flex items-center justify-between"><div><p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Personal copilot</p><h2 className="text-2xl font-semibold tracking-[-0.04em]">Assistant</h2></div><span className="flex items-center gap-2 rounded-full border border-border px-2.5 py-1 text-[10px] text-muted-foreground"><span className="size-1.5 rounded-full bg-emerald-500" />Ready</span></div>{sent ? <div className="rounded-xl border border-border bg-card p-6"><div className="flex gap-3"><span className="grid size-8 place-items-center rounded-lg bg-violet-500/10 text-violet-600"><Sparkles className="size-4" /></span><div><p className="text-sm font-medium">I&apos;m ready when your workspace is connected.</p><p className="mt-1 text-sm leading-6 text-muted-foreground">This interface is wired for grounded answers, citations, and agent plans through your FastAPI backend. No response was fabricated.</p></div></div></div> : <div className="flex flex-1 flex-col items-center justify-center text-center"><div className="mb-5 grid size-14 place-items-center rounded-2xl border border-border bg-card shadow-sm"><Sparkles className="size-6 text-violet-500" /></div><h3 className="text-xl font-semibold tracking-[-0.03em]">Ask anything in your knowledge base</h3><p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">SynapseOS will retrieve the relevant context, show its sources, and make uncertainty visible.</p><div className="mt-8 grid w-full gap-2 sm:grid-cols-3">{['What did I decide about the launch?', 'Summarize my product principles', 'Find related notes'].map((prompt) => <button key={prompt} onClick={() => setMessage(prompt)} className="rounded-lg border border-border bg-card p-3 text-left text-xs text-muted-foreground transition-colors hover:bg-muted">{prompt}</button>)}</div></div>}<div className="mt-8 rounded-xl border border-border bg-card p-3 shadow-sm"><textarea value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); onSubmit() } }} placeholder="Ask your workspace anything..." className="min-h-20 w-full resize-none bg-transparent p-2 text-sm outline-none placeholder:text-muted-foreground" aria-label="Message the assistant" /><div className="flex items-center justify-between border-t border-border pt-3"><span className="text-[10px] text-muted-foreground">Grounded answers · source citations</span><Button size="sm" onClick={onSubmit} disabled={!message.trim()}>Send <Send className="size-3.5" /></Button></div></div></div> }

function MemoryView({ memories, query, setQuery, onAction }: { memories: typeof memories; query: string; setQuery: (s: string) => void; onAction: (s: string) => void }) { return <div><SectionHeading eyebrow="Knowledge base" title="Memory" action={<Button size="sm" onClick={() => onAction('Add memory')}><Plus className="size-4" />Add memory</Button>} /><div className="mb-6 flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search memories..." className="h-10 w-full rounded-lg border border-input bg-card pl-9 pr-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring" /></div><Button variant="outline" size="sm"><Library className="size-4" />All types <ChevronDown className="size-3.5" /></Button></div><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{memories.map((memory) => <MemoryRow key={memory.title} memory={memory} />)}</div>{memories.length === 0 && <EmptyState title="No memories found" detail="Try a different search or create your first memory." />}</div> }
function GraphView() { return <div><SectionHeading eyebrow="Connected knowledge" title="Knowledge graph" action={<div className="flex items-center gap-2"><span className="rounded-full border border-border px-2.5 py-1 text-[10px] text-muted-foreground">Preview data</span><Button variant="outline" size="sm"><Search className="size-4" />Find node</Button></div>} /><div className="grid gap-4 xl:grid-cols-[1fr_280px]"><div className="relative min-h-[520px] overflow-hidden rounded-xl border border-border bg-card"><GraphLarge /></div><div className="rounded-xl border border-border bg-card p-5"><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Selected node</p><div className="mt-5 flex items-center gap-3"><span className="grid size-9 place-items-center rounded-lg bg-violet-500/10 text-violet-600"><Brain className="size-4" /></span><div><p className="text-sm font-medium">Product principles</p><p className="text-[11px] text-muted-foreground">Reflection · Oct 21</p></div></div><p className="mt-5 text-xs leading-6 text-muted-foreground">Graph data will appear here when the knowledge graph endpoint is available.</p><div className="mt-6 border-t border-border pt-4 text-xs text-muted-foreground"><p className="mb-2 font-medium text-foreground">Related concepts</p><p>Design systems · Product strategy</p></div></div></div></div> }
function GraphMini() { return <GraphLines small /> }
function GraphLarge() { return <GraphLines /> }
function GraphLines({ small = false }: { small?: boolean }) { return <div className={cn('relative h-full w-full overflow-hidden bg-[radial-gradient(circle_at_center,hsl(var(--muted))_0,transparent_55%)]', small ? 'min-h-[178px]' : 'min-h-[520px]')}><svg className="absolute inset-0 h-full w-full" viewBox="0 0 800 500" aria-label="Knowledge graph preview"><g stroke="currentColor" strokeOpacity=".16" strokeWidth="1">{[[400,250,205,130],[400,250,580,145],[400,250,210,360],[400,250,590,350],[205,130,110,75],[205,130,120,210],[580,145,685,90],[580,145,690,230],[210,360,100,425],[210,360,330,430],[590,350,700,425],[590,350,480,430]].map(([x1,y1,x2,y2], i) => <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />)}</g><g fill="hsl(var(--card))" stroke="currentColor" strokeWidth="1.5">{[[400,250,22],[205,130,17],[580,145,17],[210,360,17],[590,350,17],[110,75,11],[120,210,11],[685,90,11],[690,230,11],[100,425,11],[330,430,11],[700,425,11],[480,430,11]].map(([cx,cy,r], i) => <circle key={i} cx={cx} cy={cy} r={r} className={i === 0 ? 'fill-violet-500/20 stroke-violet-500' : i % 2 ? 'fill-blue-500/10 stroke-blue-500/50' : 'fill-amber-500/10 stroke-amber-500/50'} />)}</g><g fill="currentColor" fontSize="11" opacity=".6">{!small && <><text x="425" y="245">Product principles</text><text x="222" y="125">Launch notes</text><text x="597" y="140">Design</text><text x="225" y="385">Strategy</text></>}</g></svg></div> }
function DocumentsView({ onAction }: { onAction: (s: string) => void }) { return <div><SectionHeading eyebrow="Sources" title="Documents" action={<Button size="sm" onClick={() => onAction('Upload document')}><UploadCloud className="size-4" />Upload document</Button>} /><div className="mb-5 rounded-xl border border-dashed border-border bg-card p-8 text-center"><UploadCloud className="mx-auto size-7 text-muted-foreground" /><p className="mt-3 text-sm font-medium">Drop a document here</p><p className="mt-1 text-xs text-muted-foreground">PDF, Markdown, text, JSON, or CSV — supported formats depend on the backend.</p><button onClick={() => onAction('Choose file')} className="mt-4 text-xs font-medium underline underline-offset-4">Choose a file</button></div><div className="rounded-xl border border-border bg-card"><div className="flex items-center justify-between border-b border-border p-4"><span className="text-sm font-medium">Recent sources</span><span className="text-xs text-muted-foreground">Backend status unavailable</span></div>{['Q4 research.md','Product brief.pdf','Meeting notes.txt'].map((name, i) => <div key={name} className="flex items-center gap-3 border-b border-border p-4 last:border-0"><FileText className="size-4 text-muted-foreground" /><span className="flex-1 text-sm">{name}</span><span className="rounded-full bg-muted px-2 py-1 text-[10px] text-muted-foreground">{i === 0 ? 'Ready to index' : 'Not connected'}</span><MoreHorizontal className="size-4 text-muted-foreground" /></div>)}</div></div> }
function AgentsView({ onAction }: { onAction: (s: string) => void }) { return <div><SectionHeading eyebrow="Bounded automation" title="Agents & approvals" action={<Button size="sm" onClick={() => onAction('Create agent task')}><Plus className="size-4" />New task</Button>} /><div className="grid gap-4 lg:grid-cols-2"><div className="rounded-xl border border-amber-200 bg-amber-50/50 p-5 dark:border-amber-900/50 dark:bg-amber-950/20"><div className="flex items-center gap-2 text-amber-700 dark:text-amber-300"><ShieldCheck className="size-4" /><span className="text-xs font-semibold uppercase tracking-[0.14em]">Awaiting approval</span></div><h3 className="mt-5 text-lg font-semibold">Prepare weekly focus blocks</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Review a proposed calendar update before any action is taken.</p><div className="mt-5 flex gap-2"><Button size="sm">Review request</Button><Button size="sm" variant="outline">Dismiss</Button></div></div><div className="rounded-xl border border-border bg-card p-5"><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Run history</p>{['Research synthesis', 'Inbox triage', 'Weekly reflection'].map((name, i) => <div key={name} className="mt-5 flex items-center gap-3"><span className={cn('grid size-7 place-items-center rounded-full', i === 0 ? 'bg-emerald-500/10 text-emerald-600' : 'bg-muted text-muted-foreground')}>{i === 0 ? <Check className="size-3.5" /> : <CircleDot className="size-3.5" />}</span><span className="flex-1 text-sm">{name}</span><span className="text-[10px] text-muted-foreground">{i === 0 ? 'Completed' : 'Unavailable'}</span></div>)}</div></div></div> }
function ActivityView() { return <div><SectionHeading eyebrow="System log" title="Activity" /><div className="rounded-xl border border-border bg-card">{['Memory retrieved for “launch sequence”', 'Product principles memory updated', 'Assistant session started', 'Q4 research.md added to sources'].map((item, i) => <div key={item} className="flex items-center gap-4 border-b border-border p-4 last:border-0"><span className="grid size-7 place-items-center rounded-full bg-muted"><Activity className="size-3.5 text-muted-foreground" /></span><span className="flex-1 text-sm">{item}</span><span className="text-[10px] text-muted-foreground">{i + 1}h ago</span></div>)}</div></div> }
function EmptyState({ title, detail }: { title: string; detail: string }) { return <div className="rounded-xl border border-dashed border-border p-12 text-center"><Search className="mx-auto size-6 text-muted-foreground" /><p className="mt-3 text-sm font-medium">{title}</p><p className="mt-1 text-xs text-muted-foreground">{detail}</p></div> }
