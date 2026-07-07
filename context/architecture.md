# Architecture

## Stack

| Layer                          | Tool                     |Purpose                                                                               |
| ------------------------------ | ------------------------ | ------------------------------------------------------------------------------------ |
| Framework                      | Next.js 16 (App Router)  | Full-stack framework for building the web application                                |
| Auth + DB + Storage + Realtime | InsForge                 | Complete backend platform for authentication, database, storage and realtime updates |
| AI Workflow                    | LangGraph                | Multi-agent orchestration and workflow management                                    |
| Large Language Model           | Gemini 2.5 Pro           | Fraud reasoning, evidence analysis and investigation reporting                       |
| Machine Learning Model         | XGBoost                  | Healthcare fraud prediction and risk scoring                                         |
| OCR Engine                     | PaddleOCR                | Extract structured information from medical documents                                |
| Vector Database                | ChromaDB                 | Store and retrieve similar historical fraud cases (RAG)                              |
| Analytics                      | PostHog                  | User activity tracking and application analytics                                     |
| Styling                        | Tailwind CSS + shadcn/ui | Responsive UI components and design system                                           |
| Language                       | TypeScript + Python      | Frontend, backend and AI development                                                 |

---

## Folder Structure

```text
/
├── AGENTS.md
├── context/
│   ├── project-overview.md
│   ├── architecture.md
│   ├── build-plan.md
│   ├── progress-tracker.md
│   ├── code-standards.md
│   ├── library-docs.md
│   ├── ui-rules.md
│   ├── ui-registry.md
│   └── ui-tokens.md
│
├── app/
│   ├── layout.tsx                               → Root layout
│   ├── page.tsx                                 → Landing page
│   │
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx                         → Login page
│   │   └── callback/
│   │       └── page.tsx                         → Authentication callback
│   │
│   ├── dashboard/
│   │   └── page.tsx                             → Main dashboard
│   │
│   ├── claims/
│   │   ├── page.tsx                             → All uploaded claims
│   │   ├── upload/
│   │   │   └── page.tsx                         → Upload new claim
│   │   └── [id]/
│   │       └── page.tsx                         → Claim details
│   │
│   ├── investigations/
│   │   ├── page.tsx                             → Investigation dashboard
│   │   └── [id]/
│   │       └── page.tsx                         → Investigation details
│   │
│   ├── reports/
│   │   ├── page.tsx                             → Investigation reports
│   │   └── [id]/
│   │       └── page.tsx                         → Report viewer
│   │
│   ├── analytics/
│   │   └── page.tsx                             → Fraud analytics dashboard
│   │
│   └── api/
│       ├── claims/
│       │   ├── upload/route.ts                  → Upload claim
│       │   ├── process/route.ts                 → Start OCR & preprocessing
│       │   └── status/route.ts                  → Claim processing status
│       │
│       ├── investigation/
│       │   ├── start/route.ts                   → Start LangGraph workflow
│       │   ├── chat/route.ts                    → AI Investigator Chat
│       │   └── report/route.ts                  → Generate investigation report
│       │
│       └── notifications/
│           └── route.ts                         → Real-time notifications
│
├── agents/
│   ├── orchestrator.ts                          → LangGraph workflow controller
│   ├── claim-agent.ts                           → Claim analysis agent
│   ├── provider-agent.ts                        → Provider intelligence agent
│   ├── patient-agent.ts                         → Patient intelligence agent
│   ├── fraud-agent.ts                           → Fraud reasoning agent
│   ├── evidence-agent.ts                        → Evidence validation agent
│   ├── report-agent.ts                          → Investigation report generation
│   └── types.ts                                 → Shared agent types
│
├── ml/
│   ├── model.pkl                               → Trained XGBoost model
│   ├── predictor.py                             → Fraud prediction
│   ├── preprocess.py                            → Feature preprocessing
│   └── feature_engineering.py                   → Feature engineering logic
│
├── ocr/
│   ├── extractor.py                             → PaddleOCR extraction
│   ├── parser.py                                → Medical document parser
│   └── utils.py                                 → OCR utilities
│
├── rag/
│   ├── embeddings.ts                            → Generate embeddings
│   ├── retriever.ts                             → Retrieve similar fraud cases
│   └── vectordb.ts                              → ChromaDB operations
│
├── actions/
│   ├── claims.ts                                → Claim CRUD operations
│   ├── investigations.ts                        → Investigation updates
│   └── reports.ts                               → Report management
│
├── components/
│   ├── ui/                                      → shadcn/ui components
│   │
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   │
│   ├── dashboard/
│   │   ├── StatsCards.tsx
│   │   ├── RecentInvestigations.tsx
│   │   ├── FraudTrends.tsx
│   │   └── RiskDistribution.tsx
│   │
│   ├── claims/
│   │   ├── ClaimUploader.tsx
│   │   ├── ClaimTable.tsx
│   │   ├── ClaimFilters.tsx
│   │   └── ClaimDetails.tsx
│   │
│   ├── investigation/
│   │   ├── AgentTimeline.tsx
│   │   ├── RiskScore.tsx
│   │   ├── EvidencePanel.tsx
│   │   ├── AIReasoning.tsx
│   │   └── InvestigatorChat.tsx
│   │
│   ├── reports/
│   │   ├── ReportViewer.tsx
│   │   └── ReportExport.tsx
│   │
│   └── analytics/
│       ├── FraudChart.tsx
│       ├── ProviderChart.tsx
│       ├── ClaimHeatmap.tsx
│       └── KPIcards.tsx
│
├── lib/
│   ├── insforge-client.ts                       → Browser client
│   ├── insforge-server.ts                       → Server client
│   ├── langgraph.ts                             → LangGraph initialization
│   ├── gemini.ts                                → Gemini configuration
│   ├── chromadb.ts                              → ChromaDB client
│   ├── posthog.ts                               → PostHog initialization
│   └── utils.ts                                 → Shared utilities
│
└── types/
    ├── claim.ts                                 → Claim interfaces
    ├── investigation.ts                         → Investigation interfaces
    ├── report.ts                                → Report interfaces
    └── index.ts                                 → Shared project types
```

---

## System Boundaries

| Folder        | Owns                                                                                                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/`        | Next.js pages, layouts and API routes only. No AI logic or direct database queries inside UI components.                                                                              |
| `agents/`     | All LangGraph agent implementations including claim analysis, provider intelligence, patient intelligence, fraud reasoning, evidence validation and report generation. No React code. |
| `ml/`         | Machine learning components only. Contains the trained XGBoost model, preprocessing pipeline and fraud prediction logic.                                                              |
| `ocr/`        | OCR pipeline for extracting structured information from uploaded healthcare documents.                                                                                                |
| `rag/`        | Retrieval-Augmented Generation (RAG) components including ChromaDB indexing, embedding generation and historical fraud case retrieval.                                                |
| `actions/`    | Next.js Server Actions responsible for user-triggered database mutations such as claim uploads, investigation updates and report management.                                          |
| `components/` | Reusable UI components only. No business logic, AI processing or database operations.                                                                                                 |
| `lib/`        | Shared libraries, third-party client initialization, configuration files and utility functions.                                                                                       |
| `types/`      | Shared TypeScript interfaces, enums and data models used throughout the application.                                                                                                  |
| `context/`    | Project documentation, development guidelines, architecture references and implementation plans.                                                                                      |

---



## Data Flow

### UI Mutations (Server Actions)

```text
User interaction in component
        ↓
Server Action in actions/
        ↓
InsForge Database write
        ↓
Realtime UI update or page revalidation
```

---

### Claim Processing (API Routes)

```text
User uploads healthcare claim
        ↓
API route in app/api/claims/upload
        ↓
Claim stored in InsForge Storage
        ↓
Claim metadata saved in InsForge Database
        ↓
OCR pipeline extracts structured information
        ↓
Structured claim data stored in database
        ↓
Claim marked as Ready for Investigation
```

---

### AI Fraud Investigation (LangGraph Workflow)

```text
User clicks "Start Investigation"
        ↓
API route in app/api/investigation/start
        ↓
LangGraph Orchestrator initializes workflow
        ↓
Runs Claim Analysis Agent
        ↓
Runs Provider Intelligence Agent
        ↓
Runs Patient Intelligence Agent
        ↓
Retrieves similar historical fraud cases (ChromaDB)
        ↓
XGBoost predicts fraud probability
        ↓
Gemini performs evidence reasoning
        ↓
Evidence Validation Agent verifies findings
        ↓
Decision Agent calculates final fraud score
        ↓
Investigation report generated
        ↓
Results saved to InsForge Database
        ↓
Dashboard updated
```
---

### Investigation Report Generation

```text
User opens Investigation Report
        ↓
API route in app/api/investigation/report
        ↓
Load investigation results
        ↓
Gemini generates explainable report
        ↓
Risk score, evidence and reasoning compiled
        ↓
Final report saved to InsForge Storage
        ↓
Report displayed in dashboard
```
---


## InsForge Database Schema

### `users`

| Column       | Type        | Notes                                     |
| ------------ | ----------- | ----------------------------------------- |
| id           | uuid        | References auth.users                     |
| full_name    | text        | User's full name                          |
| email        | text        | Retrieved from authentication             |
| role         | text        | admin / investigator / auditor / hospital |
| organization | text        | Hospital or organization name             |
| created_at   | timestamptz | Account creation timestamp                |
| updated_at   | timestamptz | Last profile update                       |

---

### `claims`

| Column            | Type        | Notes                                             |
| ----------------- | ----------- | ------------------------------------------------- |
| id                | uuid        | Primary key                                       |
| uploaded_by       | uuid        | References users.id                               |
| patient_id        | text        | Patient identifier                                |
| provider_id       | text        | Healthcare provider identifier                    |
| claim_amount      | numeric     | Claimed reimbursement amount                      |
| diagnosis_codes   | jsonb       | ICD diagnosis codes                               |
| procedure_codes   | jsonb       | CPT/HCPCS procedure codes                         |
| claim_date        | date        | Claim submission date                             |
| status            | text        | uploaded / processing / investigating / completed |
| fraud_probability | numeric     | XGBoost prediction score                          |
| created_at        | timestamptz | Upload timestamp                                  |
| updated_at        | timestamptz | Last modification                                 |

---

### `documents`

| Column         | Type        | Notes                                                                 |
| -------------- | ----------- | --------------------------------------------------------------------- |
| id             | uuid        | Primary key                                                           |
| claim_id       | uuid        | References claims.id                                                  |
| document_type  | text        | claim / prescription / discharge_summary / medical_bill / doctor_note |
| file_url       | text        | InsForge Storage file path                                            |
| extracted_text | text        | OCR extracted content                                                 |
| uploaded_at    | timestamptz | Upload timestamp                                                      |

---

### `investigations`

| Column               | Type        | Notes                             |
| -------------------- | ----------- | --------------------------------- |
| id                   | uuid        | Primary key                       |
| claim_id             | uuid        | References claims.id              |
| overall_risk_score   | numeric     | Final fraud risk score            |
| fraud_prediction     | text        | genuine / suspicious / fraudulent |
| confidence_score     | numeric     | AI confidence score               |
| investigation_status | text        | pending / running / completed     |
| assigned_to          | uuid        | Investigator (optional)           |
| started_at           | timestamptz | Investigation start time          |
| completed_at         | timestamptz | Investigation completion time     |

---

### `agent_runs`

| Column           | Type        | Notes                                                                  |
| ---------------- | ----------- | ---------------------------------------------------------------------- |
| id               | uuid        | Primary key                                                            |
| investigation_id | uuid        | References investigations.id                                           |
| agent_name       | text        | ClaimAgent / ProviderAgent / PatientAgent / FraudAgent / EvidenceAgent |
| status           | text        | running / completed / failed                                           |
| execution_time   | numeric     | Execution time in seconds                                              |
| created_at       | timestamptz | Execution timestamp                                                    |

---

### `agent_logs`

| Column     | Type        | Notes                    |
| ---------- | ----------- | ------------------------ |
| id         | uuid        | Primary key              |
| run_id     | uuid        | References agent_runs.id |
| log_level  | text        | info / warning / error   |
| message    | text        | Agent execution log      |
| created_at | timestamptz | Log timestamp            |

---

### `reports`

| Column            | Type        | Notes                                           |
| ----------------- | ----------- | ----------------------------------------------- |
| id                | uuid        | Primary key                                     |
| investigation_id  | uuid        | References investigations.id                    |
| executive_summary | text        | AI-generated investigation summary              |
| evidence          | jsonb       | Supporting fraud evidence                       |
| recommendations   | text        | Suggested next actions                          |
| report_url        | text        | Generated PDF report stored in InsForge Storage |
| generated_at      | timestamptz | Report generation timestamp                     |

---


## InsForge Storage

| Bucket              | Path                                  | Contents                                 |
| ------------------- | ------------------------------------- | ---------------------------------------- |
| claims              | claims/{claim_id}/                    | Uploaded healthcare claim documents      |
| prescriptions       | prescriptions/{claim_id}/             | Prescription documents                   |
| discharge-summaries | discharge-summaries/{claim_id}/       | Hospital discharge summaries             |
| medical-bills       | medical-bills/{claim_id}/             | Medical bills and invoices               |
| doctor-notes        | doctor-notes/{claim_id}/              | Doctor consultation notes                |
| reports             | reports/{investigation_id}/report.pdf | AI-generated fraud investigation reports |

Access: Authenticated users only. Access permissions are controlled using InsForge Row-Level Security (RLS) based on user roles and ownership.

---

## Authentication

* Provider: InsForge Auth
* Methods: Email/Password Authentication
* User Roles:

  * Administrator
  * Investigator
  * Auditor
  * Hospital Staff
* Protected Routes:

  * `/dashboard`
  * `/claims`
  * `/claims/[id]`
  * `/investigations`
  * `/investigations/[id]`
  * `/reports`
  * `/analytics`
* Public Routes:

  * `/`
  * `/login`
* Authentication middleware validates every protected request before granting access.
* After successful login, users are redirected to the dashboard according to their assigned role.

---


## InsForge Client Pattern

The application uses **two separate InsForge client instances**. The browser client is responsible for user authentication and client-side interactions, while the server client handles secure database operations, file storage, AI workflows and API requests.

**Never mix the browser client and server client.**

```typescript
// lib/insforge-client.ts
// Browser-side client
// Used for authentication, session management and client-side interactions.

import { createBrowserClient } from "@insforge/ssr";

export const insforge = createBrowserClient(
  process.env.NEXT_PUBLIC_INSFORGE_URL!,
  process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY!,
);
```

```typescript
// lib/insforge-server.ts
// Server-side client
// Used inside API routes, Server Actions and AI agent workflows.

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

### Usage Guidelines

| Client               | Used For                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `insforge-client.ts` | User authentication, session state, realtime subscriptions and client-side interactions     |
| `insforge-server.ts` | Database operations, file uploads, API routes, Server Actions and LangGraph agent workflows |

The browser client must never perform privileged database operations. All secure queries, storage access and AI workflow interactions should be executed through the server client.

---

## LangGraph Workflow Pattern

Every healthcare claim investigation is executed through a single LangGraph workflow. The workflow coordinates all AI agents, manages shared investigation state and ensures that every claim follows the same execution pipeline.

```typescript
// Start a new healthcare fraud investigation

const workflow = await fraudInvestigationGraph.invoke({
  claimId: claim.id,
  userId: session.user.id,
});
```

### Workflow Responsibilities

* Initialize the investigation state.
* Coordinate communication between AI agents.
* Maintain shared context throughout the investigation.
* Execute fraud prediction using the XGBoost model.
* Retrieve similar historical fraud cases from ChromaDB.
* Generate the final explainable investigation report.
* Return the completed investigation to the dashboard.

---

## Claim Processing Pattern

**Healthcare Claim Upload & Processing**

```typescript
// Upload healthcare claim and start processing

const formData = new FormData();
formData.append("claim", uploadedFile);

const response = await fetch("/api/claims/upload", {
  method: "POST",
  body: formData,
});

const data = await response.json();

// data.claimId         → Unique claim identifier
// data.status          → uploaded | processing | completed
// data.documentUrl     → Stored document location
// data.investigationId → Investigation workflow identifier
```

### Processing Pipeline

```text
User uploads healthcare claim
        ↓
Store document in InsForge Storage
        ↓
Create claim record in InsForge Database
        ↓
Extract document using PaddleOCR
        ↓
Generate structured claim information
        ↓
Launch LangGraph investigation workflow
        ↓
Return investigation ID to frontend
```

---

## Multi-Agent Fraud Investigation Pattern

```typescript
// Initialize LangGraph workflow

const investigation = await fraudInvestigationGraph.invoke({
  claimId: claim.id,
  userId: session.user.id,
});
```

### Investigation Workflow

```text
Healthcare Claim Uploaded
          │
          ▼
Claim stored in InsForge
          │
          ▼
OCR extracts structured information
          │
          ▼
LangGraph Orchestrator
          │
     ┌────┴───────────────┐
     │                    │
     ▼                    ▼
Investigation Agent   Knowledge Agent
     │                    │
     └──────────┬─────────┘
                ▼
      Fraud Intelligence Agent
                │
                ▼
          Report Agent
                │
                ▼
     Investigation Report
                │
                ▼
     Results saved to InsForge
                │
                ▼
        Dashboard Updated
```

---

## AI Agent Responsibilities

### 1. Investigation Agent

**Purpose**

Perform the primary investigation by analyzing all structured healthcare claim information.

**Responsibilities**

* Analyze uploaded healthcare claims
* Validate diagnosis and procedure codes
* Review provider claim history
* Review patient claim history
* Detect duplicate or suspicious claims
* Identify abnormal reimbursement patterns
* Produce structured investigation evidence

**Output**

* Claim analysis
* Provider analysis
* Patient analysis
* Initial fraud indicators

---

### 2. Knowledge Agent

**Purpose**

Retrieve external knowledge that can support the investigation.

**Responsibilities**

* Search ChromaDB for similar fraud cases
* Retrieve historical investigation reports
* Retrieve fraud detection rules
* Retrieve insurance policy references
* Provide supporting evidence for reasoning

**Output**

* Historical fraud cases
* Relevant regulations
* Supporting evidence

---

### 3. Fraud Intelligence Agent

**Purpose**

Combine machine learning predictions with LLM reasoning to determine the final fraud assessment.

**Responsibilities**

* Execute XGBoost fraud prediction
* Analyze evidence from previous agents
* Perform contextual reasoning using Gemini
* Calculate fraud probability
* Generate explainable reasoning
* Produce confidence score

**Output**

* Fraud classification
* Risk score
* Confidence score
* Explainable reasoning

---

### 4. Report Agent

**Purpose**

Generate the final investigation report for investigators.

**Responsibilities**

* Compile investigation findings
* Generate executive summary
* Organize supporting evidence
* Create AI investigation report
* Export report to PDF
* Store report in InsForge Storage

**Output**

* Investigation report
* Executive summary
* Fraud recommendation
* PDF report

---

## LangGraph Orchestrator

The LangGraph Orchestrator coordinates the complete investigation workflow. It is responsible for maintaining the shared workflow state and ensuring every AI agent executes in the correct sequence.

**Responsibilities**

* Initialize investigation workflow
* Route information between agents
* Maintain shared investigation state
* Trigger feedback loops when additional evidence is required
* Handle agent failures and retries
* Collect outputs from all agents
* Return the final investigation result

The orchestrator is a workflow controller and is **not counted as an AI agent**.

---

## Invariants

The following architectural rules must always be enforced throughout the Healthcare Fraud Detection Platform.

* API routes contain no UI logic. UI components contain no business logic or direct database operations.
* AI agents inside `/agents` must never import or depend on React components.
* Server Actions must never directly invoke LangGraph agents. All AI workflows are triggered through API routes.
* All database reads and writes must use the InsForge server client (`createInsforgeServer()`). The browser client is only used for authentication, session management   and realtime subscriptions.
* Every healthcare claim must be successfully stored before any AI investigation begins.
* OCR processing must complete before the LangGraph investigation workflow is executed.
* The LangGraph Orchestrator is the only component responsible for coordinating communication between AI agents.
* AI agents must never communicate directly with each other. All information exchange occurs through the shared LangGraph state.
* The Investigation Agent is responsible only for evidence collection and anomaly detection. It must never assign a final fraud classification.
* The Knowledge Agent must only retrieve historical cases and supporting context. It must never modify investigation results.
* The Fraud Intelligence Agent is the only component permitted to combine XGBoost predictions with Gemini reasoning to produce the final fraud assessment.
* Every fraud prediction must include an explainable reasoning summary and a confidence score.
* The Report Agent must generate the final investigation report only after all required agents complete successfully.
* Every AI agent execution must be recorded in the `agent_runs` and `agent_logs` tables for auditability.
* Every uploaded document must be preserved in InsForge Storage. Original files must never be modified or overwritten during processing.
* All ChromaDB retrieval results are treated as supporting evidence only and must never replace model predictions or LLM reasoning.
* All database queries must be scoped according to the authenticated user's role and permissions using InsForge Row-Level Security (RLS).
* Investigation reports are immutable after generation. Any subsequent analysis must create a new investigation record rather than modifying an existing report.
* All application styling must use the project's shared design system defined in `ui-tokens.md`. Hardcoded color values should be avoided.
---