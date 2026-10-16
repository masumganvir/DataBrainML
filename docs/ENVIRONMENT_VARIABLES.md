# DataWise AI — Environment Variables Specification

**Security Notice:** Never commit actual secrets or production values to version control. This document lists variable names, expected types, and configuration purposes only.

---

## 1. Application & Core Settings

| Variable Name | Type | Default Value | Description |
|---|---|---|---|
| `ENVIRONMENT` | string | `development` | Deployment mode: `development`, `staging`, `production`. |
| `DEBUG` | boolean | `false` | Enable verbose logging and exception stack traces in API responses. |
| `API_V1_STR` | string | `/api` | Root prefix for REST API routing. |
| `PROJECT_NAME` | string | `DataWise AI` | Human-readable application name. |
| `FRONTEND_URL` | string | `http://localhost:5173` | Allowed origin for CORS headers and OAuth redirection. |

---

## 2. Security & Authentication

| Variable Name | Type | Default Value | Description |
|---|---|---|---|
| `SECRET_KEY` | string | *Generated* | Cryptographic secret for session signing and hashing. Minimum 32 chars. |
| `JWT_SECRET` | string | *Generated* | Secret key for signing HS256 JSON Web Tokens. Minimum 64 chars. |
| `JWT_ALGORITHM` | string | `HS256` | Token signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `60` | JWT expiration duration in minutes. |
| `ALLOWED_HOSTS` | string | `["*"]` | Comma-separated list of allowed HTTP Host headers. |

---

## 3. Database & Storage

| Variable Name | Type | Default Value | Description |
|---|---|---|---|
| `DATABASE_URL` | string | `sqlite+aiosqlite:///./datawise.db` | SQLAlchemy asynchronous database connection string. |
| `STORAGE_BACKEND` | string | `local` | Storage provider: `local`, `s3`, `supabase`. |
| `LOCAL_STORAGE_DIR` | string | `./artifacts` | Root directory for local file artifact storage. |
| `MAX_UPLOAD_SIZE_BYTES` | integer | `52428800` | Maximum file upload ceiling (50 MB default). |

---

## 4. Third-Party OAuth Providers

| Variable Name | Type | Description |
|---|---|---|
| `GOOGLE_CLIENT_ID` | string | OAuth Client ID from Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | string | OAuth Client Secret from Google Cloud Console. |
| `GOOGLE_REDIRECT_URI` | string | Authorized redirect URL for Google OAuth callback. |
| `GITHUB_CLIENT_ID` | string | Client ID from GitHub Developer Settings. |
| `GITHUB_CLIENT_SECRET` | string | Client Secret from GitHub Developer Settings. |
| `GITHUB_REDIRECT_URI` | string | Authorized callback URL for GitHub OAuth. |
