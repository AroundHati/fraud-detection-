import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(date));
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export function getRiskLevel(score: number): "low" | "medium" | "high" {
  if (score <= 30) return "low";
  if (score <= 70) return "medium";
  return "high";
}

export function getRiskColor(score: number): {
  bg: string;
  text: string;
  label: string;
} {
  if (score <= 30)
    return {
      bg: "bg-success-light",
      text: "text-success-foreground",
      label: "Low Risk",
    };
  if (score <= 70)
    return {
      bg: "bg-warning-light",
      text: "text-warning-foreground",
      label: "Medium Risk",
    };
  return {
    bg: "bg-error-light",
    text: "text-error-foreground",
    label: "High Risk",
  };
}

export function getStatusColor(status: string): {
  bg: string;
  text: string;
} {
  switch (status) {
    case "uploaded":
      return { bg: "bg-surface-secondary", text: "text-text-secondary" };
    case "processing":
      return { bg: "bg-info-light", text: "text-info-foreground" };
    case "investigating":
      return { bg: "bg-warning-light", text: "text-warning-foreground" };
    case "completed":
      return { bg: "bg-success-light", text: "text-success-foreground" };
    case "high_risk":
      return { bg: "bg-error-light", text: "text-error-foreground" };
    case "pending":
      return { bg: "bg-surface-secondary", text: "text-text-secondary" };
    case "running":
      return { bg: "bg-info-light", text: "text-info-foreground" };
    case "failed":
      return { bg: "bg-error-light", text: "text-error-foreground" };
    default:
      return { bg: "bg-surface-secondary", text: "text-text-secondary" };
  }
}
