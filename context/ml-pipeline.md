# ML Pipeline

Machine learning components for the FraudShield Healthcare Fraud Detection Platform. This document tracks the current status, planned architecture and implementation details for all ML/AI components.

---

## Current Status

| Component | Status | Location |
|-----------|--------|----------|
| XGBoost fraud prediction | Not implemented | `ml/` |
| PaddleOCR document extraction | Not implemented | `ocr/` |
| ChromaDB vector database (RAG) | Not implemented | `rag/` |
| Gemini reasoning (LLM) | Not implemented | `lib/gemini.ts` |
| LangGraph orchestration | Not implemented | `agents/` |

---

## Planned Architecture

### ML Pipeline Flow

```
Healthcare Claim Uploaded
        │
        ▼
OCR Document Processing (PaddleOCR)
        │
        ▼
Feature Extraction & Preprocessing
        │
        ▼
XGBoost Fraud Prediction
        │
        ▼
Gemini Reasoning (Explainability)
        │
        ▼
Final Fraud Assessment
```

---

## 1. XGBoost Fraud Prediction

### Purpose

Predict fraud probability for healthcare claims using a trained XGBoost model.

### Planned Files

| File | Purpose |
|------|---------|
| `ml/model.pkl` | Trained XGBoost model (binary classification) |
| `ml/predictor.py` | Model inference and prediction logic |
| `ml/preprocess.py` | Feature preprocessing pipeline |
| `ml/feature_engineering.py` | Feature engineering logic |

### Expected Features

From `feature_columns.json`:
- Claim amount
- Diagnosis code frequency
- Provider claim history
- Patient claim history
- Procedure code patterns
- Claim date patterns
- Geographic features

### Model Output

```python
{
  "fraud_probability": 0.85,
  "prediction": "fraudulent",  # genuine | suspicious | fraudulent
  "confidence": 0.92,
  "feature_importance": { ... }
}
```

### Fraud Risk Thresholds

```typescript
// lib/constants.ts
export const FRAUD_RISK_THRESHOLD = 0.7;

// Risk levels:
// 0.0 - 0.3 → Low Risk (genuine)
// 0.3 - 0.7 → Medium Risk (suspicious)
// 0.7 - 1.0 → High Risk (fraudulent)
```

### Integration Point

The Fraud Intelligence Agent (Phase 4, Feature 16) will call the XGBoost predictor as part of the LangGraph workflow.

---

## 2. PaddleOCR Document Processing

### Purpose

Extract structured information from uploaded healthcare documents (claim forms, prescriptions, medical bills, doctor notes, discharge summaries).

### Planned Files

| File | Purpose |
|------|---------|
| `ocr/extractor.py` | PaddleOCR extraction engine |
| `ocr/parser.py` | Medical document parser (structured fields) |
| `ocr/utils.py` | OCR utilities (text cleaning, validation) |

### Expected Extraction

| Document Type | Extracted Fields |
|---------------|------------------|
| Claim Form | Patient ID, Provider ID, Claim Amount, Diagnosis Codes, Procedure Codes |
| Prescription | Medication name, Dosage, Prescriber, Date |
| Medical Bill | Total amount, Itemized charges, Provider |
| Doctor Notes | Diagnosis, Treatment plan, Notes |
| Discharge Summary | Admission/Discharge dates, Diagnosis, Procedures |

### Processing Pipeline

```
Document Upload
        │
        ▼
File Type Detection
        │
        ▼
PaddleOCR Text Extraction
        │
        ▼
Structured Data Parsing
        │
        ▼
Data Validation
        │
        ▼
Store in documents table (extracted_text column)
```

### Integration Point

The OCR pipeline runs as Feature 07 (OCR Document Processing) and is triggered automatically after claim upload (Feature 06).

---

## 3. ChromaDB Vector Database (RAG)

### Purpose

Store embeddings of historical fraud cases and retrieve similar cases to support AI investigations.

### Planned Files

| File | Purpose |
|------|---------|
| `rag/embeddings.ts` | Generate embeddings from investigation evidence |
| `rag/retriever.ts` | Retrieve similar fraud cases |
| `rag/vectordb.ts` | ChromaDB operations |

### Configuration

| Key | Value |
|-----|-------|
| Database Path | Configured via `CHROMA_DB_PATH` environment variable |
| Collection | `fraud_cases` |

### Retrieval Flow

```
Investigation Evidence
        │
        ▼
Generate Embeddings
        │
        ▼
Search ChromaDB (similarity search)
        │
        ▼
Retrieve Top-K Similar Cases
        │
        ▼
Return to LangGraph Workflow
```

### Integration Point

The Knowledge Agent (Phase 4, Feature 15) uses ChromaDB for RAG retrieval during investigations.

---

## 4. Gemini Reasoning (LLM)

### Purpose

Generate explainable fraud assessments by reasoning over structured investigation data, XGBoost predictions and historical evidence.

### Planned Files

| File | Purpose |
|------|---------|
| `lib/gemini.ts` | Gemini API configuration |

### Configuration

| Key | Value |
|-----|-------|
| Model | `gemini-2.5-pro` |
| API Key | Configured via `GEMINI_API_KEY` environment variable |
| Temperature | 0.2 — 0.4 (for consistent outputs) |

### Expected Input

The Fraud Intelligence Agent sends a structured investigation context containing:
- Claim information
- Provider information
- Patient information
- OCR extracted data
- XGBoost prediction
- Investigation Agent findings
- Knowledge Agent evidence (similar historical cases)

### Expected Output

```typescript
type FraudAssessment = {
  fraudClassification: "Low Risk" | "Medium Risk" | "High Risk";
  confidence: number;
  reasoning: string;
  evidence: string[];
  recommendations: string[];
};
```

### Integration Point

The Fraud Intelligence Agent (Phase 4, Feature 16) calls Gemini for explainability after receiving the XGBoost prediction.

---

## 5. LangGraph Multi-Agent Orchestration

### Purpose

Coordinate all AI agents involved in a healthcare fraud investigation through a shared workflow state.

### Planned Files

| File | Purpose |
|------|---------|
| `agents/orchestrator.ts` | LangGraph workflow controller |
| `agents/claim-agent.ts` | Claim analysis agent |
| `agents/provider-agent.ts` | Provider intelligence agent |
| `agents/patient-agent.ts` | Patient intelligence agent |
| `agents/fraud-agent.ts` | Fraud reasoning agent |
| `agents/evidence-agent.ts` | Evidence validation agent |
| `agents/report-agent.ts` | Investigation report generation |
| `agents/types.ts` | Shared agent types |

### Workflow State

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
  status: "pending" | "running" | "completed" | "failed";
};
```

### Agent Execution Order

```
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
```

### Integration Point

The LangGraph workflow is triggered via API route `/api/investigation/start` (Phase 4, Feature 13).

---

## Implementation Phases

| Phase | Feature | Component | Status |
|-------|---------|-----------|--------|
| Phase 1 | 04 Project Configuration | All ML setup | Pending |
| Phase 2 | 07 OCR Document Processing | PaddleOCR | Pending |
| Phase 4 | 13 LangGraph Multi-Agent Workflow | LangGraph | Pending |
| Phase 4 | 14 Investigation Agent | Claim analysis | Pending |
| Phase 4 | 15 Knowledge Agent (RAG) | ChromaDB | Pending |
| Phase 4 | 16 Fraud Intelligence Agent | XGBoost + Gemini | Pending |
| Phase 4 | 17 Report Agent | Report generation | Pending |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Gemini API authentication |
| `CHROMA_DB_PATH` | ChromaDB storage location |
| `MODEL_PATH` | XGBoost model file path |
| `OCR_MODEL_PATH` | PaddleOCR model path |

---

## Notes

- The XGBoost model file (`model.pkl`) and feature columns (`feature_columns.json`) are expected to exist but have not been created yet.
- PaddleOCR requires Python 3.8+ and the `paddleocr` package.
- ChromaDB can run in-process for development (no separate server needed).
- All ML inference should be performed server-side only — never in the browser.
- Agent failures should be logged to `agent_logs` table without terminating the workflow.
