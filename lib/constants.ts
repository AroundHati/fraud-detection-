export const FRAUD_RISK_THRESHOLD = 0.7;

export const APP_NAME = "FraudShield";
export const APP_DESCRIPTION =
  "AI-powered healthcare fraud detection and investigation platform.";

export const PROTECTED_ROUTES = [
  "/dashboard",
  "/upload",
  "/investigations",
  "/reports",
] as const;

export const PUBLIC_ROUTES = ["/", "/login", "/signup"] as const;

export const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Upload Claims", href: "/upload" },
  { label: "Investigations", href: "/investigations" },
  { label: "Reports", href: "/reports" },
] as const;
