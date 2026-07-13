"use client";

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  Upload,
  Search,
  FileText,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useUser } from "@/hooks/use-user";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Upload Claims", href: "/upload", icon: Upload },
  { label: "Investigations", href: "/investigations", icon: Search },
  { label: "Reports", href: "/reports", icon: FileText },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { signOut } = useAuth();
  const { initials, displayName } = useUser();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[240px] flex-col border-r border-border bg-surface transition-transform duration-200 md:static md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Logo */}
        <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-border px-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5"
            onClick={() => setSidebarOpen(false)}
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary text-[11px] font-bold text-primary-foreground">
              FS
            </span>
            <span className="text-sm font-bold text-text-primary">
              FraudShield
            </span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto rounded p-1 text-text-muted hover:text-text-primary md:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-3">
          <ul className="space-y-0.5">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" &&
                  pathname.startsWith(item.href));

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary-light text-primary"
                        : "text-text-secondary hover:bg-surface-secondary hover:text-text-primary",
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Sidebar footer — version */}
        <div className="shrink-0 border-t border-border px-4 py-3">
          <p className="text-[11px] text-text-muted">FraudShield v1.0</p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-surface px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded p-1.5 text-text-secondary hover:bg-surface-secondary hover:text-text-primary md:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-3 md:ml-auto">
            {/* User dropdown */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary-dark"
              >
                {initials}
              </button>

              {dropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setDropdownOpen(false)}
                  />
                  <div className="absolute right-0 top-full z-50 mt-2 w-52 overflow-hidden rounded-lg border border-border bg-surface shadow-lg">
                    <div className="border-b border-border px-3 py-2.5">
                      <p className="text-sm font-medium text-text-primary truncate">
                        {displayName}
                      </p>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          signOut();
                        }}
                        className="flex w-full items-center gap-2.5 px-3 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-secondary hover:text-text-primary"
                      >
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
