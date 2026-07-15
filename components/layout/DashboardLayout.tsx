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
        <div className="flex h-[60px] shrink-0 items-center border-b border-border px-5">
          <Link
            href="/dashboard"
            className="flex items-center gap-3"
            onClick={() => setSidebarOpen(false)}
          >
            <svg
              viewBox="0 0 28 32"
              fill="none"
              className="h-7 w-7 shrink-0"
              aria-hidden="true"
            >
              <path
                d="M14 1L3 5.5V14C3 20.63 7.69 26.84 14 28.5C20.31 26.84 25 20.63 25 14V5.5L14 1Z"
                fill="#2563EB"
              />
              <path
                d="M14 9.5V21.5M8.5 14H19.5"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            <div className="flex flex-col">
              <span className="text-[15px] font-bold leading-tight text-text-primary">
                FraudShield
              </span>
              <span className="text-[10px] font-medium leading-tight text-text-muted">
                AI-Powered Fraud Detection
              </span>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto rounded p-1 text-text-muted hover:text-text-primary md:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
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
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                      isActive
                        ? "bg-primary-light text-primary"
                        : "text-text-secondary hover:bg-surface-secondary hover:text-text-primary",
                    )}
                  >
                    <item.icon className="h-[18px] w-[18px] shrink-0" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Sidebar footer — version */}
        <div className="shrink-0 border-t border-border px-5 py-3">
          <p className="text-[11px] font-medium text-text-muted">
            FraudShield v1.0
          </p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-[60px] shrink-0 items-center justify-between border-b border-border bg-surface px-6">
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
                className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary transition-colors hover:bg-primary/20"
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
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  );
}
