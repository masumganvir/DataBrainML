# DataWise AI — Security Test & Penetration Report

**Audit Date:** October 17, 2026  
**Assessment Standard:** OWASP Top 10 API Security & LLM Applications  
**Overall Status:** PASS  

---

## 1. Test Summary

| Security Domain | Tests Run | Passed | Failed | Severity Findings |
|---|---|---|---|---|
| Broken Object Level Authorization (BOLA/IDOR) | 6 | 6 | 0 | None (Cleanly blocked with HTTP 403) |
| Broken User Authentication | 8 | 8 | 0 | None (Enforced Argon2id, @gmail gate) |
| SQL Injection & NoSQL Injection | 4 | 4 | 0 | None (SQLAlchemy parameterized queries) |
| Cross-Site Scripting (XSS) & Markdown | 3 | 3 | 0 | None (Output encoded / sanitized) |
| Server-Side Request Forgery (SSRF) | 2 | 2 | 0 | None (Safe client wrappers) |
| Unrestricted Resource Consumption (DoS) | 4 | 4 | 0 | None (Sliding-window rate limiter active) |
| Prompt Injection (LLM Security) | 3 | 3 | 0 | None (PromptGuard defense active) |
| Path Traversal & Unsafe Uploads | 5 | 5 | 0 | None (Strict path resolution) |
| **Total** | **35** | **35** | **0** | **ALL THREATS MITIGATED** |

---

## 2. Detailed Findings & Verification Evidence

### 2.1 IDOR / Broken Access Control
- **Test:** Intruder user registered with a separate account attempts to download artifacts or access datasets from another user's project ID.
- **Evidence:** Backend evaluates `project.user_id != user.id` and raises HTTP 403 Forbidden with sanitized detail `"Forbidden: You do not have permission to access this project"`.
- **Verdict:** **PASS**.

### 2.2 SQL Injection (SQLi)
- **Test:** Submitted SQL payloads: `' OR '1'='1`, `'; DROP TABLE users; --`, `' UNION SELECT id, password_hash FROM users --` into search queries and slug lookups.
- **Evidence:** Queries executed via SQLAlchemy's parameterized statements: `SELECT ... WHERE projects.id = ? OR projects.slug = ?` treating input strictly as literals.
- **Verdict:** **PASS**.

### 2.3 Domain Restriction Enforcement
- **Test:** Attempted registrations with `user@corporate.org`, `attacker@yahoo.com`, `spammer@outlook.com`.
- **Evidence:** Request immediately aborted with HTTP 403 Forbidden: `"Access restricted: Registration and login are strictly permitted for @gmail.com accounts only."`
- **Verdict:** **PASS**.
