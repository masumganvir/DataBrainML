# DataWise AI — Incident Response & Security Playbook

**Version:** 1.0.0  
**Target:** Security Operations & Platform On-Call Engineers  

---

## 1. Incident Classification

| Severity Level | Definition | Examples | Response Target |
|---|---|---|---|
| **SEV-1 (Critical)** | Active data breach, cross-tenant isolation failure, authentication bypass. | User A accesses User B's dataset or models; unauthenticated remote code execution. | Immediate (< 15 mins) |
| **SEV-2 (High)** | Core feature outage, continuous OAuth failure, database connection pool exhaustion. | Login fails for all users; AutoML pipeline hanging indefinitely. | < 1 hour |
| **SEV-3 (Medium)** | Intermittent failure in reporting or non-critical artifact export. | PDF export fails while HTML/Notebook succeeds. | < 8 hours |
| **SEV-4 (Low)** | Minor UI cosmetic glitch or minor deprecation warning. | Typo in button tooltip. | Next sprint |

---

## 2. Emergency Security Response Playbooks

### 2.1 Compromised Secret Key or JWT Secret
1. Rotate `JWT_SECRET` in environment vault immediately.
2. Restart backend instances (`docker-compose restart backend`). This immediately invalidates all outstanding JWT tokens across all sessions.
3. Force all active users to re-authenticate.

### 2.2 Suspected Brute-Force / Abuse Attack
1. Verify sliding-window rate limiter telemetry in Redis / memory.
2. Ban attacking IP address at the reverse proxy / Cloudflare WAF:
   ```bash
   iptables -A INPUT -s <ATTACKER_IP> -j DROP
   ```
3. Audit `audit_logs` table for successful logins originating from the attacker IP.

### 2.3 Cross-Tenant Isolation Incident
1. Identify affected project and user IDs.
2. Place affected projects in `maintenance` status:
   ```sql
   UPDATE projects SET status = 'suspended' WHERE id = 'proj_affected';
   ```
3. Inspect server access logs and `audit_logs` for resource access events.
4. Notify affected parties in compliance with applicable breach notification policies.
