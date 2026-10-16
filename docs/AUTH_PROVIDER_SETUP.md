# DataWise AI — External Authentication Provider Setup Guide

**Owner Action Required:** This document specifies the exact developer portal configuration required for Google Cloud and GitHub OAuth integrations.

---

## 1. Google OAuth 2.0 (Google Cloud Console)

### Step 1: Create or Select Project
1. Log in to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named **DataWise AI Production** (or select existing).

### Step 2: Configure OAuth Consent Screen
1. Navigate to **APIs & Services > OAuth consent screen**.
2. User Type: **External**.
3. App name: `DataWise AI`.
4. User support email: `your-admin@gmail.com`.
5. Developer contact information: `your-admin@gmail.com`.
6. Scopes requested:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`

### Step 3: Create OAuth Client Credentials
1. Navigate to **APIs & Services > Credentials > Create Credentials > OAuth client ID**.
2. Application type: **Web application**.
3. Name: `DataWise AI Web Client`.
4. **Authorized JavaScript origins**:
   - Development: `http://localhost:5173`
   - Production: `https://yourdomain.com`
5. **Authorized redirect URIs**:
   - Development: `http://localhost:8000/api/auth/google/callback`
   - Production: `https://api.yourdomain.com/api/auth/google/callback`
6. Click **Create** and copy the Client ID and Client Secret into your production environment vault.

---

## 2. GitHub OAuth Application

### Step 1: Register New OAuth Application
1. Log in to GitHub and navigate to **Settings > Developer Settings > OAuth Apps > New OAuth App**.
2. Application name: `DataWise AI`.
3. Homepage URL:
   - Development: `http://localhost:5173`
   - Production: `https://yourdomain.com`
4. **Authorization callback URL**:
   - Development: `http://localhost:8000/api/auth/github/callback`
   - Production: `https://api.yourdomain.com/api/auth/github/callback`
5. Click **Register application**.
6. Generate a client secret and store it in your environment vault.

---

## 3. Environment Variable Binding

Ensure the following keys are set in your backend `.env` file:
```bash
# Google OAuth
GOOGLE_CLIENT_ID="<your-google-client-id>.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="<your-google-client-secret>"
GOOGLE_REDIRECT_URI="http://localhost:8000/api/auth/google/callback"

# GitHub OAuth
GITHUB_CLIENT_ID="<your-github-client-id>"
GITHUB_CLIENT_SECRET="<your-github-client-secret>"
GITHUB_REDIRECT_URI="http://localhost:8000/api/auth/github/callback"

# Frontend Application Origin
FRONTEND_URL="http://localhost:5173"
```
