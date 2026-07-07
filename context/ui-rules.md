# UI Rules

Design standards for the Healthcare Fraud Detection Platform.

The application is designed as an enterprise investigation dashboard. Every interface should prioritize readability, consistency and efficient data analysis.

---

# Font

Always import **Inter** using `next/font/google`.

```typescript
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});
```

Use the `--font-sans` variable throughout the application.

Never use system fonts.

---

# Layout

- Maximum page width: **1440px**
- Center all page content
- Page padding: **32px**
- Gap between sections: **24px**
- Navbar height: **64px**
- Dashboard uses:
  - Top Navbar
  - Left Sidebar
- Investigation pages use the same layout throughout the application.

---

# Navigation

## Navbar

Contains

- Dashboard
- Claims
- Investigations
- Reports
- Analytics
- Profile

---

## Sidebar

Contains

- Dashboard
- Upload Claim
- Claims
- Investigations
- Reports
- Analytics
- Settings

The active navigation item uses the primary accent color.

---

# Cards

Every major section is displayed inside a card.

```
Background: White
Border Radius: 16px
Padding: 24px
Border: 1px solid
Light shadow
```

Never place content directly on the page background.

---

# Typography

## Page Heading

```
32px
Weight 700
```

---

## Section Heading

```
18px
Weight 600
```

---

## Body Text

```
14px
Weight 400
```

---

## Labels

```
12px
Weight 500
```

---

## KPI Numbers

```
32px
Weight 700
```

---

# Buttons

## Primary

- Filled
- Rounded
- Used for primary actions

Examples

- Upload Claim
- Start Investigation
- Generate Report

---

## Secondary

Outlined button

Used for

- Cancel
- View Details
- Download

---

# Forms

All forms follow the same spacing.

Input height

```
44px
```

Border Radius

```
8px
```

Validation errors appear below the input.

---

# Tables

Used for

- Claims
- Investigations
- Reports

Rules

- Sticky header
- Row hover
- No alternating colors
- Pagination
- Search
- Sorting
- Filtering

---

# Status Badges

Standard badge colors

| Status | Meaning |
|---------|----------|
| Gray | Uploaded |
| Blue | Processing |
| Orange | Investigating |
| Green | Completed |
| Red | High Risk |

Never invent new badge colors.

---

# Risk Score

Every fraud score uses the same color scale.

| Score | Color |
|--------|--------|
| 0–30 | Green |
| 31–70 | Orange |
| 71–100 | Red |

Risk scores always display

- Percentage
- Color
- Label

Example

```
87%

High Risk
```

---

# Investigation Timeline

Every investigation page contains the same timeline.

```
Claim Uploaded

↓

OCR Completed

↓

Investigation Agent

↓

Knowledge Agent

↓

Fraud Intelligence Agent

↓

Report Generated
```

Completed steps

Green

Running

Blue

Failed

Red

Pending

Gray

---

# Empty States

Every page must have an empty state.

Include

- Icon
- Short description
- Primary action

Example

"No investigations found."

↓

Upload Claim

---

# Charts

Dashboard charts

- Bar Chart
- Line Chart
- Pie Chart

Rules

- Clear legends
- Consistent colors
- No unnecessary animations

---

# Icons

Use **Lucide React** only.

Icons should always precede labels where appropriate.

---

# Responsive Design

Support

- Desktop
- Tablet

Mobile support is optional for this project.

---

# Accessibility

- Keyboard navigation
- Visible focus states
- Sufficient color contrast
- Form labels for every input

---

# Tailwind CSS

Use Tailwind CSS v4.

Design tokens belong inside

```
globals.css
```

Never use hardcoded color values throughout the application.

---

# Do Nots

- Never hardcode colors.
- Never use inline styles.
- Never duplicate UI components.
- Never use multiple card styles.
- Never display raw error messages.
- Never overload pages with unnecessary animations.
- Never use more than one primary action button per section.