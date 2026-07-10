"use client";

import { useAuth } from "./use-auth";
import { getInitials } from "@/lib/utils";

export function useUser() {
  const { user, loading } = useAuth();

  const initials = user
    ? getInitials(
        (user.profile?.name as string) || (user.email as string) || "U",
      )
    : "U";

  const displayName =
    (user?.profile?.name as string) || user?.email?.split("@")[0] || "User";

  return {
    user,
    loading,
    initials,
    displayName,
  };
}
