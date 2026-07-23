/**
 * Dashboard layout with sidebar and header.
 *
 * TODO: Implement:
 * - Sidebar navigation
 * - Header with user info
 * - Main content area
 * - Mobile responsive
 */

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* TODO: Sidebar */}
      <aside className="hidden w-64 border-r bg-muted/10 lg:block">
        <div className="p-4">
          <h2 className="text-lg font-semibold">SynapseOS</h2>
        </div>
        {/* TODO: Navigation items */}
      </aside>
      <div className="flex-1 overflow-auto">
        {/* TODO: Header */}
        <header className="border-b p-4">
          <h1 className="text-xl font-semibold">Dashboard</h1>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
