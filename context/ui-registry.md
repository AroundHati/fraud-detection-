# UI Registry

Living document.

This file serves as the single source of truth for all reusable UI components in the Healthcare Fraud Detection Platform.

Update this file immediately after creating or modifying a reusable component.

---

# How to Use

Before building any new component:

1. Check if an equivalent component already exists.
2. Reuse existing components whenever possible.
3. Match existing spacing, typography and color tokens.
4. Follow the standards defined in `ui-rules.md`.
5. If a new reusable component is created, register it here immediately.

Never create duplicate components with similar functionality.

---

# Component Registry

| Component | Location | Purpose | Used In | Status |
|-----------|----------|---------|---------|--------|
| Homepage Landing UI | `app/page.tsx` | Public landing page with hero, navigation, dashboard preview and metric strip | `/` | Active |
| Auth Login Form | `app/(auth)/login/page.tsx` | Email/password login form with InsForge integration | `/login` | Active |
| Auth Signup Form | `app/(auth)/signup/page.tsx` | Registration form with full name, email, password | `/signup` | Active |
| Dashboard Layout | `components/layout/DashboardLayout.tsx` | Sidebar + top navbar + avatar dropdown layout wrapper | All `/dashboard/*` routes | Active |
| Sidebar | `components/layout/Sidebar.tsx` | Standalone sidebar component (unused, DashboardLayout has inline sidebar) | — | Deprecated |
| Top Navbar | `components/layout/TopNavbar.tsx` | Standalone top navbar (unused, DashboardLayout has inline navbar) | — | Deprecated |
| Dashboard Page | `app/(dashboard)/dashboard/page.tsx` | Stats cards, recent claims table, activity feed, risk distribution charts | `/dashboard` | Active |
| Upload Page | `app/(dashboard)/upload/page.tsx` | Drag-and-drop file upload with progress indicators | `/upload` | Active |
| Analyze Page | `app/(dashboard)/analyze/page.tsx` | AI analysis workflow with step-by-step progress and results display | `/analyze` | Active |
| Claims Page | `app/(dashboard)/claims/page.tsx` | Claims table with search, status/risk filters, sortable columns | `/claims` | Active |
| Investigations Page | `app/(dashboard)/investigations/page.tsx` | Investigation list, agent timeline, evidence summary | `/investigations` | Active |
| Reports Page | `app/(dashboard)/reports/page.tsx` | Report list with PDF/CSV export toggle | `/reports` | Active |
| Analytics Page | `app/(dashboard)/analytics/page.tsx` | KPI cards, bar chart, risk distribution, provider risk, diagnosis codes | `/analytics` | Active |
| Settings Page | `app/(dashboard)/settings/page.tsx` | Profile form, password change, sidebar navigation | `/settings` | Active |
| Provider Investigation Page | `app/(dashboard)/investigations/[providerId]/page.tsx` | Detailed provider investigation with summary, fraud indicators, recommendations | `/investigations/[providerId]` | Active |
| Investigation Header | `components/investigation/InvestigationHeader.tsx` | Provider ID, risk badge, prediction, confidence display | Investigation Details | Active |
| Investigation Summary Card | `components/investigation/InvestigationSummaryCard.tsx` | Claims, reimbursement, beneficiary stats grid | Investigation Details | Active |
| Fraud Indicators Card | `components/investigation/FraudIndicatorsCard.tsx` | Explainable fraud reasons with severity badges | Investigation Details | Active |
| Recommendation Card | `components/investigation/RecommendationCard.tsx` | Risk-based recommendation with action level | Investigation Details | Active |

---

# Component Categories

## Layout Components

### Homepage Landing UI

File: `app/page.tsx`
Last updated: July 10, 2026

| Property | Class |
| --- | --- |
| Background | `bg-background`, `bg-surface` |
| Border | `border border-border`, `border-b border-border`, `border-t border-border` |
| Border radius | `rounded-md`, `rounded-xl` |
| Text - primary | `text-text-primary`, `font-bold` |
| Text - secondary | `text-text-secondary`, `font-medium` |
| Spacing | `px-6`, `py-16`, `gap-10`, `p-2`, `py-8` |
| Hover state | `hover:text-primary`, `hover:bg-primary-dark`, `hover:bg-surface-secondary` |
| Shadow | `shadow-sm`, `shadow-md`, `shadow-lg` |
| Accent usage | `bg-primary`, `text-primary`, `bg-primary-light`, `text-primary-foreground` |

**Pattern notes:**
The homepage follows the reference landing composition: token-backed top navigation, large left-aligned headline with primary accent text, primary CTA ("Start Investigating") with conditional auth routing, and a framed dashboard preview using `public/images/dashboard.png`. Marketing-style metrics use `bg-primary-light` icon markers with `text-primary` numbers. Navigation links and "Book Demo" button have been removed. Only logo, "Log In" and "Get Started" buttons remain in the navbar.

---

### Dashboard Layout

File: `components/layout/DashboardLayout.tsx`
Last updated: July 10, 2026

| Property | Class |
| --- | --- |
| Sidebar background | `bg-surface` |
| Sidebar width | `w-[260px]` |
| Sidebar border | `border-r border-border` |
| Active nav item | `bg-primary-light text-primary` |
| Inactive nav item | `text-text-secondary hover:bg-surface-secondary hover:text-text-primary` |
| Top navbar height | `h-16` |
| Top navbar border | `border-b border-border` |
| Avatar | `h-9 w-9 rounded-full bg-primary text-primary-foreground text-sm font-semibold` |
| Dropdown | `w-56 rounded-lg border border-border bg-surface p-1.5 shadow-lg` |
| Mobile menu toggle | `md:hidden` responsive breakpoint |

**Pattern notes:**
The dashboard layout wraps all authenticated pages. It includes a left sidebar with navigation links (each with a Lucide icon), a top navbar with notification bell (with red dot indicator) and user avatar dropdown (Profile, Settings, Logout). Mobile responsive with slide-out sidebar overlay.

---

### Auth Login/Signup Pages

Files: `app/(auth)/login/page.tsx`, `app/(auth)/signup/page.tsx`
Last updated: July 10, 2026

| Property | Class |
| --- | --- |
| Layout | `flex min-h-screen` — split 50/50 on `lg:` |
| Left panel | `bg-surface`, feature highlights with `bg-success-light` icons |
| Right panel | Centered form, `max-w-md` |
| Input | `h-11 rounded-md border border-border bg-surface px-3 text-sm` |
| Primary button | `h-11 rounded-md bg-primary text-primary-foreground font-semibold hover:bg-primary-dark` |
| Error message | `rounded-md bg-error-light p-3 text-sm font-medium text-error-foreground` |
| Logo link | `flex items-center gap-2` |

**Pattern notes:**
Auth pages use a two-column split layout. The left column shows FraudShield branding and feature highlights. The right column contains the form. Mobile shows only the form with a compact logo link at the top. Login page wraps useSearchParams() in a Suspense boundary for Next.js 16 compatibility.

---

## Dashboard Components

### Dashboard Stats Cards

File: `app/(dashboard)/dashboard/page.tsx`

| Property | Class |
| --- | --- |
| Card | `rounded-xl border border-border bg-surface p-6 shadow-sm` |
| Icon container | `flex h-10 w-10 items-center justify-center rounded-lg` |
| Value | `text-2xl font-bold text-text-primary` |
| Label | `text-sm font-medium text-text-secondary` |
| Trend indicator | `text-xs font-semibold text-success` / `text-error` |

---

### Claims Table

File: `app/(dashboard)/claims/page.tsx`

| Property | Class |
| --- | --- |
| Table header | `bg-surface-secondary text-text-muted uppercase tracking-wider text-xs font-medium` |
| Row hover | `hover:bg-background` |
| Status badge | `rounded-full px-2.5 py-0.5 text-xs font-medium` |
| Search input | `h-10 rounded-md border border-border bg-surface pl-9 pr-4 text-sm` |

---

### Investigation Timeline

File: `app/(dashboard)/investigations/page.tsx`

| Property | Class |
| --- | --- |
| Completed step | `bg-success text-primary-foreground rounded-full` |
| Running step | `bg-primary text-primary-foreground rounded-full` |
| Pending step | `bg-surface-secondary text-text-muted rounded-full` |
| Step size | `h-8 w-8 text-xs font-bold` |

---

### Investigation Header

File: `components/investigation/InvestigationHeader.tsx`
Last updated: July 11, 2026

| Property | Class |
| --- | --- |
| Back link | `text-sm font-medium text-text-secondary hover:text-primary` |
| Card | `rounded-xl border border-border bg-surface p-6 shadow-sm` |
| Risk badge | `rounded-full px-2.5 py-0.5 text-xs font-medium` with `getRiskColor()` tokens |
| Stat icons | `flex h-8 w-8 items-center justify-center rounded-lg` with token bg |

**Pattern notes:**
Renders back navigation, provider ID + name, risk level badge, and a 3-column stat row (prediction, confidence, risk score) with colored icon containers.

---

### Investigation Summary Card

File: `components/investigation/InvestigationSummaryCard.tsx`
Last updated: July 11, 2026

| Property | Class |
| --- | --- |
| Card | `rounded-xl border border-border bg-surface p-6 shadow-sm` |
| Stat item | `flex items-center gap-3 rounded-lg border border-border p-3` |
| Icon container | `flex h-9 w-9 shrink-0 items-center justify-center rounded-lg` with token bg |
| Value | `truncate text-sm font-semibold text-text-primary` |
| Label | `text-xs font-medium text-text-muted` |

**Pattern notes:**
Responsive grid of claim statistics. Uses `formatCurrency()` from utils for monetary values. Grid is `sm:grid-cols-2 lg:grid-cols-3`.

---

### Fraud Indicators Card

File: `components/investigation/FraudIndicatorsCard.tsx`
Last updated: July 11, 2026

| Property | Class |
| --- | --- |
| Card | `rounded-xl border border-border bg-surface p-6 shadow-sm` |
| Indicator row | `flex items-start gap-3 rounded-lg border border-border p-3.5` |
| Status icon | `flex h-7 w-7 shrink-0 items-center justify-center rounded-lg` with status bg |
| Severity badge | `inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold` |
| Label | `text-sm font-medium text-text-primary` |
| Description | `text-sm text-text-secondary` |

**Pattern notes:**
Each indicator shows a status icon (flagged=red, warning=orange, info=blue), a label with severity badge, and a description. Severity badges use token-backed colors: critical/high=`bg-error-light`, medium=`bg-warning-light`, low=`bg-surface-secondary`.

---

### Recommendation Card

File: `components/investigation/RecommendationCard.tsx`
Last updated: July 11, 2026

| Property | Class |
| --- | --- |
| Card | `rounded-xl border border-border bg-surface p-6 shadow-sm` |
| Banner | `rounded-lg border p-4` with level-specific border |
| Icon container | `flex h-10 w-10 shrink-0 items-center justify-center rounded-lg` |
| Level colors | immediate=`bg-error-light/border-error/20`, manual=`bg-warning-light/border-warning/20`, routine=`bg-success-light/border-success/20` |

**Pattern notes:**
Single recommendation banner that adapts color and icon based on risk level. Uses `RecommendationLevel` type to select configuration. Includes arrow icon indicating actionability.

---

## Shared UI Patterns

- Landing navigation: `bg-surface`, `border-b border-border`, `h-16`, `max-w-[1440px]`, `px-6`.
- Primary CTA: `bg-primary text-primary-foreground rounded-md px-8 py-4 font-semibold hover:bg-primary-dark`.
- Secondary CTA: `bg-surface border border-border text-primary rounded-md px-8 py-4 hover:bg-surface-secondary`.
- Dashboard preview frame: `bg-surface border border-border rounded-xl p-2 shadow-lg`.
- Metric strip: `bg-surface border-t border-border`, compact marker in `bg-primary-light text-primary`, value in `text-primary`.
- Dashboard card: `rounded-xl border border-border bg-surface p-6 shadow-sm`.
- Status badge: `rounded-full px-2.5 py-0.5 text-xs font-medium`.
- Sidebar nav item: `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors`.
- Avatar dropdown item: `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-surface-secondary`.
- Investigation detail card: `rounded-xl border border-border bg-surface p-6 shadow-sm` with section header `text-base font-semibold text-text-primary`.
- Fraud indicator row: `flex items-start gap-3 rounded-lg border border-border p-3.5` with status icon container `flex h-7 w-7 shrink-0 items-center justify-center rounded-lg`.
- Severity badge: `inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold` with token-backed severity colors.
- Recommendation banner: `rounded-lg border p-4` with level-specific border color and icon container.

---

# Design Notes

Record reusable design decisions made during implementation.

- Marketing landing pages should use the product background token with surface-backed sections.
- Hero dashboard previews should use real product imagery from `public/` when available.
- CTA and metric patterns should stay on the primary token scale.
- Dashboard pages follow a consistent card pattern: `rounded-xl border border-border bg-surface p-6 shadow-sm`.
- All form inputs use consistent height (`h-11`), border radius (`rounded-md`), and token-backed styling.
- Auth pages use a split layout that collapses to single column on mobile.
- The dashboard layout is a full-height flex container with sidebar, top navbar, and scrollable main content area.
