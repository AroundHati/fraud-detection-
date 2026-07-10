# Memory — InsForge Backend Debugging

Last updated: 2026-07-10

## What was built

- Rewrote `lib/insforge-client.ts` — corrected all InsForge API endpoint paths, response field names, auth header patterns, user object shape, DB query paths, and storage paths
- Rewrote `lib/insforge-server.ts` — same endpoint corrections as client
- Updated `hooks/use-auth.tsx` — new User type using `profile.name` instead of `user_metadata.full_name`
- Updated `hooks/use-user.tsx` — display name reads from `profile.name`
- Updated `middleware.ts` — cookie field `access_token` → `accessToken`
- Updated `app/(dashboard)/settings/page.tsx` — reads `profile.name` instead of `full_name`
- Created `context/backend-registry.md` — complete InsForge API endpoint reference
- Created `context/development-log.md` — session history
- Created `context/ml-pipeline.md` — ML pipeline status and architecture
- Updated `context/progress-tracker.md` — marked InsForge debugging complete

## Decisions made

- InsForge uses `/api/auth/*` paths (NOT `/auth/v1/*` as originally assumed)
- All InsForge requests require `Authorization: Bearer <anon_key>` for unauthenticated endpoints (registration, login) — the `apikey` header alone is insufficient
- InsForge user object uses `profile.name` and `profile.avatar_url` (NOT `user_metadata.full_name`)
- InsForge response fields use `accessToken` (NOT `access_token`) and include `csrfToken` for web clients
- InsForge DB endpoints use `/api/database/records/{table}` (NOT `/rest/v1/{table}`)
- InsForge storage uses presigned URL upload strategy via `/api/storage/buckets/{bucket}/upload-strategy`
- Email verification is enabled on the live instance — registered users must verify email before login

## Problems solved

- All `/auth/v1/*` endpoints returned 404 — fixed by switching to `/api/auth/*`
- Registration returned 401 "No token provided" — fixed by sending `Authorization: Bearer <anon_key>` for unauthenticated requests
- User type mismatch (`user_metadata` vs `profile`) — updated all consuming hooks and pages
- Cookie field name mismatch (`access_token` vs `accessToken`) — updated middleware

## Current state

- TypeScript: 0 errors ✓
- ESLint: 0 warnings ✓
- Build: All 12 routes generated ✓
- InsForge auth endpoints verified against live instance (registration works, login returns 403 for unverified users as expected)
- All dashboard pages still use mock data — backend wiring pending
- Email verification flow in UI not yet implemented

## Next session starts with

1. Database initialization (Phase 1, Feature 03) — create InsForge tables (users, claims, documents, investigations, agent_runs, agent_logs, reports)
2. Wire mock data to real InsForge database queries
3. Handle email verification flow in the UI (code entry page)
4. Test full signup → email verify → login → dashboard flow end-to-end

## Open questions

- Should we implement email verification UI (code entry page) before database initialization, or after?
- The InsForge instance has OAuth providers configured (github, google) — should we add OAuth login to the UI?
- The `middleware.ts` deprecation warning (recommends "proxy" convention) — should we migrate to the new pattern?
