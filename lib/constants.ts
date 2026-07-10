export const FRAUD_RISK_THRESHOLD = 0.7;

export const APP_NAME = "FraudShield";
export const APP_DESCRIPTION =
  "AI-powered healthcare fraud detection and investigation platform.";

export const PROTECTED_ROUTES = [
  "/dashboard",
  "/upload",
  "/analyze",
  "/claims",
  "/investigations",
  "/reports",
  "/analytics",
  "/settings",
] as const;

export const PUBLIC_ROUTES = ["/", "/login", "/signup"] as const;

export const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Upload Claim", href: "/upload" },
  { label: "Analyze Claims", href: "/analyze" },
  { label: "Claims", href: "/claims" },
  { label: "Investigations", href: "/investigations" },
  { label: "Analytics", href: "/analytics" },
  { label: "Reports", href: "/reports" },
  { label: "Alerts", href: "/dashboard" },
  { label: "Settings", href: "/settings" },
] as const;
