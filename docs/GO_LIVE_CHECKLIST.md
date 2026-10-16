# DataWise AI — Production Go-Live Checklist

---

## 1. Authentication & Identity Controls
- [x] `@gmail.com` domain gate strictly enforced (HTTP 403 on non-gmail).
- [x] Case-insensitive email normalization implemented (no duplicate account collision crashes).
- [x] Argon2id password hashing parameters configured with secure salts.
- [x] Google OAuth client credentials verified and origin allowlists updated.
- [x] GitHub OAuth client credentials verified and callback routes registered.
- [x] Frontend `/auth/callback` route extracts and persists JWT access tokens.
- [x] Password reset mechanism delivers generic responses to prevent user enumeration.

## 2. Multi-Tenant Isolation & Storage Security
- [x] Database queries explicitly filter on `user_id == current_user.id`.
- [x] Artifact download endpoints verify project ownership before streaming files.
- [x] Path traversal attacks blocked via strict directory resolution.
- [x] Cryptographic SHA-256 checksums verify file integrity on upload and download.
- [x] Cross-project data leakage eliminated across 4 distinct sample projects.

## 3. Data Science & ML Pipeline
- [x] Dataset upload handles valid CSV, XLSX, and malformed files safely.
- [x] Exploratory Data Analysis calculates statistics without LLM hallucination.
- [x] Leakage-free preprocessing using `ColumnTransformer` inside Pipeline.
- [x] Overfitting detection measures train-vs-test variance gaps.
- [x] Artifacts generated: Jupyter Notebook (`.ipynb`), HTML report, PDF report, model pickle (`.pkl`), ZIP bundle.

## 4. Operational & Infrastructure Readiness
- [x] Database schema auto-migration tested on boot.
- [x] Sliding-window rate limiter protects sensitive endpoints.
- [x] Frontend production bundle compiled with zero TypeScript errors (`npm run build`).
- [x] Audit log captures user logins, artifact downloads, and project modifications.
- [x] 45 automated backend tests pass with 100% success rate.
