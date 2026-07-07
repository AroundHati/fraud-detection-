# UI Tokens

Design tokens for the Healthcare Fraud Detection Platform.

These tokens define the visual language of the application. Every component must use these shared tokens rather than hardcoded values.

---

# How to Use

This project uses **Tailwind CSS v4**.

All design tokens are defined using the `@theme` directive inside `app/globals.css`.

Never hardcode colors.

Never use Tailwind default color utilities.

Example

```tsx
// Correct

className="bg-surface text-text-primary border-border"

className="bg-primary text-primary-foreground"

className="bg-success-light text-success"

// Incorrect

className="bg-blue-500"

className="text-gray-700"

className="bg-[#2563EB]"
```

---

# globals.css Theme

```css
@import "tailwindcss";

@theme {

  /* Typography */

  --font-sans: "Inter", sans-serif;

  /* Backgrounds */

  --color-background: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-surface-secondary: #F1F5F9;
  --color-surface-muted: #E2E8F0;

  /* Borders */

  --color-border: #E2E8F0;
  --color-border-light: #CBD5E1;

  /* Text */

  --color-text-primary: #0F172A;
  --color-text-secondary: #475569;
  --color-text-muted: #94A3B8;

  /* Primary */

  --color-primary: #2563EB;
  --color-primary-dark: #1D4ED8;
  --color-primary-light: #DBEAFE;
  --color-primary-foreground: #FFFFFF;

  /* Success */

  --color-success: #10B981;
  --color-success-light: #D1FAE5;
  --color-success-foreground: #065F46;

  /* Warning */

  --color-warning: #F59E0B;
  --color-warning-light: #FEF3C7;
  --color-warning-foreground: #92400E;

  /* Error */

  --color-error: #EF4444;
  --color-error-light: #FEE2E2;
  --color-error-foreground: #991B1B;

  /* Information */

  --color-info: #3B82F6;
  --color-info-light: #DBEAFE;
  --color-info-foreground: #1D4ED8;

  /* Radius */

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
}
```

---

# Color Usage Guide

## Page Layout

| Element | Token |
|----------|-------|
| Application Background | `bg-background` |
| Cards | `bg-surface` |
| Secondary Surface | `bg-surface-secondary` |
| Borders | `border-border` |

---

## Typography

| Element | Token |
|----------|-------|
| Primary Text | `text-text-primary` |
| Secondary Text | `text-text-secondary` |
| Placeholder | `text-text-muted` |

---

## Primary

Used for

- Primary Buttons
- Active Navigation
- Selected Tabs
- Links

| Element | Token |
|----------|-------|
| Background | `bg-primary` |
| Text | `text-primary-foreground` |
| Hover | `bg-primary-dark` |

---

## Success

Used for

- Completed Investigations
- Safe Claims
- Success Messages

| Element | Token |
|----------|-------|
| Background | `bg-success-light` |
| Text | `text-success-foreground` |

---

## Warning

Used for

- Medium Risk Claims
- Pending Reviews

| Element | Token |
|----------|-------|
| Background | `bg-warning-light` |
| Text | `text-warning-foreground` |

---

## Error

Used for

- High Risk Claims
- Failed Investigations
- Critical Alerts

| Element | Token |
|----------|-------|
| Background | `bg-error-light` |
| Text | `text-error-foreground` |

---

# Fraud Risk Colors

| Score | Background | Text |
|--------|------------|------|
| 0–30 | `bg-success-light` | `text-success-foreground` |
| 31–70 | `bg-warning-light` | `text-warning-foreground` |
| 71–100 | `bg-error-light` | `text-error-foreground` |

---

# Investigation Status

| Status | Background | Text |
|----------|------------|------|
| Uploaded | `bg-surface-secondary` | `text-text-secondary` |
| OCR Processing | `bg-info-light` | `text-info-foreground` |
| Investigating | `bg-warning-light` | `text-warning-foreground` |
| Completed | `bg-success-light` | `text-success-foreground` |
| High Risk | `bg-error-light` | `text-error-foreground` |

---

# Typography

| Element | Size | Weight |
|----------|------|--------|
| Page Title | 32px | 700 |
| Section Title | 20px | 600 |
| Card Title | 18px | 600 |
| Body Text | 14px | 400 |
| Labels | 12px | 500 |
| KPI Numbers | 32px | 700 |

Font

```
Inter
```

---

# Spacing

| Token | Value |
|--------|-------|
| gap-2 | 8px |
| gap-4 | 16px |
| gap-6 | 24px |
| gap-8 | 32px |
| p-4 | 16px |
| p-6 | 24px |
| p-8 | 32px |

---

# Component Tokens

## Cards

```
Background

bg-surface

Border

border-border

Radius

rounded-xl

Padding

p-6

Shadow

shadow-sm
```

---

## Buttons

### Primary

```
bg-primary

text-primary-foreground

rounded-md

px-4 py-2
```

### Secondary

```
bg-surface

border

border-border

text-text-primary
```

---

## Inputs

```
bg-surface

border

border-border

rounded-md

px-3 py-2

text-text-primary

placeholder:text-text-muted
```

---

## Tables

```
Header

bg-surface-secondary

Body

bg-surface

Hover

bg-background
```

---

## Status Badge

```
rounded-full

px-2 py-1

text-xs

font-medium
```

---

## Risk Score Indicator

Track

```
bg-border
```

Fill

Low Risk

```
bg-success
```

Medium Risk

```
bg-warning
```

High Risk

```
bg-error
```

Height

```
6px
```

Radius

```
rounded-full
```

---

## Timeline

Completed

```
bg-success
```

Running

```
bg-primary
```

Pending

```
bg-surface-muted
```

Failed

```
bg-error
```

---

## Dashboard Charts

| Chart | Color |
|--------|-------|
| Claims Uploaded | `bg-primary` |
| Fraud Distribution | `bg-error` |
| Investigation Status | `bg-warning` |
| Reports Generated | `bg-success` |
| Timeline | `bg-info` |

---

## Sidebar

```
Background

bg-surface

Width

280px

Border

border-border
```

---

## Navbar

```
Background

bg-surface

Height

64px

Border Bottom

border-border
```

---

# Icons

Use **Lucide React** only.

Sizes

```
16px

20px

24px
```

---

# Shadows

| Token | Value |
|--------|-------|
| shadow-sm | Cards |
| shadow-md | Modals |
| shadow-lg | Dropdowns |

---

# Animations

Allowed

- Fade In
- Slide Up
- Progress Bar Fill

Avoid excessive animations.

---

# Invariants

- Never hardcode colors.
- Never use Tailwind default colors.
- Never use inline styles.
- Always use Inter.
- Always use design tokens.
- Risk indicators always use the predefined Risk Color Scale.
- Status badges always use the predefined Status Colors.
- Every page must use the same spacing system.
- Every card must use the shared Card Token.
- All dashboard charts must follow the Dashboard Chart Color Palette.