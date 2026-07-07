# Library Docs

Project-specific implementation guidelines for every third-party library used in the Healthcare Fraud Detection Platform.

This document defines how each library is used within this project, recommended usage patterns and project-specific constraints.

Always consult this document before implementing a feature that depends on an external library.

---

# Before Using Any Library

Before integrating or modifying any third-party library:

1. **Read `AGENTS.md`** to understand how the library fits into the overall multi-agent workflow.

2. **Check for an MCP Server** if one is available for the library. Use the MCP server for current documentation and debugging before relying on external references.

3. **Read this document** to understand the project's implementation standards for that library.

The order of authority is:

```text
MCP Server
      ↓
AGENTS.md
      ↓
Library Docs
      ↓
Official Documentation
```

General knowledge should only be used when the above resources do not provide the required information.

---

# InsForge

**Purpose**

InsForge provides the application's backend infrastructure.

Responsibilities

* Authentication
* PostgreSQL Database
* File Storage
* Row-Level Security (RLS)
* Realtime Updates

---

## Client vs Server

The application uses two separate InsForge clients.

Never mix them.

```typescript
// Browser Client

import { createBrowserClient } from "@insforge/ssr";

export const insforge = createBrowserClient(
  process.env.NEXT_PUBLIC_INSFORGE_URL!,
  process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY!,
);
```

```typescript
// Server Client

import { createServerClient } from "@insforge/ssr";
import { cookies } from "next/headers";

export const createInsforgeServer = async () => {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_INSFORGE_URL!,
    process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options),
          );
        },
      },
    },
  );
};
```

### Usage Rules

* Browser client is used only inside Client Components.
* Server client is used inside Server Components, API Routes, Server Actions and LangGraph workflows.
* Never expose privileged database operations to the browser.
* Always enable Row-Level Security on protected tables.

---

## Authentication

```typescript
const insforge = await createInsforgeServer();

const {
  data: { user },
} = await insforge.auth.getUser();

if (!user) redirect("/login");
```

Authentication is required before accessing any protected route.

---

### Database Queries

```typescript
// Read claims
const { data, error } = await insforge
  .from("claims")
  .select("*")
  .eq("uploaded_by", user.id)
  .order("created_at", { ascending: false });

// Insert claim
const { data, error } = await insforge
  .from("claims")
  .insert({
    uploaded_by: user.id,
    patient_id,
    provider_id,
    claim_amount,
    status: "uploaded",
  })
  .select()
  .single();

// Update investigation
const { error } = await insforge
  .from("investigations")
  .update({
    investigation_status: "completed",
    overall_risk_score: riskScore,
    fraud_prediction: prediction,
  })
  .eq("claim_id", claimId);
```

### Rules

- Always validate the authenticated user before executing queries.
- Always handle the returned `error` object.
- Use `.single()` whenever exactly one row is expected.
- Use transactions whenever multiple related tables must be updated together.
- Never expose unrestricted queries to the client.
- Protect all sensitive tables using Row-Level Security (RLS).

---

## LangGraph

**Check first:** Check `AGENTS.md` for the installed LangGraph workflow definitions. If a LangGraph MCP server is configured, use it before relying on general documentation.

---

### Investigation Workflow

```typescript
// agents/workflow.ts

import { fraudInvestigationGraph } from "./graph";

const result = await fraudInvestigationGraph.invoke({
  claimId,
  userId,
});
```

The workflow is responsible for coordinating all AI agents involved in a fraud investigation.

---

### Workflow State

Every investigation shares a common workflow state.

```typescript
type InvestigationState = {
  claimId: string;
  userId: string;

  claimData?: Claim;
  ocrData?: OCRResult;

  investigationEvidence?: InvestigationEvidence;
  historicalEvidence?: HistoricalEvidence[];

  fraudPrediction?: FraudPrediction;

  finalReport?: InvestigationReport;

  status:
    | "pending"
    | "running"
    | "completed"
    | "failed";
};
```

---

### Workflow Execution

```
Claim Uploaded
        │
        ▼
OCR Completed
        │
        ▼
LangGraph Orchestrator
        │
 ┌──────┴──────────────┐
 │                     │
 ▼                     ▼
Investigation      Knowledge
Agent              Agent
 │                     │
 └────────┬────────────┘
          ▼
 Fraud Intelligence Agent
          ▼
      Report Agent
          ▼
 Investigation Completed
```

---

### Rules

- Every investigation must begin through the LangGraph Orchestrator.
- Agents never call each other directly.
- Agents communicate only through the shared workflow state.
- Every node returns structured data.
- Agent failures are logged without terminating the complete workflow.
- Investigation state is updated after every successful node execution.
- Reports are generated only after the Fraud Intelligence Agent completes successfully.

---

## Gemini

**Check first:** Check `AGENTS.md` for an installed Gemini skill. If a Gemini MCP server is configured, use it before relying on general documentation.

---

### Purpose

Gemini is responsible for reasoning over structured investigation data and generating explainable fraud assessments.

It is **not** responsible for fraud prediction.

Fraud prediction is performed by the XGBoost model.

Gemini receives:

- Investigation Agent output
- Knowledge Agent output
- XGBoost prediction
- OCR extracted information

and produces an explainable fraud assessment.

---

### Initialization

```typescript
import { GoogleGenAI } from "@google/genai";

export const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY!,
});
```

---

### Fraud Reasoning

```typescript
const response = await ai.models.generateContent({
  model: "gemini-2.5-pro",
  contents: prompt,
});
```

---

### Prompt Structure

Every reasoning prompt should contain:

- Claim Information
- Provider Information
- Patient Information
- OCR Results
- Historical Fraud Cases
- XGBoost Prediction
- Investigation Evidence

Never send raw database records directly to Gemini.

Always construct a structured investigation context first.

---

### Expected Output

Gemini returns structured investigation reasoning.

```typescript
type FraudAssessment = {
  fraudClassification:
    | "Low Risk"
    | "Medium Risk"
    | "High Risk";

  confidence: number;

  reasoning: string;

  evidence: string[];

  recommendations: string[];
};
```

---

### Fraud Intelligence Pipeline

The Fraud Intelligence Agent combines machine learning prediction with large language model reasoning.
---
Investigation Evidence
        │
        ▼
XGBoost
(Fraud Probability)
        │
        ▼
Gemini
(Explainability)
        │
        ▼
Final Fraud Assessment
---

### Rules

- Gemini performs reasoning only.
- Never use Gemini for fraud prediction.
- Always include the XGBoost prediction in the prompt.
- Every response must contain explainable reasoning.
- Validate every AI response before storing it.
- Keep temperature between **0.2** and **0.4** for consistent outputs.
- Never expose raw prompts or API responses to users.
