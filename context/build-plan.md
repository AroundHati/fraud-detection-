# Build Plan

## Core Principle

The Healthcare Fraud Detection Platform will be developed incrementally, with each feature designed, implemented and validated before moving to the next stage. User interfaces will first be created with realistic mock data to establish the complete user experience, after which backend services, AI agents and machine learning components will be integrated step by step.

The development process follows a feature-first approach, ensuring that every module—including claim processing, OCR extraction, AI investigation workflows and reporting—is independently testable before being connected to the rest of the system.

This approach minimizes development complexity, simplifies debugging and allows continuous validation throughout the project while maintaining a production-like architecture.

---

## Phase 1 — Foundation

### 01 Homepage

Build the complete homepage UI for the Healthcare Fraud Detection Platform.

**UI:**

* Navigation bar with logo, Dashboard, Claims, Investigations and Login button
* Hero section introducing the AI-powered Healthcare Fraud Detection Platform
* Features section highlighting:

  * AI Fraud Investigation
  * Multi-Agent Workflow
  * Explainable AI Reports
* System Architecture preview
* Call-to-Action section
* Footer

**Logic:**

* "Get Started" button redirects:

  * `/login` if user is not authenticated
  * `/dashboard` after successful authentication

---

### 02 Authentication

Implement InsForge authentication and role-based access control.

**UI:**

* Login page
* Register page
* Forgot Password page

**Logic:**

* Email and Password Authentication using InsForge Auth
* Session management
* User role management
* Authentication middleware
* Protected routes:

  * `/dashboard`
  * `/claims`
  * `/investigations`
  * `/reports`
  * `/analytics`
* Redirect authenticated users to the dashboard after login

---

### 03 Database Initialization

Create the complete database schema defined in `architecture.md`.

**Logic:**

Create the following tables:

* `users`
* `claims`
* `documents`
* `investigations`
* `agent_runs`
* `agent_logs`
* `reports`

Configure InsForge Storage buckets:

* `claims`
* `prescriptions`
* `discharge-summaries`
* `medical-bills`
* `doctor-notes`
* `reports`

Enable Row-Level Security (RLS) for every table and configure access policies based on authenticated user roles.

---

### 04 Project Configuration

Configure the shared infrastructure used throughout the project.

**Logic:**

* Configure InsForge client and server instances
* Configure Gemini API
* Configure LangGraph
* Configure ChromaDB
* Configure PaddleOCR
* Configure XGBoost inference pipeline
* Create shared utility functions
* Configure environment variables
* Verify all external services are connected successfully before beginning feature development.

---

## Phase 2 — Claim Management

### 05 Claim Upload Page — Full UI

Build the complete claim upload interface using mock data. No backend logic yet.

**UI:**

* Upload healthcare claim card
* Drag-and-drop upload area
* Upload progress indicator
* Supported document types section
* Claim information form with clearly labeled sections:

  * Patient Information

    * Patient ID
    * Patient Name
    * Date of Birth
    * Gender
  * Provider Information

    * Provider ID
    * Provider Name
    * Hospital Name
  * Claim Information

    * Claim Amount
    * Diagnosis Codes
    * Procedure Codes
    * Date of Service
  * Supporting Documents

    * Claim Form
    * Prescription
    * Medical Bill
    * Doctor Notes
    * Discharge Summary
* Submit Claim button

---

### 06 Claim Upload Logic

Connect the claim upload page with InsForge.

**Logic:**

* Save claim details to the `claims` table
* Upload supporting documents to InsForge Storage
* Create document records in the `documents` table
* Automatically generate a unique Claim ID
* Set initial claim status to `uploaded`
* Redirect to the Claim Details page after successful submission

---

### 07 OCR Document Processing

Automatically extract structured information from uploaded healthcare documents.

**UI:**

* OCR processing indicator
* Extraction progress bar
* Structured data preview
* Highlight extracted fields for user review
* "Continue Investigation" button

**Logic:**

* Process uploaded documents using PaddleOCR
* Extract patient information
* Extract provider information
* Extract diagnosis codes
* Extract procedure codes
* Extract claim amount
* Store extracted text in the `documents` table
* Update claim status to `ready_for_investigation`

---

### 08 Claim Review & Validation

Allow users to review extracted information before AI investigation begins.

**UI:**

* Claim summary page
* Uploaded document preview
* Editable extracted fields
* Validation status indicators
* "Start Investigation" button

**Logic:**

* Display OCR results alongside uploaded documents
* Allow manual correction of extracted information
* Validate required fields before submission
* Save updated claim information
* Trigger the LangGraph investigation workflow
* Update claim status to `investigating`

---

## Phase 3 — Dashboard & Claim Management

### 09 Dashboard — Full UI

Build the complete dashboard using realistic mock data. No backend logic yet.

**UI:**

* Statistics cards

  * Total Claims
  * Active Investigations
  * High Risk Claims
  * Completed Investigations

* Investigation Overview Chart

  * Claims by Status
  * Fraud Risk Distribution

* Recent Claims Table

  * Claim ID
  * Patient ID
  * Provider
  * Claim Amount
  * Investigation Status
  * Risk Level

* Recent Investigation Activity

* Quick Actions

  * Upload Claim
  * View Investigations
  * View Reports

---

### 10 Dashboard Logic

Connect dashboard components with InsForge.

**Logic:**

* Retrieve dashboard statistics
* Display latest uploaded claims
* Display active investigations
* Display completed investigations
* Display fraud risk summary
* Refresh dashboard after claim upload or investigation completion

---

### 11 Claim Search, Filters & Pagination

Connect the claim management page to InsForge.

**UI**

* Search bar

  * Search by Claim ID
  * Patient ID
  * Provider ID

* Filters

  * Investigation Status
  * Fraud Risk
  * Date Range

* Sorting

  * Latest Claims
  * Highest Claim Amount
  * Highest Fraud Risk

* Pagination

---

**Logic**

* Search claims by Claim ID
* Search by Patient ID
* Search by Provider ID
* Filter by:

  * Uploaded
  * Processing
  * Investigating
  * Completed
* Filter by fraud risk:

  * Low
  * Medium
  * High
* Sort by:

  * Upload Date
  * Claim Amount
  * Fraud Risk Score
* Display 20 claims per page
* Retrieve total claim count for pagination

---

## Phase 4 — AI Fraud Investigation

### 12 Investigation Workspace — Full UI

Build the complete investigation interface using mock data. No AI logic yet.

**UI:**

* Investigation Header

  * Investigation ID
  * Claim ID
  * Investigation Status
  * Assigned Investigator
  * Overall Risk Indicator

* Claim Summary Card

  * Patient Information
  * Provider Information
  * Claim Amount
  * Diagnosis Codes
  * Procedure Codes

* Uploaded Documents Panel

  * Claim Form
  * Prescription
  * Medical Bill
  * Doctor Notes
  * Discharge Summary

* AI Investigation Timeline

  * Investigation Agent
  * Knowledge Agent
  * Fraud Intelligence Agent
  * Report Agent

* AI Investigation Progress

* Start Investigation Button

---

### 13 LangGraph Multi-Agent Investigation

Initialize the complete AI investigation workflow.

**Logic:**

* POST `/api/investigation/start`
* Load claim information from InsForge
* Load OCR extracted data
* Initialize LangGraph workflow
* Create investigation record
* Execute AI agents
* Store investigation state
* Return investigation progress to the frontend

---

### 14 Investigation Agent

The Investigation Agent performs the primary analysis of the healthcare claim.

**Logic:**

* Analyze uploaded healthcare claim
* Validate diagnosis codes
* Validate procedure codes
* Review provider history
* Review patient history
* Detect duplicate claims
* Detect abnormal reimbursement patterns
* Generate structured investigation evidence
* Save findings to the investigation record

---

### 15 Knowledge Agent (RAG)

Retrieve historical fraud cases and supporting evidence.

**Logic:**

* Generate embeddings from investigation evidence
* Search ChromaDB
* Retrieve similar fraud investigations
* Retrieve healthcare fraud rules
* Retrieve historical claim patterns
* Return relevant supporting evidence to the LangGraph workflow

---

### 16 Fraud Intelligence Agent

Combine machine learning predictions with LLM reasoning.

**Logic:**

* Execute XGBoost fraud prediction
* Calculate fraud probability
* Load Investigation Agent findings
* Load Knowledge Agent evidence
* Send complete investigation context to Gemini
* Generate explainable fraud reasoning
* Calculate confidence score
* Produce final fraud classification

---

### 17 Report Agent

Generate the final explainable investigation report.

**Logic:**

* Compile investigation findings
* Generate executive summary
* Organize supporting evidence
* Create investigation timeline
* Generate fraud recommendations
* Produce PDF investigation report
* Save report to InsForge Storage
* Update investigation status to **Completed**

---

## Phase 5 — Investigation Reports

### 18 Investigation Report — Full UI

Build the complete investigation report interface using mock data.

**UI:**

* Report Header

  * Investigation ID
  * Claim ID
  * Investigation Status
  * Generated Date
  * Overall Fraud Risk Score

* Executive Summary Card

* AI Investigation Timeline

* Fraud Indicators Panel

* Supporting Evidence Panel

* AI Reasoning Panel

* Recommendations Panel

* Export Report Button

---

### 19 Report Generation

Generate a complete explainable fraud investigation report.

**Logic:**

* Load completed investigation
* Load agent outputs
* Load XGBoost prediction
* Load Gemini reasoning
* Generate executive summary
* Compile supporting evidence
* Generate investigation timeline
* Generate recommendations
* Store report in InsForge Storage
* Save report metadata in the database

---

### 20 Report Viewer

Allow investigators to review previous investigations.

**Logic:**

* Retrieve report by Investigation ID
* Display complete investigation
* Download PDF report
* View supporting evidence
* View AI reasoning
* View fraud score

```

---

# Phase 6 — Analytics Dashboard

### 21 Analytics Dashboard — Full UI

Build the analytics dashboard using realistic mock data.

**UI:**

- KPI Cards
  - Total Claims
  - Active Investigations
  - High Risk Claims
  - Fraud Detection Rate

- Investigation Status Chart

- Fraud Risk Distribution

- Claims by Provider

- Investigation Timeline

- Recent Investigation Activity

---

### 22 Analytics Integration

Connect dashboard to InsForge.

**Logic:**

- Calculate Total Claims
- Calculate Active Investigations
- Calculate Fraud Detection Rate
- Retrieve completed investigations
- Retrieve recent investigations
- Display provider statistics
- Display fraud risk distribution
- Update dashboard after investigation completion

---

### 23 Investigation Activity

Display recent investigation activity.

**Logic:**

- Query recent investigations
- Query recent reports
- Query recent AI executions
- Merge activity timeline
- Display chronological investigation history
- Refresh automatically after investigation updates

---

## Feature Count

| Phase | Features |
|------------------------------|----------|
| Phase 1 — Foundation | 4 |
| Phase 2 — Claim Management | 4 |
| Phase 3 — Dashboard & Claim Management | 3 |
| Phase 4 — AI Fraud Investigation | 5 |
| Phase 5 — Investigation Reports | 3 |
| Phase 6 — Analytics Dashboard | 3 |
| **Total** | **22 Features** |
```
---

