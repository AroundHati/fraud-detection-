"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Bell, User, Settings, LogOut, Menu } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useUser } from "@/hooks/use-user";

type TopNavbarProps = {
  onToggleSidebar?: () => void;
};

export function TopNavbar({ onToggleSidebar }: TopNavbarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const { signOut } = useAuth();
  const { initials, displayName } = useUser();
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="rounded-md p-2 text-text-secondary hover:bg-surface-secondary hover:text-text-primary md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      <div className="flex items-center gap-3">
        <button className="relative rounded-md p-2 text-text-secondary transition-colors hover:bg-surface-secondary hover:text-text-primary">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-error" />
        </button>

        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary-dark"
          >
            {initials}
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-lg border border-border bg-surface p-1.5 shadow-lg">
              <div className="border-b border-border px-3 py-2.5 mb-1">
                <p className="text-sm font-medium text-text-primary">
                  {displayName}
                </p>
              </div>
              <Link
                href="/settings"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-secondary hover:text-text-primary"
              >
                <User className="h-4 w-4" />
                Profile
              </Link>
              <Link
                href="/settings"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-secondary hover:text-text-primary"
              >
                <Settings className="h-4 w-4" />
                Settings
              </Link>
              <div className="my-1 border-t border-border" />
              <button
                onClick={() => {
                  setDropdownOpen(false);
                  signOut();
                }}
                className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-error transition-colors hover:bg-error-light"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
