"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Brain,
  FileText,
  Search,
  BarChart3,
  FileIcon,
  Bell,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const sidebarItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Upload Claim", href: "/upload", icon: Upload },
  { label: "Analyze Claims", href: "/analyze", icon: Brain },
  { label: "Claims", href: "/claims", icon: FileText },
  { label: "Investigations", href: "/investigations", icon: Search },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Reports", href: "/reports", icon: FileIcon },
  { label: "Alerts", href: "/dashboard", icon: Bell },
  { label: "Settings", href: "/settings", icon: Settings },
];

type SidebarProps = {
  collapsed?: boolean;
};

export function Sidebar({ collapsed = false }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "hidden h-full border-r border-border bg-surface md:flex md:flex-col",
        collapsed ? "w-[72px]" : "w-[260px]",
      )}
    >
      <div className="flex h-16 items-center gap-3 border-b border-border px-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-xs font-bold text-primary-foreground">
          FS
        </span>
        {!collapsed && (
          <span className="text-base font-bold text-text-primary">
            FraudShield
          </span>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {sidebarItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));

            return (
              <li key={item.label}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary-light text-primary"
                      : "text-text-secondary hover:bg-surface-secondary hover:text-text-primary",
                  )}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
