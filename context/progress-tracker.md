# Progress Tracker

Update this file after every completed feature. Any AI assistant reading this file should immediately understand the current project status, completed milestones and remaining work.

---

# Current Status

**Current Phase:**
Phase 4A — Professional Investigation Report Generation (Complete)

**Last Completed:**
Phase 4A — PDF report generation with reportlab

**Next Milestone:**
Commit Phase 4A, then proceed with remaining Phase 4 or Phase 5 work

---

# Progress

## Phase 1 — Foundation

- [x] 01 Homepage
- [x] 02 Authentication (login, signup, middleware, auth context, protected routes)
- [x] 02a InsForge Backend Integration — API endpoints corrected and verified against live instance
- [x] 03 Database Initialization — SQLite via Investigation Repository (`storage/fraudshield.db`)
- [x] 04 Project Configuration

---

## Phase 2 — Claim Management

- [x] 05 Claim Upload Page — Full UI (drag-and-drop, file list, upload simulation)
- [x] 06 Claim Upload Logic — Wired to `/api/ml/analyze` with file upload
- [ ] 07 OCR Document Processing
- [ ] 08 Claim Review & Validation

---

## Phase 3 — Dashboard & Claim Management

- [x] 09 Dashboard — Connected to real data from Investigation Repository
- [x] 10 Dashboard Logic — Real stats, recent investigations, empty states
- [x] 11 Claim Search, Filters & Pagination (search, status/risk filters, sorting)

---

## Phase 2A — Connected Workspace (Committed as v2.0-connected-workspace)

- [x] Backend — `ml/api/analyze.py`: POST `/api/ml/analyze` persists to Investigation Repository; GET `/api/ml/investigations` list all; GET `/api/ml/investigations/stats` aggregate counts; GET `/api/ml/investigations/{id}` fetch single
- [x] Frontend API client — `lib/api.ts`: `listInvestigations`, `getInvestigation`, `getInvestigationStats`, typed interfaces
- [x] Dashboard — Real stats from repo, recent investigations, empty states
- [x] Upload — Saves to repository after analysis, shows investigation ID link
- [x] Investigations — Loads from SQLite via `listInvestigations()`, uses DataTable
- [x] Investigation Detail — Fetches by ID from API, maps to `InvestigationDetail` type
- [x] Reports — Shows completed investigations filtered from `listInvestigations()`

---

## Phase 3A — Investigation Details Redesign (In Progress)

- [x] Redesign page to work directly with real API data structure
- [x] Two-column summary (Provider Info + AI Assessment)
- [x] Risk distribution cards (High/Medium/Low counts)
- [x] AI Summary section
- [x] Flagged Providers section (medium/high risk)
- [x] Full provider results table
- [x] Investigation Timeline
- [x] Recommendation with Generate Report action

---

## Phase 4 — AI Fraud Investigation

- [x] 12 Investigation Workspace — Full UI (investigation list, timeline, evidence panel)
- [x] Investigation Agent — `ml/services/investigation_agent.py` + `ml/api/investigate.py` + `AIInvestigationAssistant.tsx`
- [ ] 13 LangGraph Multi-Agent Workflow
- [ ] 14 Investigation Agent — (Template-based complete; LLM-based pending)
- [ ] 15 Knowledge Agent (RAG)
- [ ] 16 Fraud Intelligence Agent
- [ ] 17 Report Agent

---

## Phase 4A — Professional Investigation Report Generation

- [x] `ml/services/report_generator.py` — PDF generation service using reportlab; professional layout with branded header, executive summary, provider info, AI assessment, fraud indicators table, AI explanation narrative, recommendation with next actions, and legal disclaimer footer
- [x] `ml/api/report.py` — FastAPI endpoint `POST /api/ml/investigations/{id}/report` returning PDF binary with Content-Disposition attachment header
- [x] Report router mounted in `ml/api/analyze.py` via `app.include_router()`
- [x] `lib/api.ts` — `generateReport(investigationId, providerId)` function calling the new endpoint
- [x] Investigation Detail page — "Generate Report" button wired with loading state, auto-downloads PDF for selected or first provider
- [x] `reportlab>=4.0.0` added to `ml/requirements.txt`

---

## Phase 5 — Investigation Reports

- [x] 18 Investigation Report — Full UI (report list, PDF/CSV export, risk scores)
- [x] 19 Report Generation — PDF generated via reportlab in `ml/services/report_generator.py`; served by FastAPI endpoint in `ml/api/report.py`; downloaded from frontend via `lib/api.ts` `generateReport()` and triggered by the "Generate Report" button
- [ ] 20 Report Viewer

---

## Phase 6 — Analytics Dashboard

- [x] 21 Analytics Dashboard — Full UI (KPI cards, monthly trends, risk distribution, provider risk, diagnosis distribution)
- [ ] 22 Analytics Integration
- [ ] 23 Investigation Activity

---

## Additional Features Completed

- [x] UI Foundation Redesign — Removed all fake/mock data, deleted dead pages/components, created `components/ui/` library (Button, EmptyState, PageHeader, SectionCard, StatusBadge, DataTable, LoadingState)
- [x] Sidebar — Exactly 4 items: Dashboard, Upload Claims, Investigations, Reports
- [x] Auth Redirect — `middleware.ts` covers `/`, landing page cleaned
- [x] Investigation Details page (`/investigations/[providerId]`) — Redesigned to work with real API data, two-column summary, risk distribution, flagged providers, full results table, timeline, recommendation
- [x] ExplainabilityEngine (`ml/services/explainability.py`) — deterministic rule-based fraud indicators, investigation summary, and recommendations from engineered features + risk scores
- [x] Pipeline integration — ExplainabilityEngine runs after RiskScorer; each provider result now includes `investigation_summary`, `fraud_indicators`, and `recommendation`
- [x] Investigation Repository (`ml/services/investigation_repository.py`) — SQLite persistence layer using Repository Pattern; auto-creates `storage/fraudshield.db`; full CRUD (create, save, get, list, get_latest, update_status, delete, exists); `INV-YYYYMMDD-NNNN` ID generation; dataclass models; parameterised queries; 20 unit tests passing
- [x] Alerts page (`/alerts`) — dedicated alerts page with severity badges, provider IDs, timestamps, read/unread status; fixed routing (was incorrectly pointing to `/dashboard`)
- [x] Settings page (profile form, password change)
- [x] Landing page modification (removed nav links, Book Demo; kept logo, auth buttons, Start Investigating)
- [x] Dashboard layout (sidebar, top navbar, user avatar dropdown with Profile/Settings/Logout)
- [x] Auth system (InsForge client, auth context, middleware, protected routes)
- [x] All pages use design tokens, responsive layout, consistent styling

---

# Project Milestones

- [x] Project Idea Finalized
- [x] System Architecture Designed
- [x] Technology Stack Finalized
- [x] Folder Structure Designed
- [x] Database Schema Designed
- [x] Multi-Agent Architecture Designed
- [x] Documentation Completed
- [x] Development Started
- [ ] MVP Completed
- [ ] Final Testing
- [ ] Deployment

---

# Decisions Made During Development

- Reduced AI architecture from six agents to four specialized agents.
- Adopted LangGraph for workflow orchestration.
- Selected Gemini for reasoning and explainability.
- Selected XGBoost for fraud prediction.
- Selected PaddleOCR for healthcare document extraction.
- Selected ChromaDB for Retrieval-Augmented Generation (RAG).
- Built the homepage as a static Server Component using token-backed Tailwind CSS and public dashboard imagery.
- Created custom InsForge REST client since @insforge/ssr is not publicly available on npm.
- Used cookie-based session detection for middleware (cookie name: insforge-auth).
- Login page uses Suspense boundary for useSearchParams() compatibility with Next.js 16.
- All dashboard pages use mock data with InsForge query builders ready for backend wiring.
- Analytics page uses inline bar chart (no external charting library needed yet).
- **InsForge uses `/api/auth/*` paths** (NOT `/auth/v1/*` as originally assumed). Confirmed via live instance testing and official docs at docs.insforge.dev.
- **InsForge auth requires `Authorization: Bearer <anon_key>`** for all requests including unauthenticated endpoints (registration, login). The `apikey` header alone is insufficient.
- **InsForge user shape** uses `profile.name` and `profile.avatar_url` (NOT `user_metadata.full_name`).
- **InsForge response fields** use `accessToken` (NOT `access_token`), and include `csrfToken` for web clients.
- **Email verification is enabled** on the live InsForge instance (`requireEmailVerification: true`). Registered users must verify email before login.
- **InsForge DB endpoints** use `/api/database/records/{table}` (NOT `/rest/v1/{table}`).
- **InsForge storage** uses presigned URL upload strategy via `/api/storage/buckets/{bucket}/upload-strategy`.
- **Phase 4A Report Generation** — Used reportlab (Python PDF library) for server-side PDF generation rather than client-side solutions (jspdf, @react-pdf/renderer). Reportlab provides full typographic control, proper table layouts, and professional print-quality output. The report endpoint is mounted into the existing analyze.py FastAPI app to avoid a third server process. Report generation triggers per-provider: the selected provider's data is sent to the backend, which fetches the full investigation from SQLite and generates the PDF.

---

# Known Issues

- Next.js 16 reports middleware deprecation warning (recommends "proxy" convention). Works correctly with current implementation.
- InsForge client is a custom REST API wrapper — may need adjustment if InsForge SDK becomes available on npm.
- All dashboard page data is mock data. Backend wiring to InsForge database is pending database initialization (Phase 1, Feature 03).
- **Email verification is required** on the InsForge instance. New users must verify email before they can login. No email verification bypass is available.
- InsForge anon key is exposed as `NEXT_PUBLIC_INSFORGE_ANON_KEY` — this is by design for browser-side auth, but should be rotated if the project goes to production.

---

# Notes

- The `@insforge/ssr` package is not publicly available on npm. A custom client was built using fetch API patterns matching InsForge's REST API.
- Auth persistence uses both localStorage (client-side) and cookies (middleware detection).
- The `insforge-auth` cookie stores the session JSON for server-side middleware verification.
- InsForge instance URL: `NEXT_PUBLIC_INSFORGE_URL` (configured in `.env.local`).
- Full InsForge API endpoint reference: see `context/backend-registry.md`.
