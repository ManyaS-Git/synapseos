/* ── Sidebar Navigation ────────────────────────────────────────────── */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain,
  LayoutDashboard,
  FolderKanban,
  MessageSquareText,
  GitBranch,
  Settings2,
  CircleDot,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { useAuthStore, useWorkspaceStore } from "@/store";
import { useLogout } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
  disabled?: boolean;
  children?: { label: string; href: string }[];
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Assistant Copilot",
    href: "/assistant",
    icon: MessageSquareText,
  },
  {
    label: "Memories",
    href: "/memory",
    icon: Brain,
    children: [
      { label: "All Memories", href: "/memory" },
      { label: "Create", href: "/memory/create" },
      { label: "Search", href: "/memory/search" },
      { label: "Graph", href: "/memory/graph" },
    ],
  },
  {
    label: "Knowledge Graph",
    href: "/memory/graph",
    icon: GitBranch,
  },
  {
    label: "Projects",
    href: "/projects",
    icon: FolderKanban,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings2,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const { currentWorkspace } = useWorkspaceStore();
  const logoutMutation = useLogout();

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  const workspaceName = currentWorkspace?.name || (user ? `${user.username}'s workspace` : "Workspace");
  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : user?.username?.slice(0, 2).toUpperCase() || "SO";

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-[248px] lg:border-r border-border bg-sidebar px-4 py-5 shrink-0 min-h-screen">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-2">
        <span className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm">
          <Brain className="size-4" />
        </span>
        <span className="font-semibold tracking-[-0.02em]">
          synapse<span className="text-muted-foreground">OS</span>
        </span>
      </div>

      {/* Workspace Selector */}
      <div className="mt-6 flex items-center gap-2 rounded-lg border border-sidebar-border bg-sidebar-accent/50 px-3 py-2.5 text-left">
        <div className="grid size-7 place-items-center rounded-md bg-foreground text-xs font-semibold text-background">
          {workspaceName.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-medium">{workspaceName}</p>
          <p className="truncate text-[10px] text-muted-foreground">
            {currentWorkspace?.description || "Personal knowledge base"}
          </p>
        </div>
        <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" />
      </div>

      {/* Navigation */}
      <nav className="mt-6 flex-1 space-y-1" aria-label="Primary navigation">
        <p className="mb-2 px-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
          Workspace
        </p>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const hasChildren = "children" in item && item.children;
          const Icon = item.icon;
          return (
            <div key={item.label}>
              <Link
                href={item.disabled ? "#" : item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                    : "text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                  item.disabled && "opacity-50 cursor-not-allowed"
                )}
                onClick={(e) => {
                  if (item.disabled) e.preventDefault();
                }}
              >
                <Icon className="size-4 shrink-0" />
                <span>{item.label}</span>
                {item.disabled && (
                  <span className="ml-auto text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                    Soon
                  </span>
                )}
              </Link>
              {hasChildren && isActive && (
                <div className="ml-7 mt-1 space-y-0.5 border-l border-sidebar-border pl-2">
                  {item.children?.map((child: { label: string; href: string }) => (
                    <Link
                      key={child.href}
                      href={child.href}
                      className={cn(
                        "block px-2.5 py-1 rounded-md text-xs transition-colors",
                        pathname === child.href
                          ? "bg-sidebar-accent text-sidebar-foreground font-medium"
                          : "text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
                      )}
                    >
                      {child.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Memory health & user section */}
      <div className="mt-auto space-y-2 pt-4">
        <div className="rounded-xl border border-sidebar-border bg-sidebar-accent/30 p-3">
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              Memory health
            </span>
            <CircleDot className="size-3 text-emerald-500" />
          </div>
          <div className="mb-2 flex items-end justify-between">
            <span className="text-base font-medium">92%</span>
            <span className="text-[10px] text-muted-foreground">Vectorized</span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-border">
            <div className="h-full w-[92%] rounded-full bg-emerald-500" />
          </div>
        </div>

        <div className="flex items-center gap-2 border-t border-sidebar-border px-2 pt-3">
          <div className="grid size-7 place-items-center rounded-full bg-gradient-to-br from-violet-400 to-blue-500 text-xs font-semibold text-white shadow-xs">
            {userInitials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-sidebar-foreground">
              {user?.full_name || user?.username || "Pilot"}
            </p>
            <p className="truncate text-[10px] text-muted-foreground">
              {user?.email || "Personal workspace"}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="p-1.5 text-muted-foreground hover:text-sidebar-foreground rounded-lg hover:bg-sidebar-accent transition-colors"
            title="Log out"
          >
            <LogOut className="size-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
