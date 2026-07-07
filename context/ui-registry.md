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

---

# Component Categories

## Layout Components

### Homepage Landing UI

File: `app/page.tsx`
Last updated: July 3, 2026

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
The homepage follows the reference landing composition: token-backed top navigation, large left-aligned headline with primary accent text, primary and secondary CTAs, compact trust badges and a framed dashboard preview using `public/images/dashboard.png`. Marketing-style metrics use `bg-primary-light` icon markers with `text-primary` numbers.

---

## Dashboard Components

_Components will be added here during development._

---

## Claim Components

_Components will be added here during development._

---

## Investigation Components

_Components will be added here during development._

---

## Report Components

_Components will be added here during development._

---

## Analytics Components

_Components will be added here during development._

---

# Shared UI Patterns

- Landing navigation: `bg-surface`, `border-b border-border`, `h-16`, `max-w-[1440px]`, `px-6`.
- Primary CTA: `bg-primary text-primary-foreground rounded-md px-8 py-4 font-semibold hover:bg-primary-dark`.
- Secondary CTA: `bg-surface border border-border text-primary rounded-md px-8 py-4 hover:bg-surface-secondary`.
- Dashboard preview frame: `bg-surface border border-border rounded-xl p-2 shadow-lg`.
- Metric strip: `bg-surface border-t border-border`, compact marker in `bg-primary-light text-primary`, value in `text-primary`.

---

# Design Notes

Record reusable design decisions made during implementation.

- Marketing landing pages should use the product background token with surface-backed sections.
- Hero dashboard previews should use real product imagery from `public/` when available.
- CTA and metric patterns should stay on the primary token scale.
