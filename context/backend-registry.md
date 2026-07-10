# Backend Registry

Complete reference for all InsForge API endpoints used in the FraudShield platform. This document is the source of truth for every backend integration.

---

## Instance Configuration

| Key | Value |
|-----|-------|
| Instance URL | Configured via `NEXT_PUBLIC_INSFORGE_URL` in `.env.local` |
| Anon Key | Configured via `NEXT_PUBLIC_INSFORGE_ANON_KEY` in `.env.local` |
| Email Verification | **Required** (`requireEmailVerification: true`) |
| OAuth Providers | `github`, `google` |
| Password Min Length | 6 characters |
| Signup Disabled | `false` |

---

## Authentication

### Headers

All requests to InsForge require the `Authorization` header:

```
Authorization: Bearer <jwt-or-anon-key>
```

- **Unauthenticated requests** (registration, login): use the anon key as the Bearer token
- **Authenticated requests**: use the JWT access token from login/register response

The `apikey` header alone is **insufficient** — the Bearer token is required.

---

### Register User

```
POST /api/auth/users
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_type` | string | No | `web` (default), `mobile`, `desktop`, or `server` |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email address |
| `password` | string | Yes | Password (min 6 chars) |
| `name` | string | No | User display name |
| `redirectTo` | string | No | Redirect URL after email verification |

**Response (200):**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "emailVerified": false,
    "providers": ["email"],
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  },
  "accessToken": "jwt-token-or-null",
  "csrfToken": "csrf-token-or-null",
  "requireEmailVerification": true
}
```

- When `requireEmailVerification` is `true`, `accessToken` is `null` until email is verified.
- For web clients: `csrfToken` is returned, refresh token is stored as httpOnly cookie.
- For server clients: `refreshToken` is returned in the response body.

**Error Responses:**
- `400` — Invalid input / validation error
- `403` — Signups disabled
- `409` — User already exists

---

### Sign In

```
POST /api/auth/sessions
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_type` | string | No | `web` (default), `mobile`, `desktop`, or `server` |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email address |
| `password` | string | Yes | User password |

**Response (200) — Web Client:**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "emailVerified": true,
    "providers": ["email"],
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  },
  "accessToken": "jwt-token",
  "csrfToken": "csrf-token"
}
```

**Response (200) — Server Client:**

```json
{
  "user": { ... },
  "accessToken": "jwt-token",
  "refreshToken": "refresh-token"
}
```

**Error Responses:**
- `401` — Invalid credentials
- `403` — Email verification required

---

### Refresh Token

```
POST /api/auth/refresh
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_type` | string | No | `web` (default), `mobile`, `desktop`, or `server` |

**Headers (Web Client):**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-CSRF-Token` | string | Yes | CSRF token from login response |

**Request Body (Non-Web Client):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refreshToken` | string | Yes | Refresh token from login response |

**Response (200):**

```json
{
  "user": { ... },
  "accessToken": "new-jwt-token",
  "csrfToken": "new-csrf-token"
}
```

---

### Logout

```
POST /api/auth/logout
```

**Response (200):**

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### Get Current User

```
GET /api/auth/sessions/current
```

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <access-token>` |

**Response (200):**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "authenticated"
  }
}
```

Note: This endpoint does not refresh expired tokens. Use `/api/auth/refresh` explicitly.

---

### Update Profile

```
PATCH /api/auth/profiles/current
```

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <access-token>` |

**Request Body:**

```json
{
  "profile": {
    "name": "John Doe",
    "avatar_url": "https://example.com/avatar.jpg"
  }
}
```

**Response (200):**

```json
{
  "id": "user-id",
  "profile": {
    "name": "John Doe",
    "avatar_url": "https://example.com/avatar.jpg"
  }
}
```

---

### Get User Profile (Public)

```
GET /api/auth/profiles/{userId}
```

**Response (200):**

```json
{
  "id": "user-id",
  "profile": {
    "name": "John Doe",
    "avatar_url": "https://example.com/avatar.jpg"
  }
}
```

---

### Public Configuration

```
GET /api/auth/public-config
```

No authentication required.

**Response (200):**

```json
{
  "oAuthProviders": ["github", "google"],
  "customOAuthProviders": [],
  "requireEmailVerification": true,
  "passwordMinLength": 6,
  "requireNumber": false,
  "requireLowercase": false,
  "requireUppercase": false,
  "requireSpecialChar": false,
  "verifyEmailMethod": "code",
  "resetPasswordMethod": "code",
  "disableSignup": false
}
```

---

## Email Verification

### Send Verification Email

```
POST /api/auth/email/send-verification
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email address |
| `redirectTo` | string | No | Redirect URL after verification |

---

### Verify Email (Code)

```
POST /api/auth/email/verify
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_type` | string | No | `web` (default) or `server` |

**Request Body:**

```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response (200):**

```json
{
  "user": { ... },
  "accessToken": "jwt-token",
  "csrfToken": "csrf-token"
}
```

---

## Password Reset

### Send Reset Email

```
POST /api/auth/email/send-reset-password
```

**Request Body:**

```json
{
  "email": "user@example.com",
  "redirectTo": "http://localhost:3000/reset-password"
}
```

---

### Reset Password

```
POST /api/auth/email/reset-password
```

**Request Body:**

```json
{
  "newPassword": "newSecurePassword123",
  "otp": "reset-token-from-email"
}
```

---

## Database

### Query Records

```
GET /api/database/records/{tableName}
```

**Query Parameters (PostgREST-style):**

| Parameter | Example | Description |
|-----------|---------|-------------|
| `select` | `select=id,name,email` | Columns to select |
| `{column}` | `status=eq.active` | Filter by column value |
| `order` | `order=created_at.desc` | Sort order |
| `limit` | `limit=20` | Max rows to return |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <access-token>` |

---

### Create Records

```
POST /api/database/records/{tableName}
```

**Request Body:** Array of record objects (even for single insert)

```json
[
  {
    "patient_id": "P-001",
    "provider_id": "PRV-001",
    "claim_amount": 15000,
    "status": "uploaded"
  }
]
```

---

### Update Records

```
PATCH /api/database/records/{tableName}?field=eq.value
```

**Request Body:** Partial record with fields to update

```json
{
  "status": "investigating",
  "overall_risk_score": 0.85
}
```

---

### Delete Records

```
DELETE /api/database/records/{tableName}?field=eq.value
```

---

## Storage

### Upload File (New — Presigned URL)

**Step 1: Get upload strategy**

```
POST /api/storage/buckets/{bucketName}/upload-strategy
```

**Request Body:**

```json
{
  "path": "claims/claim-id/file.pdf",
  "contentType": "application/pdf"
}
```

**Response (200):**

```json
{
  "uploadUrl": "https://...",
  "method": "PUT",
  "headers": { "Content-Type": "application/pdf" }
}
```

**Step 2: Upload to presigned URL**

```
PUT {uploadUrl}
```

---

### Download File

```
GET /api/storage/buckets/{bucketName}/objects/{objectKey}
```

---

## User Object Shape

The InsForge user object returned from auth endpoints:

```typescript
type InsForgeUser = {
  id: string;           // UUID
  email: string;
  emailVerified: boolean;
  providers: string[];  // e.g., ["email"]
  createdAt: string;    // ISO timestamp
  updatedAt: string;    // ISO timestamp
  profile?: {
    name?: string;
    avatar_url?: string;
    [key: string]: unknown;  // Custom fields
  };
  metadata?: Record<string, unknown>;
};
```

**Important:** The user object uses `profile.name` (NOT `user_metadata.full_name`).

---

## Response Field Names

| Incorrect (old) | Correct (InsForge) |
|------------------|--------------------|
| `access_token` | `accessToken` |
| `refresh_token` | `refreshToken` |
| `user_metadata` | `profile` |
| `user_metadata.full_name` | `profile.name` |

---

## Client Type Behavior

| `client_type` | Refresh Token | CSRF Token | Use Case |
|---------------|---------------|------------|----------|
| `web` (default) | httpOnly cookie | Returned in response | Browser apps |
| `server` | Returned in response body | `null` | SSR, BFF, CLI |
| `mobile` | Returned in response body | `null` | Mobile apps |
| `desktop` | Returned in response body | `null` | Desktop apps |

**For FraudShield:** We use `web` (default) for browser client. The `server` client type is available for server-side operations but our custom client currently manages tokens manually via localStorage.

---

## Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "statusCode": 401,
  "nextActions": "Suggested action to resolve the error"
}
```

Common error codes:
- `INVALID_CREDENTIALS` — Wrong email or password
- `USER_EXISTS` — Email already registered
- `EMAIL_NOT_VERIFIED` — Email verification required before login
- `AUTH_SIGNUP_DISABLED` — Registration is disabled
- `AUTH_INVALID_CREDENTIALS` — Missing or invalid auth token
- `AUTH_UNAUTHORIZED` — Not authorized for this operation

---

## Source References

- InsForge Docs: https://docs.insforge.dev
- REST Auth API: https://docs.insforge.dev/sdks/rest/auth
- TypeScript SDK: https://docs.insforge.dev/sdks/typescript/auth
- OpenAPI spec: https://raw.githubusercontent.com/InsForge/InsForge/main/openapi/auth.yaml
