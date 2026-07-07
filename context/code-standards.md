# Code Standards

Implementation rules and conventions for the Healthcare Fraud Detection Platform. These standards ensure consistency, maintainability and predictable development throughout the project.

---

## Engineering Mindset

The AI assistant working on this project operates as a senior software engineer.

This means:

* **Understand before implementing** — always understand the problem, architecture and feature requirements before writing code.
* **Read project documentation first** — verify implementation against `architecture.md`, `build-plan.md` and `project-overview.md`.
* **Respect feature boundaries** — only implement the current feature. Avoid adding functionality outside the defined scope.
* **Every feature must be testable** — every implementation should have a clear method of verification before moving to the next task.
* **Prefer readability over complexity** — write code that is easy to understand, maintain and extend.
* **Complete one milestone before starting another** — avoid partially implemented features.
* **Design for failure** — anticipate failures, handle errors gracefully and ensure the system remains stable.

---

## TypeScript

* Strict Mode must remain enabled.
* Never use `any`.
* Prefer `unknown` when the type is uncertain.
* Explicitly define parameter and return types for exported functions.
* Prefer `type` for object definitions and unions.
* Use `interface` only for extendable component props.
* Prefer `const` over `let`.
* Handle every asynchronous operation using proper error handling.

---

## Next.js Conventions

* Use the App Router exclusively.
* Server Components are the default.
* Add `"use client"` only when required.
* Perform data fetching inside Server Components whenever possible.
* API routes belong in `app/api/`.
* Server Actions belong in the `actions/` directory.
* Keep business logic outside React components.
* Keep API routes lightweight by delegating processing to services or AI agents.
* Follow the latest Next.js documentation when framework behaviour changes.

---

## LangGraph Conventions

* Every investigation must begin through the LangGraph Orchestrator.
* AI agents communicate only through the shared workflow state.
* Individual agents must remain focused on a single responsibility.
* Agent outputs should be structured and deterministic whenever possible.
* Agent failures should be logged without terminating the complete investigation.
* Shared investigation state must be updated after every agent execution.

---

## AI Development Standards

* Keep prompts modular and reusable.
* Never hardcode claim-specific values inside prompts.
* Every AI-generated fraud assessment must include supporting reasoning.
* Every fraud prediction must include a confidence score.
* AI reasoning should complement machine learning predictions, not replace them.
* Keep prompts version-controlled and easy to maintain.

---

## Machine Learning Standards

* Perform all preprocessing before model inference.
* Never modify the trained XGBoost model during runtime.
* Validate all required features before prediction.
* Handle missing or invalid values before inference.
* Treat the model prediction as evidence rather than the final decision.

---

## OCR Standards

* Process uploaded documents before investigation begins.
* Preserve original uploaded files.
* Store extracted text separately from the original document.
* Allow manual correction of OCR results before AI investigation.

---

## Database Standards

* Use the InsForge server client for all database operations.
* Never expose privileged database operations to the browser.
* Apply Row-Level Security (RLS) to all protected tables.
* Never perform unrestricted queries on user data.
* Keep database schema changes synchronized with `architecture.md`.

---

## UI Standards

* Build reusable components.
* Avoid duplicate UI implementations.
* Use the shared design system defined in `ui-tokens.md`.
* Avoid hardcoded spacing, colors and typography values.
* Keep components focused on presentation rather than business logic.

---

## Error Handling

* Wrap all external API calls in `try/catch`.
* Log all AI workflow failures.
* Display meaningful error messages to users.
* Prevent failures in one module from affecting unrelated features.
* Never expose internal errors to the user interface.

---

## Documentation Standards

* Keep documentation synchronized with implementation.
* Update architecture documentation whenever the system design changes.
* Record significant implementation decisions.
* Maintain clear comments only where additional context is valuable.
* Remove obsolete documentation as features evolve.

---

## File and Folder Naming

* Folders: **kebab-case** — `claim-details`, `fraud-investigation`, `claim-upload`
* Component files: **PascalCase** — `ClaimCard.tsx`, `InvestigationTimeline.tsx`
* Utility files: **camelCase** — `langgraph.ts`, `chromadb.ts`, `utils.ts`
* Type files: **camelCase** — `claim.ts`, `investigation.ts`, `report.ts`
* API route files: always `route.ts`
* Server Action files: **camelCase** — `claims.ts`, `investigations.ts`, `reports.ts`
* One component per file — never export multiple components from one file
* Index files only inside `components/ui/` — never create barrel exports elsewhere

---

## Component Structure

Every component follows this exact structure:

```typescript
"use client"; // Only when required

// 1. External imports
import { useState } from "react";

// 2. Internal imports
import { Button } from "@/components/ui/button";
import { RiskScore } from "@/components/investigation/RiskScore";

// 3. Type definitions
type Props = {
  investigationId: string;
  riskScore: number;
};

// 4. Component
export function InvestigationCard({
  investigationId,
  riskScore,
}: Props) {
  // State

  // Derived values

  // Event handlers

  // JSX
}
```

* Prefer named exports for all components.
* Define component props directly above the component unless shared across multiple files.
* Avoid inline styles. Use Tailwind utility classes and the shared design tokens from `ui-tokens.md`.
* Keep components focused on presentation only. Business logic belongs in Server Actions, API routes or AI services.

---

## API Route Handlers

```typescript
// app/api/investigation/start/route.ts

import { NextRequest, NextResponse } from "next/server";
import { createInsforgeServer } from "@/lib/insforge-server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request

    // Execute LangGraph workflow

    return NextResponse.json({
      success: true,
      data: result,
    });
  } catch (error) {
    console.error("[investigation/start]", error);

    return NextResponse.json(
      {
        success: false,
        error: "Internal Server Error",
      },
      {
        status: 500,
      },
    );
  }
}
```

### API Standards

* Every route handler must use `try/catch`.
* Validate all request payloads before processing.
* Keep route handlers lightweight by delegating business logic to services or AI agents.
* Log errors using the API route as a prefix (e.g., `[claims/upload]`, `[investigation/start]`).
* Always return responses using the following structure:

```typescript
{
  success: boolean;
  data?: T;
  error?: string;
}
```

* Never expose internal exception details to the client.
* Return appropriate HTTP status codes for validation errors, authorization failures and server errors.

---

## Server Actions

```typescript
// actions/claims.ts

"use server";

import { revalidatePath } from "next/cache";
import { createInsforgeServer } from "@/lib/insforge-server";

export async function uploadClaim(formData: ClaimFormData) {
  try {
    const insforge = await createInsforgeServer();

    // Validate claim data

    // Save claim to database

    revalidatePath("/claims");

    return { success: true };
  } catch (error) {
    console.error("[actions/claims]", error);

    return {
      success: false,
      error: "Failed to upload claim.",
    };
  }
}
```

### Server Action Standards

* Every Server Action must use `try/catch`.
* Every Server Action returns:

```typescript
{
  success: boolean;
  error?: string;
}
```

* Always call `revalidatePath()` after database mutations.
* Never throw errors directly from Server Actions.
* Keep Server Actions focused on user-initiated database operations.

---

## AI Agent Development

```typescript
// agents/investigation-agent.ts

export async function investigateClaim(
  claimId: string,
): Promise<{
  success: boolean;
  evidence?: InvestigationEvidence;
  error?: string;
}> {
  try {
    // Analyze healthcare claim

    return {
      success: true,
      evidence,
    };
  } catch (error) {
    await logAgentError(claimId, error);

    return {
      success: false,
      error: String(error),
    };
  }
}
```

### AI Agent Standards

* Every AI agent returns:

```typescript
{
  success: boolean;
  error?: string;
}
```

* Every AI agent must implement `try/catch`.
* Log all failures to the `agent_logs` table.
* AI agents must never import React components.
* AI agents must never call browser APIs.
* Keep every AI agent focused on a single responsibility.
* Communication between agents must occur through the LangGraph Orchestrator.

---

## InsForge Client Usage

```typescript
// Browser Context
// Client Components only

import { insforge } from "@/lib/insforge-client";
```

```typescript
// Server Context
// Server Components, API Routes,
// Server Actions and LangGraph Workflows

import { createInsforgeServer } from "@/lib/insforge-server";

const insforge = await createInsforgeServer();
```

### InsForge Standards

* Never use the browser client in server-side code.
* Never use the server client inside Client Components.
* Always await `createInsforgeServer()`.
* Apply Row-Level Security (RLS) to every protected query.
* Never expose privileged database operations to the browser.

---

## Error Handling

* Never leave `catch` blocks empty.
* Every error log must include a descriptive context prefix.
* Display user-friendly error messages in the UI.
* Never expose stack traces or internal exceptions.
* AI workflow failures must be recorded in the `agent_logs` table.
* API routes should return generic server errors with appropriate HTTP status codes.
* Failed AI investigations should never crash the complete LangGraph workflow.

---

## Application Events

The Healthcare Fraud Detection Platform records the following application events throughout the investigation lifecycle. These events are stored in the database and are used for dashboard statistics, audit logs and investigation tracking.

| Event                      | When                                           | Key Properties                              |
| -------------------------- | ---------------------------------------------- | ------------------------------------------- |
| `claim_uploaded`           | A healthcare claim is successfully uploaded    | claimId, userId                             |
| `ocr_completed`            | OCR extraction completes successfully          | claimId, processingTime                     |
| `investigation_started`    | A LangGraph investigation workflow begins      | investigationId, claimId                    |
| `fraud_analysis_completed` | Fraud Intelligence Agent finishes analysis     | investigationId, riskScore, confidenceScore |
| `report_generated`         | Investigation report is successfully generated | reportId, investigationId                   |

These five events are the only application events in this project. Do not introduce additional event types without updating this document first.

Dashboard metrics are calculated directly from the InsForge PostgreSQL database using investigation records, claims and reports rather than an external analytics service.

---

## Environment Variables

All environment variables are stored in `.env.local` during development. Never hardcode API keys, URLs or secrets anywhere in the codebase.

| Variable                        | Used In                   |
| ------------------------------- | ------------------------- |
| `NEXT_PUBLIC_INSFORGE_URL`      | `lib/insforge-client.ts`  |
| `NEXT_PUBLIC_INSFORGE_ANON_KEY` | `lib/insforge-client.ts`  |
| `GEMINI_API_KEY`                | `lib/gemini.ts`           |
| `NEXT_PUBLIC_APP_URL`           | Application configuration |
| `CHROMA_DB_PATH`                | `rag/vectordb.ts`         |
| `MODEL_PATH`                    | `ml/predictor.py`         |
| `OCR_MODEL_PATH`                | `ocr/extractor.py`        |

Environment variables prefixed with `NEXT_PUBLIC_` are accessible from the browser.

Never expose API keys, database credentials or other sensitive values using the `NEXT_PUBLIC_` prefix.

---

## Fraud Risk Threshold

The fraud risk threshold is defined once as a shared constant. Never hardcode this value anywhere else in the project.

```typescript
// lib/constants.ts

export const FRAUD_RISK_THRESHOLD = 0.7;
```

Import and use `FRAUD_RISK_THRESHOLD` wherever fraud classifications or investigation decisions depend on a minimum confidence level.

---

## Import Aliases

Always use the `@/` alias. Avoid relative imports that traverse multiple directory levels.

```typescript
// Correct

import { Button } from "@/components/ui/button";
import { createInsforgeServer } from "@/lib/insforge-server";
import { FRAUD_RISK_THRESHOLD } from "@/lib/constants";

// Avoid

import { Button } from "../../../components/ui/button";
```

---

## Comments

* Write self-explanatory code whenever possible.
* Comments should explain **why**, not **what**.
* Add brief comments only when describing non-obvious implementation decisions.
* AI agent implementations may include short comments explaining workflow decisions or LangGraph node behavior.
* Never leave `TODO` comments in committed code.

---

## Dependencies

Never install a new dependency without a clear technical justification.

Before installing a package, verify:

1. Can the functionality be implemented using the existing project stack?
2. Does Next.js already provide this capability?
3. Does shadcn/ui already include the required component?
4. Is there a simpler native solution?

### Approved Dependencies

* `@insforge/ssr` — InsForge client
* `@langchain/langgraph` — Multi-agent workflow orchestration
* `@google/genai` — Gemini API
* `xgboost` — Healthcare fraud prediction
* `paddleocr` — OCR processing
* `chromadb` — Vector database
* `zod` — Schema validation
* `lucide-react` — Icons
* `tailwindcss` — Styling
* `shadcn/ui` — UI components

Do not introduce additional dependencies without updating this document first.
---