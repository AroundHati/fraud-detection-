# Project Overview

## About the Project

Healthcare Fraud Detection Platform is an AI-powered multi-agent investigation system designed to assist insurance providers, healthcare organizations, and fraud investigators in identifying potentially fraudulent medical claims.

The platform combines traditional machine learning with Agentic AI to automate the investigation process. Users can upload healthcare claims along with supporting medical documents such as prescriptions, medical bills, discharge summaries, and doctor's notes. The system extracts structured information using OCR, analyzes the claim using a trained XGBoost fraud detection model, retrieves similar historical fraud cases through Retrieval-Augmented Generation (RAG), and coordinates multiple AI agents using LangGraph to generate an explainable fraud investigation report.

Rather than replacing human investigators, the platform acts as an intelligent investigation assistant by highlighting suspicious patterns, presenting supporting evidence, explaining why a claim appears risky, and generating a structured report that investigators can review before making a final decision.

All investigations, reports, and claim history are stored within the platform, providing a centralized workspace for healthcare fraud analysis.

---

# The Problem It Solves

Healthcare insurance fraud costs organizations billions of dollars every year. Investigating suspicious claims is often a slow, repetitive, and document-intensive process that requires investigators to manually review multiple medical records, billing information, provider histories, and reimbursement patterns before reaching a conclusion.

Traditional fraud detection systems typically provide only a fraud score without explaining why a claim appears suspicious, leaving investigators to perform additional manual analysis.

This platform significantly reduces investigation time by automating repetitive tasks while keeping investigators in control of the final decision.

The system automatically:

- Extracts information from uploaded healthcare documents.
- Detects suspicious claim patterns using machine learning.
- Retrieves similar historical fraud cases for comparison.
- Explains the reasoning behind every fraud prediction.
- Generates a structured investigation report with supporting evidence.
- Maintains a complete investigation history for auditing and future reference.

By combining machine learning, retrieval-augmented generation, and multi-agent reasoning, the platform enables investigators to focus on decision-making instead of manual document analysis.

---

# Key Features

- Secure authentication using InsForge Auth.
- Upload healthcare claims and supporting medical documents.
- OCR-based extraction from scanned healthcare records.
- Machine learning fraud prediction using XGBoost.
- Retrieval of similar historical fraud cases using ChromaDB.
- Multi-agent investigation workflow powered by LangGraph.
- Explainable fraud reasoning using Gemini.
- AI-generated investigation reports.
- Investigation dashboard with real-time claim tracking.
- Analytics dashboard for fraud trends and investigation metrics.

---

# Target Users

The platform is designed for:

- Healthcare Insurance Companies
- Claims Investigators
- Fraud Detection Analysts
- Insurance Auditors
- Healthcare Compliance Teams

---

# Technology Overview

The platform combines several AI technologies into a single investigation workflow:

```
Healthcare Documents
        │
        ▼
PaddleOCR
        │
        ▼
XGBoost
        │
        ▼
LangGraph
   │        │
   ▼        ▼
Knowledge Agent
Investigation Agent
        │
        ▼
Fraud Intelligence Agent
        │
        ▼
Report Agent
        │
        ▼
Investigation Report
```

The platform is designed as an explainable AI system, ensuring that every fraud prediction is accompanied by supporting evidence and clear reasoning rather than acting as a black-box model.

---

## Pages

```text
/                       → Homepage
/login                  → Authentication
/dashboard              → Investigation dashboard
/upload-claim           → Upload healthcare claims and documents
/claims                 → All uploaded claims
/claims/[id]            → Individual claim details
/investigations         → Investigation history
/investigations/[id]    → AI investigation workspace
/reports                → Investigation reports
/reports/[id]           → Report viewer
/analytics              → Fraud analytics dashboard
/profile                → User profile & settings
```

---

# Navigation

Enterprise healthcare dashboard.

Top navigation bar.

```text
Dashboard

Claims

Investigations

Reports

Analytics

Profile
```

The application uses a consistent top navigation across every page.

---

# Core User Flow

## Homepage

- Introduces the Healthcare Fraud Detection Platform.
- Shows platform capabilities.
- Logged-in users are redirected to the Dashboard.
- Guests are redirected to Login.

---

## Authentication

- User signs in using InsForge Authentication.
- Google OAuth supported.
- GitHub OAuth optional.
- Successful login redirects to `/dashboard`.

---

# Claim Submission

The investigation begins with uploading a healthcare claim.

The user uploads:

- Claim Form (PDF)
- Prescription
- Medical Bill
- Doctor Notes
- Discharge Summary

The user clicks:

```
Start Investigation
```

The claim is stored in InsForge Storage.

A new investigation record is created.

---

# OCR Processing

Immediately after upload:

- PaddleOCR extracts text from uploaded documents.
- Extracted data is structured.
- User can review extracted information before continuing.
- OCR results are stored in the database.

---

# Investigation Workflow

When the user starts an investigation:

```
Claim

↓

Investigation Agent

↓

Knowledge Agent

↓

Fraud Intelligence Agent

↓

Report Agent

↓

Completed Investigation
```

The workflow is orchestrated using LangGraph.

Each completed agent updates the investigation timeline.

---

# Investigation Agent

Responsibilities:

- Validate uploaded claim.
- Verify document completeness.
- Prepare investigation context.
- Forward structured information to the remaining agents.

---

# Knowledge Agent

Responsibilities:

- Retrieve similar fraud cases.
- Search historical investigations.
- Retrieve insurance policy information.
- Provide supporting evidence.

---

# Fraud Intelligence Agent

Responsibilities:

- Run XGBoost fraud prediction.
- Combine prediction with retrieved evidence.
- Generate explainable fraud reasoning using Gemini.
- Calculate overall fraud risk.

Outputs:

- Fraud Probability
- Confidence Score
- Supporting Evidence
- Risk Classification

---

# Report Agent

Responsibilities:

- Generate structured investigation report.
- Summarize findings.
- Highlight suspicious patterns.
- Recommend next actions.

The report is saved to the database and available for download.

---

# Dashboard

The dashboard provides an overview of investigation activity.

Displays:

- Total Claims
- Active Investigations
- High Risk Claims
- Reports Generated

Recent Activity:

- Claims uploaded
- Investigations completed
- Reports generated

Charts:

- Claims Over Time
- Fraud Risk Distribution
- Investigation Status
- Monthly Fraud Trends

---

# Claims Page

Displays all uploaded claims.

Features:

- Search
- Filters
- Sorting
- Pagination

Each row displays:

- Claim ID
- Patient
- Provider
- Claim Amount
- Risk Score
- Investigation Status
- Date Submitted

Selecting a claim opens the Claim Details page.

---

# Claim Details

Displays complete claim information.

Sections:

- Patient Information
- Provider Information
- Claim Details
- Uploaded Documents
- OCR Results
- Fraud Indicators
- Supporting Evidence
- AI Assessment

Users can launch a new investigation or view an existing investigation.

---

# Investigation Workspace

The investigation workspace displays the live progress of the multi-agent workflow.

Sections:

- Investigation Timeline
- Agent Status
- Retrieved Evidence
- Fraud Risk Score
- AI Explanation
- Supporting Documents

Every completed agent updates the workflow in real time.

---

# Investigation Report

Each completed investigation produces a structured report.

Sections:

- Executive Summary
- Risk Assessment
- Fraud Indicators
- Supporting Evidence
- Historical Case Comparison
- AI Reasoning
- Recommended Actions

Users can:

- View Report
- Download PDF
- Share Report

---

# Analytics

Provides organization-wide fraud insights.

Charts include:

- Claims Submitted
- Fraud Risk Distribution
- Investigation Completion Rate
- High Risk Providers
- Monthly Investigation Trends

Analytics update automatically from the investigation database.

---

## Data Architecture

### Claims Data

- Stored in the `claims` table.
- Created whenever a healthcare claim is uploaded.
- Contains patient, provider, billing and claim metadata.
- Acts as the primary input for every fraud investigation.
- Never modified directly by AI agents.

---

### OCR Data

- Stored in the `documents` table.
- Generated after PaddleOCR processes uploaded healthcare documents.
- Contains structured text extracted from:
  - Claim Forms
  - Prescriptions
  - Medical Bills
  - Doctor Notes
  - Discharge Summaries
- Used by the Investigation Agent during fraud analysis.

---

### Investigation Data

- Stored in the `investigations` table.
- Created when the user starts a new investigation.
- Updated throughout the LangGraph workflow.
- Contains:
  - Investigation Status
  - Fraud Probability
  - Confidence Score
  - Supporting Evidence
  - Agent Outputs
- Represents the complete AI investigation lifecycle.

---

### Investigation Reports

- Stored in the `reports` table.
- Generated by the Report Agent after a successful investigation.
- Contains the final explainable fraud report.
- Never modifies original claim or investigation data.

---

# Features In Scope

- Modern healthcare fraud investigation dashboard.
- Secure authentication using InsForge.
- Healthcare claim upload.
- Multiple healthcare document uploads.
- OCR extraction using PaddleOCR.
- Claim review before investigation.
- LangGraph multi-agent workflow.
- Investigation Agent.
- Knowledge Agent with RAG.
- Fraud Intelligence Agent using XGBoost and Gemini.
- Report Agent for investigation summaries.
- Fraud risk scoring with explainable AI.
- Similar historical fraud case retrieval using ChromaDB.
- Investigation timeline.
- Investigation reports.
- Dashboard analytics.
- Claims management.
- Reports management.
- Analytics dashboard.
- User profile management.

---

# Features Out of Scope

- Real-time hospital integration.
- Electronic Health Record (EHR) integration.
- Insurance payment processing.
- Automatic claim rejection.
- Automatic legal action.
- Multi-organization collaboration.
- Mobile application.
- Offline investigation mode.
- Voice-based document analysis.
- Real-time streaming investigations.
- Live chat between investigators.
- Multi-language OCR.
- Automated retraining of ML models.
- Cloud deployment automation.
- Role-based workflow approvals.

---

# Investigation Events

```typescript
claim_uploaded;

ocr_completed;

investigation_started;

fraud_analysis_completed;

report_generated;
```

---

# Target Users

The platform is intended for:

- Healthcare Insurance Companies
- Fraud Investigation Teams
- Claims Analysts
- Insurance Auditors
- Healthcare Compliance Officers
- Healthcare Data Analysts

---

# Success Criteria

- Users can upload a healthcare claim and supporting documents in under five minutes.
- OCR accurately extracts structured information from uploaded healthcare documents.
- LangGraph successfully coordinates all AI agents.
- XGBoost produces reliable fraud probability predictions.
- Gemini generates clear and explainable fraud reasoning.
- Similar historical fraud cases are retrieved using ChromaDB.
- Investigation reports contain sufficient supporting evidence for human review.
- Dashboard analytics accurately reflect investigation activity.
- All claims, investigations and reports are securely stored in InsForge PostgreSQL.
- The user interface remains consistent across every page.
- The platform assists investigators without replacing human decision-making.


---

## Non-Functional Requirements

- Explainability: Every fraud prediction must include supporting reasoning.
- Security: All healthcare documents must be protected using authentication and Row-Level Security.
- Reliability: A failure in one AI agent must not terminate the entire investigation.
- Scalability: The architecture should support adding new AI agents without major redesign.
- Maintainability: Every module should have a single responsibility and follow the documented architecture.
- Performance: Typical investigations should complete within a few minutes under normal workloads.

---
