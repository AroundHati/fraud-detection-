"use client";

import { AuthProvider } from "@/hooks/use-auth";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <DashboardLayout>{children}</DashboardLayout>
    </AuthProvider>
  );
}
